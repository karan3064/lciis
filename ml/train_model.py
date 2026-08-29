"""Trains the Layer 2 multi-parameter deterioration risk model.

Model: gradient boosting classifier over {creatinine, BUN, potassium, SpO2}
predicting probability of an early multi-parameter AKI-type deterioration
pattern (per LCIIS architecture doc section 3.3) — i.e. simultaneous mild
rises across renal markers plus falling oxygenation, even when each value
individually sits within its normal reference range.

There is no real hospital dataset available yet, so this script generates a
clinically-plausible synthetic dataset: "normal" patients sampled around
healthy baselines, and "deteriorating" patients sampled around the AKI
pattern described in the demo scenario (Creatinine ~1.9, BUN ~30, K+ ~5.2,
SpO2 ~93%). Swap `generate_dataset` for a loader against real historical
lab sequences once LCIIS is deployed against a hospital's data warehouse.

Usage: python ml/train_model.py
"""

from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

FEATURES = ["creatinine", "bun", "potassium", "spo2"]
MODEL_PATH = Path(__file__).parent / "risk_model.joblib"


def generate_dataset(n_per_class: int = 1500, seed: int = 42):
    rng = np.random.default_rng(seed)

    normal = rng.normal(
        loc=[1.0, 15.0, 4.0, 98.0],
        scale=[0.15, 3.0, 0.3, 1.0],
        size=(n_per_class, 4),
    )

    deteriorating = rng.normal(
        loc=[1.7, 27.0, 5.0, 93.5],
        scale=[0.35, 5.0, 0.5, 2.0],
        size=(n_per_class, 4),
    )

    X = np.vstack([normal, deteriorating])
    y = np.concatenate([np.zeros(n_per_class), np.ones(n_per_class)])
    return X, y


def main():
    X, y = generate_dataset()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = GradientBoostingClassifier(
        n_estimators=150, max_depth=3, learning_rate=0.1, random_state=42
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    print(classification_report(y_test, preds, target_names=["normal", "deteriorating"]))

    joblib.dump({"model": model, "features": FEATURES}, MODEL_PATH)
    print(f"Saved model to {MODEL_PATH}")


if __name__ == "__main__":
    main()
