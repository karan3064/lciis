from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert, LabResult, Patient, VitalReading
from app.schemas import (
    LastLabResult,
    PatientCreate,
    PatientOut,
    PatientSummary,
    VitalsSnapshot,
)

router = APIRouter(prefix="/api/patients", tags=["patients"])

SEVERITY_RANK = {"red": 3, "amber": 2, "yellow": 1}


def _vitals_snapshot(db: Session, patient_id: str) -> VitalsSnapshot:
    snapshot = VitalsSnapshot()
    field_by_metric = {"spo2": "spo2", "heart_rate": "heart_rate", "temperature": "temperature"}
    latest_at = None
    for metric, field in field_by_metric.items():
        row = (
            db.execute(
                select(VitalReading)
                .where(VitalReading.patient_id == patient_id, VitalReading.metric == metric)
                .order_by(VitalReading.recorded_at.desc())
                .limit(1)
            )
            .scalars()
            .first()
        )
        if row:
            setattr(snapshot, field, row.value)
            if latest_at is None or row.recorded_at > latest_at:
                latest_at = row.recorded_at
    snapshot.recorded_at = latest_at
    return snapshot


def _last_lab_result(db: Session, patient_id: str) -> LastLabResult | None:
    row = (
        db.execute(
            select(LabResult)
            .where(LabResult.patient_id == patient_id)
            .order_by(LabResult.collected_at.desc())
            .limit(1)
        )
        .scalars()
        .first()
    )
    if not row:
        return None
    return LastLabResult(
        test_name=row.test_name, value=row.value, unit=row.unit, collected_at=row.collected_at
    )


def _worst_active_alert(db: Session, patient_id: str) -> Alert | None:
    alerts = (
        db.execute(
            select(Alert).where(Alert.patient_id == patient_id, Alert.acknowledged == 0)
        )
        .scalars()
        .all()
    )
    if not alerts:
        return None
    return max(alerts, key=lambda a: (SEVERITY_RANK.get(a.severity, 0), a.triggered_at))


@router.post("", response_model=PatientOut)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    existing = db.get(Patient, payload.id)
    if existing:
        raise HTTPException(status_code=409, detail="Patient already exists")
    patient = Patient(**payload.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("", response_model=list[PatientOut])
def list_patients(db: Session = Depends(get_db)):
    return db.execute(select(Patient)).scalars().all()


@router.get("/summary", response_model=list[PatientSummary])
def list_patient_summaries(db: Session = Depends(get_db)):
    """Everything the dashboard's patient list needs in one call: worst
    active alert severity, a vitals snapshot, and the most recent lab
    result — so clinicians can triage without opening each chart."""
    patients = db.execute(select(Patient)).scalars().all()
    summaries = []
    for patient in patients:
        worst_alert = _worst_active_alert(db, patient.id)
        active_count = (
            db.execute(
                select(Alert).where(Alert.patient_id == patient.id, Alert.acknowledged == 0)
            )
            .scalars()
            .all()
        )
        summaries.append(
            PatientSummary(
                id=patient.id,
                name=patient.name,
                bed=patient.bed,
                ward=patient.ward,
                admitted_at=patient.admitted_at,
                worst_active_severity=worst_alert.severity if worst_alert else None,
                active_alert_count=len(active_count),
                worst_active_alert_message=worst_alert.message if worst_alert else None,
                vitals=_vitals_snapshot(db, patient.id),
                last_lab_result=_last_lab_result(db, patient.id),
            )
        )
    # Worst-first, then most recently updated, so unstable patients surface at the top.
    summaries.sort(
        key=lambda s: (
            -SEVERITY_RANK.get(s.worst_active_severity, 0),
            -(s.last_lab_result.collected_at.timestamp() if s.last_lab_result else 0),
        )
    )
    return summaries


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient
