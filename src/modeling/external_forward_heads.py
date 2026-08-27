"""Apply the frozen v2.4 external localization heads to absolute embeddings."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "data" / "frozen" / "v2_4_external_forward_heads.npz"
MANIFEST = ROOT / "data" / "frozen" / "v2_4_external_forward_heads.json"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def representation_matrix(
    representation: str,
    embedded: np.ndarray,
    handcrafted: np.ndarray,
) -> np.ndarray:
    if embedded.ndim != 2 or embedded.shape[1] != 1024:
        raise ValueError("Absolute SpliceBERT features must have 1024 columns")
    if handcrafted.ndim != 2 or handcrafted.shape[0] != embedded.shape[0]:
        raise ValueError("Handcrafted and SpliceBERT rows are misaligned")
    if representation == "mean":
        return embedded[:, 512:]
    if representation == "cls_mean":
        return embedded
    if representation == "cls_mean_handcrafted":
        return np.column_stack([embedded, handcrafted])
    raise ValueError(f"Unknown frozen external representation: {representation}")


def apply_head(
    features: np.ndarray,
    mean: np.ndarray,
    scale: np.ndarray,
    coefficient: np.ndarray,
    intercept: np.ndarray,
) -> np.ndarray:
    if features.shape[1] != len(mean) or mean.shape != scale.shape:
        raise ValueError("Frozen external scaler shape changed")
    if coefficient.ndim != 2 or coefficient.shape[1] != features.shape[1]:
        raise ValueError("Frozen external coefficient shape changed")
    transformed = (features - mean) / scale
    predictions = transformed @ coefficient.T + intercept
    if not np.isfinite(predictions).all():
        raise ValueError("Frozen external head produced non-finite predictions")
    return predictions


def score_frozen_external_heads(
    embedded: np.ndarray,
    handcrafted: np.ndarray,
) -> tuple[np.ndarray, list[str]]:
    manifest = json.loads(MANIFEST.read_text())
    if file_sha256(MODEL) != manifest["model_npz_sha256"]:
        raise ValueError("Frozen v2.4 external head artifact hash changed")
    artifact = np.load(MODEL)
    outputs: list[np.ndarray] = []
    labels: list[str] = []
    for dataset in ("mikl", "arora"):
        selected = manifest["selected"][dataset]
        features = representation_matrix(
            selected["representation"], embedded, handcrafted
        )
        predictions = apply_head(
            features,
            artifact[f"{dataset}_mean"],
            artifact[f"{dataset}_scale"],
            artifact[f"{dataset}_coef"],
            artifact[f"{dataset}_intercept"],
        )
        outputs.append(predictions)
        labels.extend(f"{dataset}:{outcome}" for outcome in selected["outcomes"])
    return np.column_stack(outputs).astype(np.float64), labels
