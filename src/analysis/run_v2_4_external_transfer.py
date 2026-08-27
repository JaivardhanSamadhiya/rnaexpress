"""Run the frozen RNAddress v2.4 external-localization transfer gate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from src.analysis.hostile_internal_audit import metadata_features
from src.analysis.run_v2_2_splicebert import percentile_targets
from src.modeling.external_forward_heads import score_frozen_external_heads
from src.modeling.metrics import evaluate_predictions, parent_macro
from src.modeling.splicebert_absolute import build_splicebert_absolute_features
from src.modeling.v2_features import absolute_sequence_features


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "results" / "v2" / "nzip_development_predictions.csv.gz"
CONTEXT = ROOT / "data" / "interim" / "splicebert_v2_2_features.npy"
CONTEXT_ROWS = ROOT / "data" / "interim" / "splicebert_v2_2_source_rows.npy"
ABSOLUTE = ROOT / "data" / "interim" / "splicebert_v2_4_nzip_absolute.npy"
ABSOLUTE_SEQUENCES = ROOT / "data" / "interim" / "splicebert_v2_4_nzip_sequences.npy"
OUT_DIR = ROOT / "results" / "v2_4"
OUT_PRED = OUT_DIR / "nzip_external_transfer_predictions.csv.gz"
OUT_METRICS = OUT_DIR / "nzip_external_transfer_metrics.csv"
OUT_MACRO = OUT_DIR / "nzip_external_transfer_macro.csv"
OUT_GATE = OUT_DIR / "nzip_external_transfer_gate.json"
CONTEXT_SHA256 = "eeaca4d2c7362877755e850a8bc08fa3e3088c64ffd69fadff72ef409c165e74"
THRESHOLD = 0.6758642587586807
SEED = 20260826
PCA_COMPONENTS = 64
FINAL_FEATURES = 88


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def unique_sequences(frame: pd.DataFrame) -> list[str]:
    sequences = sorted(
        set(frame["parent_sequence"].astype(str))
        | set(frame["mutant_sequence"].astype(str))
    )
    if len(sequences) != 4_410:
        raise ValueError(f"Expected 4,410 unique N-zip sequences, observed {len(sequences)}")
    return sequences


def absolute_cache(frame: pd.DataFrame) -> tuple[list[str], np.ndarray]:
    sequences = unique_sequences(frame)
    sequence_array = np.asarray(sequences)
    if ABSOLUTE.exists() and ABSOLUTE_SEQUENCES.exists():
        cached_sequences = np.load(ABSOLUTE_SEQUENCES)
        features = np.load(ABSOLUTE)
        if np.array_equal(cached_sequences, sequence_array) and features.shape == (4_410, 1024):
            print(f"loaded cached N-zip absolute features {features.shape}", flush=True)
            return sequences, features
        raise ValueError("Stale N-zip absolute SpliceBERT cache")
    features = build_splicebert_absolute_features(
        sequences, progress_label="N-zip parent/mutant sequences"
    )
    ABSOLUTE.parent.mkdir(parents=True, exist_ok=True)
    np.save(ABSOLUTE, features, allow_pickle=False)
    np.save(ABSOLUTE_SEQUENCES, sequence_array, allow_pickle=False)
    return sequences, features


def external_delta_features(frame: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    sequences, embedded = absolute_cache(frame)
    handcrafted = absolute_sequence_features(sequences)
    absolute_predictions, labels = score_frozen_external_heads(embedded, handcrafted)
    sequence_index = {sequence: index for index, sequence in enumerate(sequences)}
    parent_indices = frame["parent_sequence"].map(sequence_index).to_numpy(int)
    mutant_indices = frame["mutant_sequence"].map(sequence_index).to_numpy(int)
    delta = absolute_predictions[mutant_indices] - absolute_predictions[parent_indices]
    if delta.shape != (len(frame), 6) or not np.isfinite(delta).all():
        raise ValueError("Frozen external delta feature matrix changed")
    return delta, labels


def load_context(frame: pd.DataFrame) -> np.ndarray:
    if file_sha256(CONTEXT) != CONTEXT_SHA256:
        raise ValueError("Frozen v2.2 contextual feature hash changed")
    rows = np.load(CONTEXT_ROWS)
    features = np.load(CONTEXT)
    if not np.array_equal(rows, frame["source_row"].to_numpy(np.int64)):
        raise ValueError("Frozen v2.2 contextual rows changed")
    if features.shape != (len(frame), 2_638):
        raise ValueError(f"Frozen v2.2 contextual feature shape changed: {features.shape}")
    return features


def lopo_transfer(
    frame: pd.DataFrame,
    context: np.ndarray,
    external: np.ndarray,
) -> np.ndarray:
    targets = percentile_targets(frame)
    metadata = metadata_features(frame)
    predictions = np.full(len(frame), np.nan, dtype=float)
    for fold, parent_id in enumerate(sorted(frame["parent_id"].unique()), start=1):
        test = frame.index[frame["parent_id"] == parent_id].to_numpy(int)
        train = frame.index[frame["parent_id"] != parent_id].to_numpy(int)
        context_scaler = StandardScaler().fit(context[train])
        context_train = context_scaler.transform(context[train])
        context_test = context_scaler.transform(context[test])
        pca = PCA(
            n_components=PCA_COMPONENTS,
            svd_solver="randomized",
            random_state=SEED,
            iterated_power=7,
        ).fit(context_train)
        train_features = np.column_stack(
            [pca.transform(context_train), metadata[train], external[train]]
        )
        test_features = np.column_stack(
            [pca.transform(context_test), metadata[test], external[test]]
        )
        if train_features.shape[1] != FINAL_FEATURES:
            raise ValueError(f"Frozen v2.4 final feature count changed: {train_features.shape[1]}")
        final_scaler = StandardScaler().fit(train_features)
        model = Ridge(
            alpha=float(FINAL_FEATURES),
            fit_intercept=True,
            solver="lsqr",
            tol=1e-6,
            max_iter=10_000,
        )
        model.fit(final_scaler.transform(train_features), targets[train])
        predictions[test] = model.predict(final_scaler.transform(test_features))
        print(f"completed v2.4 transfer fold {fold}/15: {parent_id}", flush=True)
    if not np.isfinite(predictions).all():
        raise ValueError("V2.4 transfer predictions are incomplete or non-finite")
    return predictions


def evaluate_gate(
    frame: pd.DataFrame,
    include_control: bool,
    external_labels: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    columns = {
        "external_localization_pca_ridge": "pred_external_localization_pca_ridge",
        "splicebert_percentile_ridge": "pred_splicebert_contextual_delta_ridge",
        "factorized_context_fixed": "pred_factorized_context_ranker",
        "forward_lightgbm": "pred_forward_lightgbm",
        "forward_extratrees": "pred_forward_extratrees",
        "metadata_only": "pred_metadata_only",
        "gc_only": "pred_gc_only",
        "shuffled_edit_identity": "pred_v2_4_shuffled_edit",
    }
    if include_control:
        columns["shuffled_labels_external_transfer"] = "pred_v2_4_shuffled_labels"
    metrics = evaluate_predictions(frame, columns, THRESHOLD)
    macro = parent_macro(metrics).sort_values("rank_percentile", ascending=False)
    table = macro.set_index("model")
    candidate = "external_localization_pca_ridge"
    strongest_forward = max(
        ["forward_lightgbm", "forward_extratrees"],
        key=lambda model: float(table.loc[model, "rank_percentile"]),
    )
    by_parent = metrics.groupby(["model", "parent_id"], as_index=False)[
        "rank_percentile"
    ].mean()
    custom = by_parent[by_parent["model"] == candidate].set_index("parent_id")[
        "rank_percentile"
    ]
    forward = by_parent[by_parent["model"] == strongest_forward].set_index("parent_id")[
        "rank_percentile"
    ]
    difference = custom - forward
    checks = {
        "rank_percentile_at_least_0_630": bool(table.loc[candidate, "rank_percentile"] >= 0.630),
        "gain_over_strongest_forward_at_least_0_030": bool(
            table.loc[candidate, "rank_percentile"]
            - table.loc[strongest_forward, "rank_percentile"]
            >= 0.030
        ),
        "gain_over_metadata_at_least_0_020": bool(
            table.loc[candidate, "rank_percentile"]
            - table.loc["metadata_only", "rank_percentile"]
            >= 0.020
        ),
        "improves_at_least_9_of_15_parents": bool((difference > 0).sum() >= 9),
        "positive_after_removing_two_best_parents": bool(
            difference.drop(difference.nlargest(2).index).mean() > 0
        ),
        "shuffled_edit_at_most_0_540": bool(
            table.loc["shuffled_edit_identity", "rank_percentile"] <= 0.540
        ),
    }
    if include_control:
        checks["shuffled_labels_at_most_0_530"] = bool(
            table.loc["shuffled_labels_external_transfer", "rank_percentile"] <= 0.530
        )
    gate = {
        "selected_custom": candidate,
        "strongest_forward": strongest_forward,
        "context_feature_sha256": file_sha256(CONTEXT),
        "absolute_feature_sha256": file_sha256(ABSOLUTE),
        "absolute_sequence_sha256": file_sha256(ABSOLUTE_SEQUENCES),
        "external_head_labels": external_labels,
        "pca_components": PCA_COMPONENTS,
        "ridge_alpha": FINAL_FEATURES,
        "gate_checks": checks,
        "primary_gate_pass": bool(all(list(checks.values())[:6])),
        "development_gate_pass": bool(include_control and all(checks.values())),
        "shuffled_label_control_run": include_control,
        "note": "TDP-43 locked outcomes and astrocyte outcomes remained sealed.",
    }
    return metrics, macro, gate


def save(frame: pd.DataFrame, metrics: pd.DataFrame, macro: pd.DataFrame, gate: dict[str, object]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUT_PRED, index=False, compression="gzip")
    metrics.to_csv(OUT_METRICS, index=False)
    macro.to_csv(OUT_MACRO, index=False)
    OUT_GATE.write_text(json.dumps(gate, indent=2) + "\n")
    print(macro[["model", "rank_percentile", "normalized_regret", "spearman"]].to_string(index=False))
    print(json.dumps(gate, indent=2), flush=True)


def main() -> None:
    frame = pd.read_csv(SOURCE)
    if len(frame) != 4_395 or frame["parent_id"].nunique() != 15:
        raise ValueError("N-zip v2.4 candidate set changed")
    context = load_context(frame)
    external, labels = external_delta_features(frame)
    frame["pred_external_localization_pca_ridge"] = lopo_transfer(frame, context, external)
    rng = np.random.default_rng(SEED)
    frame["pred_v2_4_shuffled_edit"] = frame.groupby("parent_id")[
        "pred_external_localization_pca_ridge"
    ].transform(lambda values: rng.permutation(values.to_numpy()))
    metrics, macro, gate = evaluate_gate(frame, False, labels)
    save(frame, metrics, macro, gate)
    if not gate["primary_gate_pass"]:
        print("Primary v2.4 checks failed; shuffled-label control was not run.", flush=True)
        return

    shuffled = frame.copy()
    shuffle_rng = np.random.default_rng(SEED)
    shuffled["delta_localization"] = shuffled.groupby("parent_id")[
        "delta_localization"
    ].transform(lambda values: shuffle_rng.permutation(values.to_numpy()))
    frame["pred_v2_4_shuffled_labels"] = lopo_transfer(shuffled, context, external)
    metrics, macro, gate = evaluate_gate(frame, True, labels)
    save(frame, metrics, macro, gate)


if __name__ == "__main__":
    main()
