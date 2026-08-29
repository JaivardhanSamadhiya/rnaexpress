"""Run frozen controls, seed checks, and robustness for the selected Phase 3 model."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.modeling.v3_mechanistic_features import build_mechanistic_features
from src.modeling.v3_nested import (
    NestedResult,
    _magnitude_predict,
    directional_metrics,
    macro_metrics,
    nested_extreme,
    nested_magnitude,
    nested_ridge,
    selection_score,
)
from src.modeling.v3_stacking import add_extreme_head, rank_magnitude_stack
from src.modeling.v3_statistics import (
    bootstrap_macro_intervals,
    exact_random_expectations,
    paired_parent_robustness,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "results/v2_6/nzip_nested_stack_predictions.csv.gz"
CONTEXT = ROOT / "data/interim/v3_3utrbert_delta_features.npy"
STRUCTURE = ROOT / "data/interim/v3_nzip_structure_cache.json"
STABILITY = ROOT / "data/interim/v3_nzip_tdp_stability_prediction.npy"
ABLATION = ROOT / "data/interim/v3_mechanistic_ablations"
EXTREME = ROOT / "data/interim/v3_best_ablation_extreme.npz"
OUT = ROOT / "results/v3_phase3"
CACHE = ROOT / "data/interim/v3_final_controls"
SEEDS = (20260828, 20260829, 20260830)
NAME = "remove_motif_interactions_plus_extreme"


def _load_nested(path: Path, tuning_path: Path) -> NestedResult:
    arrays = np.load(path, allow_pickle=False)
    return NestedResult(
        arrays["prediction"],
        pd.read_csv(tuning_path),
        arrays["inner_prediction"],
    )


def _save_nested(path: Path, tuning_path: Path, result: NestedResult) -> None:
    if result.inner_prediction is None:
        raise ValueError("Nested result is missing outer-training cross-fits")
    np.savez(
        path,
        prediction=result.prediction,
        inner_prediction=result.inner_prediction,
    )
    result.tuning.to_csv(tuning_path, index=False, lineterminator="\n")


def _load_or_run_nested(
    prefix: str,
    component: str,
    runner,
) -> NestedResult:
    path = CACHE / f"{prefix}_{component}.npz"
    tuning_path = CACHE / f"{prefix}_{component}_tuning.csv"
    if path.exists() and tuning_path.exists():
        return _load_nested(path, tuning_path)
    result = runner()
    _save_nested(path, tuning_path, result)
    return result


def _load_extreme() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    arrays = np.load(EXTREME, allow_pickle=False)
    return (
        arrays["increase"],
        arrays["decrease"],
        arrays["inner_increase"],
        arrays["inner_decrease"],
    )


def _save_scores(
    prefix: str,
    frame: pd.DataFrame,
    increase: np.ndarray,
    decrease: np.ndarray,
) -> None:
    output = frame[["source_row", "parent_id", "delta_localization"]].copy()
    output["increase_score"] = increase
    output["decrease_score"] = decrease
    output.to_csv(
        OUT / f"{prefix}_predictions.csv.gz",
        index=False,
        lineterminator="\n",
        compression={"method": "gzip", "compresslevel": 9, "mtime": 0},
    )


def _final_scores(
    frame: pd.DataFrame,
    rank: NestedResult,
    magnitude: NestedResult,
    extreme: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray],
):
    base = rank_magnitude_stack(frame, rank, magnitude)
    result = add_extreme_head(frame, base, *extreme)
    return base, result


def _rerun_selected_stochastic_magnitude(
    frame: pd.DataFrame,
    features: np.ndarray,
    primary: NestedResult,
    seed: int,
) -> NestedResult:
    """Rerun only stochastic frozen selections; copy deterministic Ridge exactly."""
    if primary.inner_prediction is None:
        raise ValueError("Primary magnitude result is missing cross-fits")
    target = frame["delta_localization"].to_numpy(float)
    parents = frame["parent_id"].to_numpy()
    parent_ids = tuple(sorted(frame["parent_id"].unique()))
    prediction = primary.prediction.copy()
    inner_prediction = primary.inner_prediction.copy()
    tuning = primary.tuning.copy()
    tuning["seed"] = seed
    for outer_fold, outer_parent in enumerate(parent_ids):
        row = tuning.loc[tuning["outer_parent"] == outer_parent].iloc[0]
        family = str(row["model_family"])
        parameter = float(row["parameter"])
        if family == "ridge":
            continue
        outer_train = np.flatnonzero(parents != outer_parent)
        outer_test = np.flatnonzero(parents == outer_parent)
        prediction[outer_test] = _magnitude_predict(
            features, target, outer_train, outer_test, family, parameter, seed
        )
        for inner_parent in parent_ids:
            if inner_parent == outer_parent:
                continue
            inner_train = np.flatnonzero(
                (parents != outer_parent) & (parents != inner_parent)
            )
            inner_test = np.flatnonzero(parents == inner_parent)
            inner_prediction[outer_fold, inner_test] = _magnitude_predict(
                features, target, inner_train, inner_test, family, parameter, seed
            )
    return NestedResult(prediction, tuning, inner_prediction)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(SOURCE)
    context = np.load(CONTEXT, allow_pickle=False)
    stability = np.load(STABILITY, allow_pickle=False)
    mechanism = build_mechanistic_features(frame, STRUCTURE, stability)
    mask = mechanism.keep_without("motif_interaction")
    features = np.column_stack([context, mechanism.values[:, mask]]).astype(np.float32)

    rank = _load_nested(
        ABLATION / "remove_motif_interactions_rank.npz",
        ABLATION / "remove_motif_interactions_rank_tuning.csv",
    )
    magnitude_28 = _load_nested(
        ABLATION / "remove_motif_interactions_magnitude.npz",
        ABLATION / "remove_motif_interactions_magnitude_tuning.csv",
    )
    extreme = _load_extreme()

    seed_metrics = []
    seed_tuning = []
    seed_predictions = frame[["source_row", "parent_id", "delta_localization"]].copy()
    seed_results = {}
    for seed in SEEDS:
        if seed == SEEDS[0]:
            magnitude = magnitude_28
        else:
            magnitude = _load_or_run_nested(
                f"seed_{seed}",
                "magnitude",
                lambda seed=seed: _rerun_selected_stochastic_magnitude(
                    frame, features, magnitude_28, seed
                ),
            )
        base, final = _final_scores(frame, rank, magnitude, extreme)
        seed_results[seed] = final
        np.savez(
            CACHE / f"seed_{seed}_final_scores.npz",
            increase=final.increase,
            decrease=final.decrease,
            inner_increase=final.inner_increase,
            inner_decrease=final.inner_decrease,
            base_increase=base.increase,
            base_decrease=base.decrease,
            inner_base_increase=base.inner_increase,
            inner_base_decrease=base.inner_decrease,
        )
        seed_predictions[f"increase_score_seed_{seed}"] = final.increase
        seed_predictions[f"decrease_score_seed_{seed}"] = final.decrease
        metrics = directional_metrics(
            frame, final.increase, final.decrease, model=f"{NAME}_seed_{seed}"
        )
        row = macro_metrics(metrics)
        row.update(seed=seed, selection_score=selection_score(metrics))
        seed_metrics.append(row)
        magnitude_table = magnitude.tuning.copy()
        magnitude_table["seed"] = seed
        magnitude_table.insert(0, "component", "magnitude")
        seed_tuning.append(magnitude_table)
        base_table = base.tuning.copy()
        base_table.insert(0, "seed", seed)
        base_table.insert(1, "component", "rank_magnitude_stack")
        seed_tuning.append(base_table)
        final_table = final.tuning.copy()
        final_table.insert(0, "seed", seed)
        final_table.insert(1, "component", "extreme_stack")
        seed_tuning.append(final_table)
    seed_predictions.to_csv(
        OUT / "seed_stability_predictions.csv.gz",
        index=False,
        lineterminator="\n",
        compression={"method": "gzip", "compresslevel": 9, "mtime": 0},
    )
    pd.DataFrame(seed_metrics).to_csv(
        OUT / "seed_stability_macro_metrics.csv", index=False, lineterminator="\n"
    )
    pd.concat(seed_tuning, ignore_index=True).to_csv(
        OUT / "seed_stability_inner_selections.csv", index=False, lineterminator="\n"
    )

    # Frozen within-parent shuffled-edit-score control. Increase and decrease
    # recommendations are independently permuted because they are separate decisions.
    rng = np.random.default_rng(SEEDS[0])
    shuffled_increase = seed_results[SEEDS[0]].increase.copy()
    shuffled_decrease = seed_results[SEEDS[0]].decrease.copy()
    for indices in frame.groupby("parent_id", sort=True).indices.values():
        indices = np.asarray(indices, dtype=int)
        shuffled_increase[indices] = rng.permutation(shuffled_increase[indices])
        shuffled_decrease[indices] = rng.permutation(shuffled_decrease[indices])
    shuffled_edit_metrics = directional_metrics(
        frame,
        shuffled_increase,
        shuffled_decrease,
        model="within_parent_shuffled_edit_scores",
    )
    _save_scores("shuffled_edit_control", frame, shuffled_increase, shuffled_decrease)

    # Frozen within-parent shuffled-label control through every nested selected head.
    shuffled_frame = frame.copy()
    rng = np.random.default_rng(SEEDS[0])
    for indices in frame.groupby("parent_id", sort=True).indices.values():
        indices = np.asarray(indices, dtype=int)
        shuffled_frame.loc[indices, "delta_localization"] = rng.permutation(
            frame.loc[indices, "delta_localization"].to_numpy(float)
        )
    shuffled_rank = _load_or_run_nested(
        "shuffled_label", "rank", lambda: nested_ridge(shuffled_frame, features, "rank")
    )
    shuffled_magnitude = _load_or_run_nested(
        "shuffled_label",
        "magnitude",
        lambda: nested_magnitude(shuffled_frame, features, seed=SEEDS[0]),
    )
    shuffled_extreme_path = CACHE / "shuffled_label_extreme.npz"
    shuffled_extreme_tuning_path = CACHE / "shuffled_label_extreme_tuning.csv"
    if shuffled_extreme_path.exists() and shuffled_extreme_tuning_path.exists():
        arrays = np.load(shuffled_extreme_path, allow_pickle=False)
        shuffled_extreme = (
            arrays["increase"],
            arrays["decrease"],
            arrays["inner_increase"],
            arrays["inner_decrease"],
        )
    else:
        inc, dec, tuning, inner_inc, inner_dec = nested_extreme(
            shuffled_frame, features, return_inner=True
        )
        shuffled_extreme = (inc, dec, inner_inc, inner_dec)
        np.savez(
            shuffled_extreme_path,
            increase=inc,
            decrease=dec,
            inner_increase=inner_inc,
            inner_decrease=inner_dec,
        )
        tuning.to_csv(shuffled_extreme_tuning_path, index=False, lineterminator="\n")
    _, shuffled_label_final = _final_scores(
        shuffled_frame, shuffled_rank, shuffled_magnitude, shuffled_extreme
    )
    shuffled_label_metrics = directional_metrics(
        frame,
        shuffled_label_final.increase,
        shuffled_label_final.decrease,
        model="within_parent_shuffled_labels_complete_pipeline",
    )
    _save_scores(
        "shuffled_label_control",
        frame,
        shuffled_label_final.increase,
        shuffled_label_final.decrease,
    )

    controls = pd.concat([shuffled_edit_metrics, shuffled_label_metrics], ignore_index=True)
    controls.to_csv(
        OUT / "negative_control_parent_direction_metrics.csv",
        index=False,
        lineterminator="\n",
    )
    control_macros = []
    for model, table in controls.groupby("model", sort=True):
        row = macro_metrics(table)
        row.update(model=model, selection_score=selection_score(table))
        control_macros.append(row)
    pd.DataFrame(control_macros).to_csv(
        OUT / "negative_control_macro_metrics.csv", index=False, lineterminator="\n"
    )

    selected_metrics = directional_metrics(
        frame,
        seed_results[SEEDS[0]].increase,
        seed_results[SEEDS[0]].decrease,
        model=NAME,
    )
    v2_metrics = directional_metrics(
        frame,
        frame["pred_nested_context_external_stack"].to_numpy(float),
        -frame["pred_nested_context_external_stack"].to_numpy(float),
        model="v2_6_historical",
    )
    paired, robustness = paired_parent_robustness(selected_metrics, v2_metrics)
    paired.to_csv(
        OUT / "selected_parent_improvement.csv", index=False, lineterminator="\n"
    )
    bootstrap_macro_intervals(selected_metrics).to_csv(
        OUT / "selected_parent_bootstrap_ci.csv", index=False, lineterminator="\n"
    )
    random = exact_random_expectations(frame)
    seed_table = pd.DataFrame(seed_metrics)
    control_table = pd.DataFrame(control_macros).set_index("model")
    control_gate = {}
    for model, row in control_table.iterrows():
        control_gate[model] = {
            "rank_at_most_threshold": bool(
                row["rank_percentile"]
                <= (0.540 if "edit_scores" in model else 0.530)
            ),
            "regret_not_more_than_0_020_better_than_random": bool(
                row["normalized_regret"] >= random["normalized_regret"] - 0.020
            ),
        }
        control_gate[model]["pass"] = bool(all(control_gate[model].values()))
    seed_gate = {
        "rank_range": float(seed_table["rank_percentile"].max() - seed_table["rank_percentile"].min()),
        "normalized_regret_range": float(
            seed_table["normalized_regret"].max() - seed_table["normalized_regret"].min()
        ),
        "rank_range_at_most_0_015": bool(seed_table["rank_percentile"].max() - seed_table["rank_percentile"].min() <= 0.015),
        "regret_range_at_most_0_025": bool(seed_table["normalized_regret"].max() - seed_table["normalized_regret"].min() <= 0.025),
        "every_seed_rank_at_least_0_625": bool((seed_table["rank_percentile"] >= 0.625).all()),
        "every_seed_regret_improvement_at_least_0_020": bool(
            (0.4272520361458629 - seed_table["normalized_regret"] >= 0.020).all()
        ),
    }
    seed_gate["pass"] = bool(
        all(value for key, value in seed_gate.items() if key != "pass" and isinstance(value, bool))
    )
    summary = {
        "candidate": NAME,
        "seeds": list(SEEDS),
        "feature_count": int(features.shape[1]),
        "parent_robustness": robustness,
        "control_gate": control_gate,
        "seed_gate": seed_gate,
        "protected_data_access": {
            "astrocyte_outcomes_opened": False,
            "moffatt_archive_opened": False,
        },
    }
    (OUT / "controls_seed_robustness.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
