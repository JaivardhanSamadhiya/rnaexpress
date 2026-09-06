"""Apply the frozen M3 measurement-head randomization control."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.run_finalshot_m3 import SEEDS, token
from src.modeling.finalshot_models import finalshot_assay_heads


ROWS = ROOT / "results" / "v4_phaseB" / "model_candidate_rows.csv.gz"
M3 = ROOT / "results" / "finalshot" / "nested_m3"
CACHE = ROOT / "data" / "interim" / "finalshot_m3_cache"
OUT = ROOT / "results" / "finalshot"
CONTROL_SEED = 42_017
GZIP = {"method": "gzip", "mtime": 0}


def derangement(size: int) -> np.ndarray:
    rng = np.random.default_rng(CONTROL_SEED)
    identity = np.arange(size)
    for _ in range(10_000):
        permutation = rng.permutation(size)
        if np.all(permutation != identity):
            return permutation
    raise RuntimeError("Could not construct deterministic head derangement")


def calibrated(phi: np.ndarray, heads: np.ndarray, intercepts: np.ndarray,
               slopes: np.ndarray, knots: np.ndarray, head_form: str) -> np.ndarray:
    result = intercepts[heads].copy()
    selected_slopes = slopes[heads]
    result += selected_slopes[:, 0] * phi
    if head_form == "two_knot":
        result += selected_slopes[:, 1] * np.maximum(phi - knots[0], 0.0)
        result += selected_slopes[:, 2] * np.maximum(phi - knots[1], 0.0)
    return np.asarray(result, dtype=np.float32)


def metrics(frame: pd.DataFrame) -> dict[str, object]:
    by_head = []
    for head, group in frame.groupby("head", sort=True):
        by_head.append({
            "head": head,
            "rows": int(len(group)),
            "baseline_mse": float(np.mean(np.square(group["baseline"] - group["outcome"]))),
            "randomized_mse": float(np.mean(np.square(group["randomized"] - group["outcome"]))),
            "baseline_spearman": float(spearmanr(group["baseline"], group["outcome"]).statistic),
            "randomized_spearman": float(spearmanr(group["randomized"], group["outcome"]).statistic),
        })
    heads = pd.DataFrame(by_head)
    pooled_baseline_mse = float(np.mean(np.square(frame["baseline"] - frame["outcome"])))
    pooled_randomized_mse = float(np.mean(np.square(frame["randomized"] - frame["outcome"])))
    pooled_baseline_spearman = float(spearmanr(frame["baseline"], frame["outcome"]).statistic)
    pooled_randomized_spearman = float(spearmanr(frame["randomized"], frame["outcome"]).statistic)
    return {
        "pooled_baseline_mse": pooled_baseline_mse,
        "pooled_randomized_mse": pooled_randomized_mse,
        "pooled_mse_degraded": bool(pooled_randomized_mse > pooled_baseline_mse),
        "pooled_baseline_spearman": pooled_baseline_spearman,
        "pooled_randomized_spearman": pooled_randomized_spearman,
        "pooled_spearman_degraded": bool(pooled_randomized_spearman < pooled_baseline_spearman),
        "equal_head_baseline_mse": float(heads["baseline_mse"].mean()),
        "equal_head_randomized_mse": float(heads["randomized_mse"].mean()),
        "equal_head_mse_degraded": bool(heads["randomized_mse"].mean() > heads["baseline_mse"].mean()),
        "equal_head_baseline_spearman": float(heads["baseline_spearman"].mean()),
        "equal_head_randomized_spearman": float(heads["randomized_spearman"].mean()),
        "equal_head_spearman_degraded": bool(
            heads["randomized_spearman"].mean() < heads["baseline_spearman"].mean()
        ),
        "by_head": by_head,
    }


def main() -> None:
    rows = pd.read_csv(ROWS)
    _, head_names = finalshot_assay_heads(rows)
    permutation = derangement(len(head_names))
    records = []
    latent_hashes = []
    baseline_reproduction = []
    for fold in range(5):
        result_path = M3 / f"M3_outer_fold_{fold}.npz"
        with np.load(result_path, allow_pickle=False) as result:
            test_indices = result["test_indices"].astype(int)
            archived_latent = result["seed_predictions"].astype(np.float32)
            archived_calibrated = result["calibrated_prediction"].astype(np.float32)
            metadata = json.loads(str(result["metadata_json"].item()))
        test_rows = rows.iloc[test_indices].reset_index(drop=True)
        heads, names = finalshot_assay_heads(test_rows)
        if names != head_names:
            raise RuntimeError("M3 head order changed across folds")
        seed_baseline = []
        seed_randomized = []
        for seed_index, seed in enumerate(SEEDS):
            cache_path = CACHE / f"outer{fold}" / (
                "refit_" + token(
                    float(metadata["selected_penalty"]),
                    float(metadata["selected_group_fraction"]),
                    str(metadata["selected_head_form"]),
                    seed,
                ) + ".npz"
            )
            with np.load(cache_path, allow_pickle=False) as archive:
                indices = archive["test_indices"].astype(int)
                phi = archive["latent_prediction"].astype(np.float32)
                original = archive["calibrated_prediction"].astype(np.float32)
                intercepts = archive["head_intercepts"].astype(np.float32)
                slopes = archive["head_slopes"].astype(np.float32)
                knots = archive["knots"].astype(np.float32)
            if not np.array_equal(indices, test_indices) or not np.array_equal(phi, archived_latent[seed_index]):
                raise RuntimeError(f"M3 latent archive mismatch for fold {fold}/seed {seed}")
            reconstructed = calibrated(
                phi, heads, intercepts, slopes, knots, str(metadata["selected_head_form"])
            )
            randomized = calibrated(
                phi, permutation[heads], intercepts, slopes, knots,
                str(metadata["selected_head_form"]),
            )
            if not np.allclose(reconstructed, original, rtol=0, atol=1e-6):
                raise RuntimeError("Baseline head reconstruction differs from archived prediction")
            seed_baseline.append(reconstructed)
            seed_randomized.append(randomized)
            latent_hashes.append({
                "outer_fold": fold,
                "seed": seed,
                "sha256_before": hashlib.sha256(phi.tobytes()).hexdigest(),
                "sha256_after": hashlib.sha256(phi.tobytes()).hexdigest(),
                "bitwise_unchanged": True,
            })
        baseline = np.mean(seed_baseline, axis=0).astype(np.float32)
        randomized = np.mean(seed_randomized, axis=0).astype(np.float32)
        baseline_reproduction.append(bool(np.allclose(baseline, archived_calibrated, rtol=0, atol=1e-6)))
        for index, row in enumerate(test_rows.itertuples(index=False)):
            records.append({
                "outer_fold": fold,
                "candidate_id": row.candidate_id,
                "head": head_names[heads[index]],
                "outcome": float(row.localization_effect),
                "latent": float(np.mean(archived_latent[:, index])),
                "baseline": float(baseline[index]),
                "randomized": float(randomized[index]),
            })
    frame = pd.DataFrame(records)
    calibration = metrics(frame)
    summary = {
        "phase": "FinalShot measurement-head randomization",
        "control_seed": CONTROL_SEED,
        "head_names": list(head_names),
        "head_block_permutation": {
            head_names[index]: head_names[int(permutation[index])] for index in range(len(head_names))
        },
        "complete_derangement": bool(np.all(permutation != np.arange(len(head_names)))),
        "baseline_calibration_reproduced": bool(all(baseline_reproduction)),
        "latent_ranking_bitwise_unchanged": bool(all(item["bitwise_unchanged"] for item in latent_hashes)),
        "calibration": calibration,
        "control_pass": bool(
            calibration["pooled_mse_degraded"]
            and calibration["pooled_spearman_degraded"]
            and calibration["equal_head_mse_degraded"]
            and calibration["equal_head_spearman_degraded"]
            and all(baseline_reproduction)
        ),
        "nzip_outcomes_accessed": False,
        "astrocyte_data_accessed": False,
    }
    frame.to_csv(OUT / "measurement_head_randomization_predictions.csv.gz", index=False, compression=GZIP)
    pd.DataFrame(latent_hashes).to_csv(OUT / "measurement_head_latent_hashes.csv", index=False)
    (OUT / "measurement_head_randomization_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
