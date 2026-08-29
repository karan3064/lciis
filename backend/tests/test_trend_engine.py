from datetime import datetime, timedelta

from app.models import LabResult
from app.services import trend_engine


def make_result(value: float, days_ago: int, test_code="2160-0", unit="mg/dL"):
    return LabResult(
        patient_id="P1",
        test_code=test_code,
        test_name="Creatinine",
        value=value,
        unit=unit,
        collected_at=datetime.utcnow() - timedelta(days=days_ago),
    )


def test_creatinine_rising_fires():
    history = [make_result(1.0, 4), make_result(1.2, 2), make_result(1.4, 0)]
    findings = trend_engine.evaluate_rules("2160-0", history)
    assert len(findings) == 1
    assert findings[0].rule_name == "creatinine_rising_3_consecutive"
    assert findings[0].severity == "amber"


def test_creatinine_stable_does_not_fire():
    history = [make_result(1.0, 4), make_result(1.02, 2), make_result(1.05, 0)]
    findings = trend_engine.evaluate_rules("2160-0", history)
    assert findings == []


def test_hemoglobin_drop_within_48h_fires():
    history = [
        make_result(13.0, 1, test_code="718-7", unit="g/dL"),
        make_result(10.5, 0, test_code="718-7", unit="g/dL"),
    ]
    findings = trend_engine.evaluate_rules("718-7", history)
    assert len(findings) == 1
    assert findings[0].rule_name == "hemoglobin_drop_48h"


def test_lactate_two_consecutive_high_fires_red():
    history = [
        make_result(2.5, 1, test_code="2524-7", unit="mmol/L"),
        make_result(3.1, 0, test_code="2524-7", unit="mmol/L"),
    ]
    findings = trend_engine.evaluate_rules("2524-7", history)
    assert len(findings) == 1
    assert findings[0].severity == "red"


def test_potassium_critical_low_or_high():
    history = [make_result(6.2, 0, test_code="2823-3", unit="mEq/L")]
    findings = trend_engine.evaluate_rules("2823-3", history)
    assert len(findings) == 1
    assert findings[0].rule_name == "potassium_critical"
