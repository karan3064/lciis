"""Layer 2 — ML-based multi-parameter pattern recognition.

Loads the gradient boosting model trained by ml/train_model.py and scores a
patient's most recent renal-panel + SpO2 values for a multi-parameter
deterioration pattern that single-test rules can miss.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import joblib
import numpy as np

from app.config import settings

REPO_ROOT = Path(__file__).resolve().parents[3]

# LOINC codes for the features the model was trained on.
FEATURE_TEST_CODES = {
    "creatinine": "2160-0",
    "bun": "3094-0",
    "potassium": "2823-3",
}
# Default (normal) value used when a patient has no reading for a feature yet.
FEATURE_DEFAULTS = {"creatinine": 1.0, "bun": 15.0, "potassium": 4.0, "spo2": 98.0}

RISK_THRESHOLDS = {"red": 0.75, "amber": 0.5}


@dataclass
class MLFinding:
    risk_score: float
    severity: str
    contributing_features: list[str]
    explanation: str


class RiskModel:
    def __init__(self, model_path: Optional[Path] = None):
        path = model_path or (REPO_ROOT / settings.ml_model_path)
        self._path = path
        self._bundle = None
        if path.exists():
            self._bundle = joblib.load(path)

    @property
    def is_loaded(self) -> bool:
        return self._bundle is not None

    def score(self, feature_values: dict[str, float]) -> Optional[MLFinding]:
        if not self.is_loaded:
            return None

        model = self._bundle["model"]
        features = self._bundle["features"]
        x = np.array(
            [[feature_values.get(f, FEATURE_DEFAULTS[f]) for f in features]]
        )
        risk_score = float(model.predict_proba(x)[0][1])

        if risk_score >= RISK_THRESHOLDS["red"]:
            severity = "red"
        elif risk_score >= RISK_THRESHOLDS["amber"]:
            severity = "amber"
        else:
            return None

        importances = getattr(model, "feature_importances_", None)
        contributing = []
        if importances is not None:
            ranked = sorted(zip(features, importances), key=lambda t: -t[1])
            contributing = [f for f, _ in ranked[:3]]

        explanation = (
            "ML model flags a multi-parameter deterioration pattern "
            f"(risk score {risk_score:.2f}). Contributing parameters: "
            f"{', '.join(contributing) if contributing else 'n/a'} — "
            "values: "
            + ", ".join(
                f"{f}={feature_values.get(f, FEATURE_DEFAULTS[f]):.1f}"
                for f in features
            )
        )

        return MLFinding(
            risk_score=risk_score,
            severity=severity,
            contributing_features=contributing,
            explanation=explanation,
        )


risk_model = RiskModel()
