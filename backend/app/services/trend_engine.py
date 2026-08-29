"""Layer 1 — deterministic, zero-latency threshold rules.

Each rule inspects a patient's recent history for one test code (already
sorted ascending by collection time, most recent last) and returns a
RuleFinding if it fires, else None. Rules are clinically-validated
thresholds per the LCIIS architecture doc (section 3.3).
"""

from dataclasses import dataclass
from datetime import timedelta
from typing import Callable, Optional

from app.models import LabResult

Severity = str  # "yellow" | "amber" | "red"


@dataclass
class RuleFinding:
    rule_name: str
    severity: Severity
    message: str


RuleFn = Callable[[list[LabResult]], Optional[RuleFinding]]


def _pct_change(old: float, new: float) -> float:
    if old == 0:
        return float("inf") if new != 0 else 0.0
    return (new - old) / abs(old) * 100.0


def rule_creatinine_rising(history: list[LabResult]) -> Optional[RuleFinding]:
    """Creatinine rising >20% across 3 consecutive tests."""
    if len(history) < 3:
        return None
    a, b, c = history[-3], history[-2], history[-1]
    if a.value <= b.value <= c.value:
        rise = _pct_change(a.value, c.value)
        if rise > 20:
            return RuleFinding(
                rule_name="creatinine_rising_3_consecutive",
                severity="amber",
                message=(
                    f"Creatinine rising {rise:.0f}% across 3 consecutive tests "
                    f"({a.value} -> {b.value} -> {c.value} {c.unit or ''})".strip()
                ),
            )
    return None


def rule_creatinine_rapid_rise_48h(history: list[LabResult]) -> Optional[RuleFinding]:
    """Creatinine rising >30% within 48 hours (fast early signal — fires even
    on just two data points, ahead of the 3-consecutive-test rule)."""
    if len(history) < 2:
        return None
    latest = history[-1]
    window_start = latest.collected_at - timedelta(hours=48)
    prior = [r for r in history[:-1] if r.collected_at >= window_start]
    if not prior:
        return None
    baseline = min(prior, key=lambda r: r.collected_at)
    rise = _pct_change(baseline.value, latest.value)
    if rise > 30:
        return RuleFinding(
            rule_name="creatinine_rapid_rise_48h",
            severity="amber",
            message=(
                f"Creatinine rising {rise:.0f}% within 48 hours "
                f"({baseline.value} -> {latest.value} {latest.unit or ''})".strip()
            ),
        )
    return None


def rule_hemoglobin_drop(history: list[LabResult]) -> Optional[RuleFinding]:
    """Hemoglobin dropping >2 g/dL within 48 hours."""
    if len(history) < 2:
        return None
    latest = history[-1]
    window_start = latest.collected_at - timedelta(hours=48)
    candidates = [r for r in history if r.collected_at >= window_start]
    if len(candidates) < 2:
        return None
    highest = max(candidates, key=lambda r: r.value)
    drop = highest.value - latest.value
    if highest.collected_at < latest.collected_at and drop > 2:
        return RuleFinding(
            rule_name="hemoglobin_drop_48h",
            severity="amber",
            message=(
                f"Hemoglobin dropped {drop:.1f} g/dL within 48 hours "
                f"({highest.value} -> {latest.value})"
            ),
        )
    return None


def rule_lactate_high(history: list[LabResult]) -> Optional[RuleFinding]:
    """Lactate > 2 mmol/L in two consecutive samples."""
    if len(history) < 2:
        return None
    a, b = history[-2], history[-1]
    if a.value > 2 and b.value > 2:
        return RuleFinding(
            rule_name="lactate_high_consecutive",
            severity="red",
            message=(
                f"Lactate > 2 mmol/L in two consecutive samples "
                f"({a.value} -> {b.value} mmol/L) — possible early septic shock"
            ),
        )
    return None


def rule_potassium_critical(history: list[LabResult]) -> Optional[RuleFinding]:
    """Potassium out of safe range — single-value critical rule."""
    if not history:
        return None
    latest = history[-1]
    if latest.value >= 6.0 or latest.value <= 2.5:
        return RuleFinding(
            rule_name="potassium_critical",
            severity="red",
            message=f"Potassium critical: {latest.value} mEq/L",
        )
    return None


# LOINC test codes used by the demo scenario / common panels. Extend as
# additional panels are onboarded.
RULES_BY_TEST_CODE: dict[str, list[RuleFn]] = {
    "2160-0": [rule_creatinine_rising, rule_creatinine_rapid_rise_48h],  # Creatinine
    "718-7": [rule_hemoglobin_drop],  # Hemoglobin
    "2524-7": [rule_lactate_high],  # Lactate
    "2823-3": [rule_potassium_critical],  # Potassium
}


def evaluate_rules(test_code: str, history: list[LabResult]) -> list[RuleFinding]:
    """History must be sorted ascending by collected_at."""
    findings = []
    for rule in RULES_BY_TEST_CODE.get(test_code, []):
        result = rule(history)
        if result:
            findings.append(result)
    return findings
