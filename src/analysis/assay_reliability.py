"""Development-only assay reliability and effect-landscape audit."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr


ROOT = Path(__file__).resolve().parents[2]
NZIP = ROOT / "data/processed/nzip_snv_intervention_pairs.csv.gz"
MIKL = ROOT / "data/processed/mikl_motif_replacement_pairs.csv.gz"
MIKL_COUNTS = ROOT / "data/raw/mikl_gse173098/GSE173098_RNAloc_MPRA_counts.csv.gz"
SPLIT = ROOT / "data/manifests/nzip_parent_split.csv"
OUT_JSON = ROOT / "reports/assay_reliability.json"
OUT_CSV = ROOT / "reports/assay_reliability_by_parent.csv"


def finite_pair(x: pd.Series, y: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    a = pd.to_numeric(x, errors="coerce").to_numpy(float)
    b = pd.to_numeric(y, errors="coerce").to_numpy(float)
    keep = np.isfinite(a) & np.isfinite(b)
    return a[keep], b[keep]


def correlations(x: pd.Series, y: pd.Series) -> dict[str, float | int]:
    a, b = finite_pair(x, y)
    return {
        "n": int(len(a)),
        "pearson": float(pearsonr(a, b).statistic) if len(a) > 2 else float("nan"),
        "spearman": float(spearmanr(a, b).statistic) if len(a) > 2 else float("nan"),
        "mae": float(np.mean(np.abs(a - b))) if len(a) else float("nan"),
    }


def robust_sigma(values: pd.Series) -> float:
    x = pd.to_numeric(values, errors="coerce").dropna().to_numpy(float)
    center = np.median(x)
    return float(np.median(np.abs(x - center)) / 0.67448975)


def mikl_replicate_agreement() -> dict[str, object]:
    counts = pd.read_csv(MIKL_COUNTS)
    output: dict[str, object] = {}
    for cell in ["CAD", "Neuro-2a"]:
        estimates: list[np.ndarray] = []
        masks: list[np.ndarray] = []
        valid_counts: list[int] = []
        for rep in [1, 2, 3]:
            soma = counts[f"{cell} soma {rep}"].astype(float)
            neurite = counts[f"{cell} neurite {rep}"].astype(float)
            valid = (soma + neurite) >= 20
            soma_cpm = soma / soma.sum() * 1_000_000
            neurite_cpm = neurite / neurite.sum() * 1_000_000
            estimates.append(np.log2((neurite_cpm + 0.5) / (soma_cpm + 0.5)).to_numpy())
            masks.append(valid.to_numpy())
            valid_counts.append(int(valid.sum()))
        pairwise = []
        for i in range(3):
            for j in range(i + 1, 3):
                x, y = estimates[i], estimates[j]
                keep = np.isfinite(x) & np.isfinite(y) & masks[i] & masks[j]
                pairwise.append(
                    {
                        "replicates": f"{i + 1}-{j + 1}",
                        "n": int(keep.sum()),
                        "spearman": float(spearmanr(x[keep], y[keep]).statistic),
                        "pearson": float(pearsonr(x[keep], y[keep]).statistic),
                    }
                )
        output[cell] = {
            "valid_constructs_total_pair_count_ge_20_by_replicate": valid_counts,
            "pairwise_localization_agreement": pairwise,
            "median_spearman": float(np.median([row["spearman"] for row in pairwise])),
        }
    return output


def main() -> None:
    split = pd.read_csv(SPLIT)
    dev_ids = set(split.loc[split["role"] == "development", "parent_id"])
    lock_ids = set(split.loc[split["role"] == "locked_internal_test", "parent_id"])
    nzip_all = pd.read_csv(NZIP)
    nzip = nzip_all[nzip_all["parent_id"].isin(dev_ids)].copy()
    if set(nzip["parent_id"]) != dev_ids or set(nzip["parent_id"]) & lock_ids:
        raise AssertionError("Development reliability filter violated the frozen parent split")

    control_difference = (
        nzip["mutant_localization_log2_neurite_soma"]
        - nzip["mutant_shscramble_localization"]
    )
    sigma = robust_sigma(control_difference)
    threshold = max(0.25, 1.96 * sigma / np.sqrt(2.0))

    parent_rows: list[dict[str, object]] = []
    for parent_id, rows in nzip.groupby("parent_id", sort=True):
        effects = rows["delta_localization"].to_numpy(float)
        parent_rows.append(
            {
                "dataset": "nzip_development",
                "parent_id": parent_id,
                "candidate_snvs": int(len(rows)),
                "effect_mean": float(np.mean(effects)),
                "effect_sd": float(np.std(effects, ddof=1)),
                "effect_min": float(np.min(effects)),
                "effect_max": float(np.max(effects)),
                "effect_range": float(np.ptp(effects)),
                "fraction_effectively_null": float(np.mean(np.abs(effects) <= threshold)),
                "fraction_beneficial_increase": float(np.mean(effects > threshold)),
                "fraction_beneficial_decrease": float(np.mean(effects < -threshold)),
                "editability_positive": float(np.max(effects)),
                "editability_negative": float(-np.min(effects)),
            }
        )
    per_parent = pd.DataFrame(parent_rows)

    mikl = pd.read_csv(MIKL)
    mikl_cad = mikl["delta_cad_localization"]
    mikl_n2a = mikl["delta_neuro2a_localization"]
    mikl_effect = (mikl_cad + mikl_n2a) / 2.0
    mikl_parent_summary = mikl.assign(mean_delta=mikl_effect).groupby("parent_id")["mean_delta"].agg(
        ["count", "mean", "std", "min", "max"]
    )

    report: dict[str, object] = {
        "policy": {
            "nzip_parents_used": "12 development parents only",
            "locked_nzip_parents_inspected": False,
            "astrocyte_outcomes_inspected": False,
            "binary_success_threshold_log2": float(threshold),
            "threshold_rule": "max(0.25, 1.96 * robust_sigma(WT-shScramble) / sqrt(2))",
        },
        "nzip_development": {
            "parents": int(nzip["parent_id"].nunique()),
            "snvs": int(len(nzip)),
            "wt_vs_shscramble_agreement": correlations(
                nzip["mutant_localization_log2_neurite_soma"],
                nzip["mutant_shscramble_localization"],
            ),
            "wt_minus_shscramble_robust_sigma": float(sigma),
            "delta_mean": float(nzip["delta_localization"].mean()),
            "delta_sd": float(nzip["delta_localization"].std()),
            "delta_min": float(nzip["delta_localization"].min()),
            "delta_max": float(nzip["delta_localization"].max()),
            "fraction_effectively_null": float(
                (nzip["delta_localization"].abs() <= threshold).mean()
            ),
            "fraction_beneficial_increase": float(
                (nzip["delta_localization"] > threshold).mean()
            ),
            "fraction_beneficial_decrease": float(
                (nzip["delta_localization"] < -threshold).mean()
            ),
            "between_parent_variance_of_mean_delta": float(
                per_parent["effect_mean"].var(ddof=1)
            ),
            "median_within_parent_effect_sd": float(per_parent["effect_sd"].median()),
            "median_parent_effect_range": float(per_parent["effect_range"].median()),
            "interpretation": (
                "WT-versus-shScramble is a negative-control cross-condition agreement, not a "
                "true technical replicate; it supports a practical threshold but not a strict "
                "measurement-error ceiling."
            ),
        },
        "mikl": {
            "safe_pairs": int(len(mikl)),
            "parents": int(mikl["parent_id"].nunique()),
            "cad_vs_neuro2a_delta_agreement": correlations(mikl_cad, mikl_n2a),
            "mean_delta_sd": float(mikl_effect.std()),
            "mean_delta_min": float(mikl_effect.min()),
            "mean_delta_max": float(mikl_effect.max()),
            "parents_with_multiple_interventions": int((mikl_parent_summary["count"] > 1).sum()),
            "median_within_parent_delta_sd": float(mikl_parent_summary["std"].median()),
            "replicate_count_based_agreement": mikl_replicate_agreement(),
            "interpretation": (
                "CAD/Neuro-2a agreement measures cross-cell-context portability. Raw count "
                "replicate agreement is a closer reliability indicator but uses a simple "
                "library-size-normalized log-ratio rather than the authors' full model."
            ),
        },
    }
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    per_parent.to_csv(OUT_CSV, index=False)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
