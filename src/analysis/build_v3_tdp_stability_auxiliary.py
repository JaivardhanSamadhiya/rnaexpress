"""Build the frozen TDP 3UTRBERT auxiliary-stability prediction for N-zip."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from src.modeling.utrbert_features import build_paired_utrbert_delta_features_resumable


ROOT = Path(__file__).resolve().parents[2]
TDP = ROOT / "data/processed/tdp43_v3_diagnostic_pairs.csv.gz"
NZIP = ROOT / "results/v2/nzip_development_predictions.csv.gz"
TDP_FEATURES = ROOT / "data/interim/v3_tdp_3utrbert_features.npy"
PARTIAL = ROOT / "data/interim/v3_tdp_3utrbert_contextual.partial.npy"
PROGRESS = ROOT / "data/interim/v3_tdp_3utrbert_contextual.progress.json"
NZIP_FEATURES = ROOT / "data/interim/v3_3utrbert_delta_features.npy"
NZIP_PREDICTION = ROOT / "data/interim/v3_nzip_tdp_stability_prediction.npy"
OUT = ROOT / "results/v3_phase3/tdp_stability_auxiliary_manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    tdp = pd.read_csv(TDP)
    nzip = pd.read_csv(NZIP)
    if len(tdp) != 4_566 or len(nzip) != 4_395:
        raise ValueError("Frozen auxiliary/primary row count changed")
    if TDP_FEATURES.exists():
        tdp_features = np.load(TDP_FEATURES, allow_pickle=False)
        print(f"loaded cached TDP 3UTRBERT features {tdp_features.shape}", flush=True)
    else:
        tdp_features = build_paired_utrbert_delta_features_resumable(
            tdp, PARTIAL, PROGRESS, batch_size=128
        )
        np.save(TDP_FEATURES, tdp_features, allow_pickle=False)
    nzip_features = np.load(NZIP_FEATURES, allow_pickle=False)
    if tdp_features.shape != (4_566, 3_662) or nzip_features.shape != (4_395, 3_662):
        raise ValueError("Selected contextual feature shape changed")
    target = tdp["stability_intervention_delta"].to_numpy(float)
    finite = np.isfinite(target)
    if int(finite.sum()) != 3_117:
        raise ValueError("Finite TDP stability linkage count changed")
    scaler = StandardScaler().fit(tdp_features[finite])
    model = Ridge(
        alpha=float(tdp_features.shape[1]),
        solver="lsqr",
        tol=1e-6,
        max_iter=10_000,
    )
    model.fit(scaler.transform(tdp_features[finite]), target[finite])
    prediction = model.predict(scaler.transform(nzip_features)).astype(np.float32)
    if not np.isfinite(prediction).all():
        raise ValueError("TDP auxiliary prediction is non-finite")
    np.save(NZIP_PREDICTION, prediction, allow_pickle=False)
    manifest = {
        "phase": "v3_phase3_tdp_stability_auxiliary",
        "analysis_class": "DEVELOPMENT_AUXILIARY_NOT_VALIDATION",
        "strategy": "C_TDP_supervision_never_enters_final_SNV_output_head",
        "representation": "yangheng/3utrbert revision 220d80829deb077d1d640463a4267a96e9e70b1d",
        "tdp_rows": len(tdp),
        "finite_tdp_stability_rows": int(finite.sum()),
        "nzip_prediction_rows": len(prediction),
        "feature_count": tdp_features.shape[1],
        "ridge_alpha": float(tdp_features.shape[1]),
        "tdp_source_sha256": sha256(TDP),
        "tdp_feature_cache_sha256": sha256(TDP_FEATURES),
        "nzip_feature_cache_sha256": sha256(NZIP_FEATURES),
        "nzip_prediction_cache_sha256": sha256(NZIP_PREDICTION),
        "no_measured_stability_required_at_inference": True,
        "protected_data_access": {
            "astrocyte_outcomes_opened": False,
            "moffatt_archive_opened": False,
        },
    }
    OUT.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
