"""Apply the frozen v2.5 Mikl published-model XGBoost heads."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from xgboost import XGBClassifier

from .external_forward_heads import file_sha256
from .fourmer_features import FOURMER_ORDER, fourmer_counts


ROOT = Path(__file__).resolve().parents[2]
NEURITE_MODEL = ROOT / "data" / "frozen" / "v2_5_mikl_neurite_xgboost.json"
SOMA_MODEL = ROOT / "data" / "frozen" / "v2_5_mikl_soma_xgboost.json"
MANIFEST = ROOT / "data" / "frozen" / "v2_5_mikl_xgboost_heads.json"


def load_frozen_heads() -> tuple[XGBClassifier, XGBClassifier]:
    manifest = json.loads(MANIFEST.read_text())
    if manifest["fourmer_order"] != list(FOURMER_ORDER):
        raise ValueError("Frozen Mikl 4-mer order changed")
    if file_sha256(NEURITE_MODEL) != manifest["neurite_model_sha256"]:
        raise ValueError("Frozen Mikl neurite model hash changed")
    if file_sha256(SOMA_MODEL) != manifest["soma_model_sha256"]:
        raise ValueError("Frozen Mikl soma model hash changed")
    neurite = XGBClassifier()
    soma = XGBClassifier()
    neurite.load_model(NEURITE_MODEL)
    soma.load_model(SOMA_MODEL)
    return neurite, soma


def predict_frozen_heads(sequences: list[str]) -> np.ndarray:
    features = fourmer_counts(sequences, equivalent_150nt=True)
    neurite, soma = load_frozen_heads()
    predictions = np.column_stack(
        [
            neurite.predict_proba(features)[:, 1],
            soma.predict_proba(features)[:, 1],
        ]
    ).astype(np.float64)
    if predictions.shape != (len(sequences), 2) or not np.isfinite(predictions).all():
        raise ValueError("Frozen Mikl heads produced invalid predictions")
    return predictions
