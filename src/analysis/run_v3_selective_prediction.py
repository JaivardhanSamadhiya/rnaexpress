"""Develop the frozen outcome-free confidence score and selective curves."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr
from sklearn.metrics.pairwise import cosine_distances

from src.modeling.features import normalize_sequence
from src.modeling.utrbert_features import sha256_bytes
from src.modeling.v3_nested import NestedResult, directional_metrics
from src.modeling.v3_statistics import BOOTSTRAP_RESAMPLES, BOOTSTRAP_SEED, MEANINGFUL_EFFECT


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "results/v2_6/nzip_nested_stack_predictions.csv.gz"
ABSOLUTE_FEATURES = ROOT / "data/interim/v3_3utrbert_absolute_features.npy"
ABSOLUTE_SEQUENCES = ROOT / "data/interim/v3_3utrbert_absolute_sequences.npy"
ABLATION = ROOT / "data/interim/v3_mechanistic_ablations"
EXTREME = ROOT / "data/interim/v3_best_ablation_extreme.npz"
CONTROL_CACHE = ROOT / "data/interim/v3_final_controls"
OUT = ROOT / "results/v3_phase3"
SEEDS = (20260828, 20260829, 20260830)
COVERAGES = (1.0, 0.8, 0.6, 0.4)


def _load_nested(component: str, seed: int = SEEDS[0]) -> NestedResult:
    if component == "rank":
        prefix = ABLATION / "remove_motif_interactions_rank"
    elif seed == SEEDS[0]:
        prefix = ABLATION / "remove_motif_interactions_magnitude"
    else:
        prefix = CONTROL_CACHE / f"seed_{seed}_magnitude"
    arrays = np.load(prefix.with_suffix(".npz"), allow_pickle=False)
    return NestedResult(
        arrays["prediction"],
        pd.read_csv(str(prefix) + "_tuning.csv"),
        arrays["inner_prediction"],
    )


def _parent_embeddings(frame: pd.DataFrame) -> tuple[list[str], np.ndarray]:
    features = np.load(ABSOLUTE_FEATURES, allow_pickle=False)
    sequences = np.load(ABSOLUTE_SEQUENCES, allow_pickle=False)
    lookup = {
        sha256_bytes(normalize_sequence(sequence)): features[index]
        for index, sequence in enumerate(sequences)
    }
    parent_ids = sorted(frame["parent_id"].unique())
    values = []
    for parent_id in parent_ids:
        sequence = frame.loc[frame["parent_id"] == parent_id, "parent_sequence"].iloc[0]
        values.append(lookup[sha256_bytes(normalize_sequence(sequence))])
    return parent_ids, np.asarray(values, dtype=np.float32)


def _percentile(values: np.ndarray, selected: int) -> float:
    if len(values) <= 1:
        return 1.0
    return float((rankdata(values, method="average")[selected] - 1.0) / (len(values) - 1))


def _signals(
    indices: np.ndarray,
    selected: int,
    direction: str,
    rank_score: np.ndarray,
    magnitude_score: np.ndarray,
    base_score: np.ndarray,
    extreme_score: np.ndarray,
    final_by_seed: list[np.ndarray],
    parent_distance: float,
) -> dict[str, float]:
    sign = 1.0 if direction == "increase" else -1.0
    rank_values = sign * rank_score[indices]
    magnitude_values = sign * magnitude_score[indices]
    base_values = base_score[indices]
    extreme_values = extreme_score[indices]
    final_values = final_by_seed[0][indices]
    if len(final_values) > 1:
        top = np.partition(final_values, -2)[-2:]
        margin = float(top.max() - top.min())
    else:
        margin = 0.0
    row = indices[selected]
    seed_values = np.asarray([values[row] for values in final_by_seed], dtype=float)
    return {
        "rank_magnitude_disagreement": abs(
            _percentile(rank_values, selected) - _percentile(magnitude_values, selected)
        ),
        "base_extreme_disagreement": abs(
            _percentile(base_values, selected) - _percentile(extreme_values, selected)
        ),
        "nearest_parent_contextual_distance": float(parent_distance),
        "top1_top2_margin": margin,
        "seed_prediction_std": float(np.std(seed_values)),
    }


def _support(value: float, reference: np.ndarray, high_is_good: bool) -> float:
    reference = np.asarray(reference, dtype=float)
    if high_is_good:
        return float(np.mean(reference <= value))
    return float(np.mean(reference >= value))


def _bootstrap_coverage(table: pd.DataFrame) -> dict[str, dict[str, float]]:
    parents = np.asarray(sorted(table["parent_id"].unique()))
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    columns = (
        "rank_percentile",
        "normalized_regret",
        "selected_utility",
        "meaningful_effect",
    )
    draws = {column: np.empty(BOOTSTRAP_RESAMPLES, dtype=float) for column in columns}
    groups = {parent: table[table["parent_id"] == parent] for parent in parents}
    for draw in range(BOOTSTRAP_RESAMPLES):
        sampled = rng.choice(parents, size=len(parents), replace=True)
        sample = pd.concat([groups[parent] for parent in sampled], ignore_index=True)
        for column in columns:
            draws[column][draw] = sample[column].mean()
    return {
        column: {
            "lower_95": float(np.quantile(values, 0.025)),
            "upper_95": float(np.quantile(values, 0.975)),
        }
        for column, values in draws.items()
    }


def main() -> None:
    frame = pd.read_csv(SOURCE)
    parents = frame["parent_id"].to_numpy()
    parent_ids = tuple(sorted(frame["parent_id"].unique()))
    rank = _load_nested("rank")
    magnitude = _load_nested("magnitude")
    extreme_arrays = np.load(EXTREME, allow_pickle=False)
    extreme_outer = {
        "increase": extreme_arrays["increase"],
        "decrease": extreme_arrays["decrease"],
    }
    extreme_inner = {
        "increase": extreme_arrays["inner_increase"],
        "decrease": extreme_arrays["inner_decrease"],
    }
    seed_arrays = {
        seed: np.load(CONTROL_CACHE / f"seed_{seed}_final_scores.npz", allow_pickle=False)
        for seed in SEEDS
    }
    primary = seed_arrays[SEEDS[0]]
    embedding_parent_ids, embeddings = _parent_embeddings(frame)
    if embedding_parent_ids != list(parent_ids):
        raise ValueError("Parent embedding order is inconsistent")
    distances = cosine_distances(embeddings)

    signal_rows = []
    high_is_good = {
        "rank_magnitude_disagreement": False,
        "base_extreme_disagreement": False,
        "nearest_parent_contextual_distance": False,
        "top1_top2_margin": True,
        "seed_prediction_std": False,
    }
    for outer_fold, outer_parent in enumerate(parent_ids):
        outer_indices = np.flatnonzero(parents == outer_parent)
        training_parent_positions = [
            index for index, value in enumerate(parent_ids) if value != outer_parent
        ]
        held_distance = float(distances[outer_fold, training_parent_positions].min())
        reference = {name: [] for name in high_is_good}
        for inner_fold, inner_parent in enumerate(parent_ids):
            if inner_parent == outer_parent:
                continue
            inner_indices = np.flatnonzero(parents == inner_parent)
            inner_training_positions = [
                index
                for index, value in enumerate(parent_ids)
                if value not in {outer_parent, inner_parent}
            ]
            inner_distance = float(distances[inner_fold, inner_training_positions].min())
            for direction in ("increase", "decrease"):
                final_key = f"inner_{direction}"
                inner_final = primary[final_key][outer_fold]
                selected = int(np.argmax(inner_final[inner_indices]))
                values = _signals(
                    inner_indices,
                    selected,
                    direction,
                    rank.inner_prediction[outer_fold],
                    magnitude.inner_prediction[outer_fold],
                    primary[f"inner_base_{direction}"][outer_fold],
                    extreme_inner[direction][outer_fold],
                    [
                        seed_arrays[seed][final_key][outer_fold]
                        for seed in SEEDS
                    ],
                    inner_distance,
                )
                for name, value in values.items():
                    reference[name].append(value)
        for direction in ("increase", "decrease"):
            final_score = primary[direction]
            selected = int(np.argmax(final_score[outer_indices]))
            held_signals = _signals(
                outer_indices,
                selected,
                direction,
                rank.prediction,
                magnitude.prediction,
                primary[f"base_{direction}"],
                extreme_outer[direction],
                [seed_arrays[seed][direction] for seed in SEEDS],
                held_distance,
            )
            row = {
                "parent_id": outer_parent,
                "direction": direction,
                "selected_source_row": int(frame.iloc[outer_indices[selected]]["source_row"]),
            }
            supports = []
            for name, value in held_signals.items():
                row[name] = value
                row[f"{name}_support"] = _support(
                    value, np.asarray(reference[name]), high_is_good[name]
                )
                supports.append(row[f"{name}_support"])
            row["confidence"] = float(np.mean(supports))
            signal_rows.append(row)
    signals = pd.DataFrame(signal_rows)

    selected_metrics = directional_metrics(
        frame,
        primary["increase"],
        primary["decrease"],
        model="remove_motif_interactions_plus_extreme",
    )
    decisions = signals.merge(
        selected_metrics,
        on=["parent_id", "direction", "selected_source_row"],
        validate="one_to_one",
    )
    decisions["meaningful_effect"] = decisions["selected_utility"] >= MEANINGFUL_EFFECT
    decisions = decisions.sort_values(
        ["confidence", "parent_id", "direction"],
        ascending=[False, True, True],
        kind="stable",
    ).reset_index(drop=True)
    decisions["confidence_rank"] = np.arange(1, len(decisions) + 1)
    decisions.to_csv(
        OUT / "confidence_decision_metrics.csv", index=False, lineterminator="\n"
    )

    coverage_rows = []
    coverage_intervals = {}
    for coverage in COVERAGES:
        retained = decisions.iloc[: int(round(len(decisions) * coverage))].copy()
        row = {
            "coverage": coverage,
            "decision_count": len(retained),
            "rank_percentile": float(retained["rank_percentile"].mean()),
            "normalized_regret": float(retained["normalized_regret"].mean()),
            "selected_utility": float(retained["selected_utility"].mean()),
            "meaningful_effect_rate": float(retained["meaningful_effect"].mean()),
            "near_oracle_rate": float(retained["near_oracle"].mean()),
        }
        coverage_rows.append(row)
        coverage_intervals[str(coverage)] = _bootstrap_coverage(retained)
    coverage_table = pd.DataFrame(coverage_rows)
    coverage_table.to_csv(
        OUT / "selective_coverage_metrics.csv", index=False, lineterminator="\n"
    )
    (OUT / "selective_coverage_bootstrap_ci.json").write_text(
        json.dumps(coverage_intervals, indent=2) + "\n", encoding="utf-8"
    )

    rho = float(spearmanr(decisions["confidence"], decisions["normalized_regret"]).statistic)
    regret = coverage_table.set_index("coverage")["normalized_regret"]
    gate = {
        "confidence_regret_spearman": rho,
        "rho_at_most_minus_0_20": bool(rho <= -0.20),
        "regret_improvement_at_60_percent": float(regret.loc[1.0] - regret.loc[0.6]),
        "sixty_percent_improves_regret_by_0_030": bool(
            regret.loc[1.0] - regret.loc[0.6] >= 0.030
        ),
        "regret_nonworsening_100_to_80_to_60": bool(
            regret.loc[1.0] >= regret.loc[0.8] >= regret.loc[0.6]
        ),
    }
    gate["pass"] = bool(
        gate["rho_at_most_minus_0_20"]
        and gate["sixty_percent_improves_regret_by_0_030"]
        and gate["regret_nonworsening_100_to_80_to_60"]
    )
    result = {
        "candidate": "remove_motif_interactions_plus_extreme",
        "signals": list(high_is_good),
        "confidence_construction": "outer-training empirical support percentiles, unweighted mean",
        "gate_J": gate,
        "protected_data_access": {
            "astrocyte_outcomes_opened": False,
            "moffatt_archive_opened": False,
        },
    }
    (OUT / "selective_prediction_gate.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(coverage_table.to_string(index=False))
    print(json.dumps(gate, indent=2))


if __name__ == "__main__":
    main()
