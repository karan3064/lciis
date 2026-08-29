from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert, LabResult, Patient, VitalReading
from app.schemas import IngestResult, LabResultIn, TrendPoint, TrendSeries
from app.services import trend_engine
from app.services.ml_engine import FEATURE_TEST_CODES, risk_model
from app.services.mqtt_client import publish_alert

router = APIRouter(prefix="/api", tags=["lab-results"])

# How long to suppress a repeat alert of the same kind for the same patient,
# so a batch of near-simultaneous test results (a single collection episode)
# doesn't page the bedside device multiple times for the same event.
ALERT_DEDUP_WINDOW = timedelta(minutes=30)


def _is_duplicate_alert(db: Session, patient_id: str, source: str, rule_name: str | None) -> bool:
    cutoff = datetime.utcnow() - ALERT_DEDUP_WINDOW
    stmt = select(Alert).where(
        Alert.patient_id == patient_id,
        Alert.source == source,
        Alert.triggered_at >= cutoff,
    )
    if rule_name is not None:
        stmt = stmt.where(Alert.rule_name == rule_name)
    return db.execute(stmt.limit(1)).scalars().first() is not None


def _upsert_patient(db: Session, payload: LabResultIn) -> Patient:
    patient = db.get(Patient, payload.patient_id)
    if patient is None:
        patient = Patient(
            id=payload.patient_id,
            name=payload.patient_name or payload.patient_id,
            bed=payload.bed,
            ward=payload.ward,
        )
        db.add(patient)
    else:
        if payload.bed:
            patient.bed = payload.bed
        if payload.ward:
            patient.ward = payload.ward
    db.flush()
    return patient


def _latest_value(db: Session, patient_id: str, test_code: str) -> float | None:
    row = (
        db.execute(
            select(LabResult)
            .where(LabResult.patient_id == patient_id, LabResult.test_code == test_code)
            .order_by(LabResult.collected_at.desc())
            .limit(1)
        )
        .scalars()
        .first()
    )
    return row.value if row else None


def _latest_spo2(db: Session, patient_id: str) -> float | None:
    row = (
        db.execute(
            select(VitalReading)
            .where(VitalReading.patient_id == patient_id, VitalReading.metric == "spo2")
            .order_by(VitalReading.recorded_at.desc())
            .limit(1)
        )
        .scalars()
        .first()
    )
    return row.value if row else None


@router.post("/lab-result", response_model=IngestResult)
def ingest_lab_result(payload: LabResultIn, db: Session = Depends(get_db)):
    """Receives the parsed JSON payload Mirth Connect forwards after parsing
    an HL7 ORU^R01 message. Stores the result, runs both trend-engine
    layers, persists any alerts, and publishes them to the bedside MQTT
    topic for the patient's bed."""

    patient = _upsert_patient(db, payload)

    lab_result = LabResult(
        patient_id=patient.id,
        test_code=payload.test_code,
        test_name=payload.test_name,
        value=payload.value,
        unit=payload.unit,
        ref_low=payload.ref_low,
        ref_high=payload.ref_high,
        ordering_physician=payload.ordering_physician,
        collected_at=payload.collected_at,
    )
    db.add(lab_result)
    db.flush()

    triggered_alerts: list[Alert] = []

    # --- Layer 1: rule-based trend detection ---
    history = (
        db.execute(
            select(LabResult)
            .where(LabResult.patient_id == patient.id, LabResult.test_code == payload.test_code)
            .order_by(LabResult.collected_at.asc())
        )
        .scalars()
        .all()
    )
    for finding in trend_engine.evaluate_rules(payload.test_code, history):
        if _is_duplicate_alert(db, patient.id, "rule_engine", finding.rule_name):
            continue
        alert = Alert(
            patient_id=patient.id,
            severity=finding.severity,
            source="rule_engine",
            rule_name=finding.rule_name,
            test_codes=payload.test_code,
            message=finding.message,
        )
        db.add(alert)
        triggered_alerts.append(alert)

    # --- Layer 2: ML multi-parameter pattern recognition ---
    if payload.test_code in FEATURE_TEST_CODES.values():
        feature_values = {
            name: _latest_value(db, patient.id, code)
            for name, code in FEATURE_TEST_CODES.items()
        }
        feature_values = {k: v for k, v in feature_values.items() if v is not None}
        spo2 = _latest_spo2(db, patient.id)
        if spo2 is not None:
            feature_values["spo2"] = spo2

        ml_finding = risk_model.score(feature_values)
        if ml_finding and not _is_duplicate_alert(db, patient.id, "ml_engine", None):
            alert = Alert(
                patient_id=patient.id,
                severity=ml_finding.severity,
                source="ml_engine",
                risk_score=ml_finding.risk_score,
                test_codes=",".join(
                    FEATURE_TEST_CODES.get(f, f) for f in ml_finding.contributing_features
                ),
                message=(
                    f"Multi-parameter deterioration pattern detected "
                    f"(risk score {ml_finding.risk_score:.2f})"
                ),
                explanation=ml_finding.explanation,
            )
            db.add(alert)
            triggered_alerts.append(alert)

    db.commit()
    for alert in triggered_alerts:
        db.refresh(alert)
        publish_alert(
            bed=patient.bed,
            patient_id=patient.id,
            patient_name=patient.name,
            test_name=payload.test_name,
            severity=alert.severity,
            message=alert.message,
            suggested_action="Review patient chart and reassess" if alert.severity != "red"
            else "Urgent clinical review required",
        )

    return IngestResult(lab_result_id=lab_result.id, alerts_triggered=triggered_alerts)


@router.get("/patients/{patient_id}/trend", response_model=list[TrendSeries])
def get_patient_trend(patient_id: str, db: Session = Depends(get_db)):
    """All lab result series for a patient, grouped by test code, for the
    dashboard's interactive trend graphs."""
    rows = (
        db.execute(
            select(LabResult)
            .where(LabResult.patient_id == patient_id)
            .order_by(LabResult.test_code, LabResult.collected_at.asc())
        )
        .scalars()
        .all()
    )

    grouped: dict[str, list[LabResult]] = defaultdict(list)
    for row in rows:
        grouped[row.test_code].append(row)

    return [
        TrendSeries(
            test_code=test_code,
            test_name=series[0].test_name,
            unit=series[0].unit,
            points=[TrendPoint(collected_at=r.collected_at, value=r.value) for r in series],
        )
        for test_code, series in grouped.items()
    ]
