"""Post-lock hostile audit. Astrocyte outcomes are never accessed."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.linear_model import Ridge

from src.modeling.development_benchmark import ALL_METHODS
from src.modeling.features import kmer_frequencies, normalize_sequence
from src.modeling.metrics import evaluate_predictions, parent_macro
from src.modeling.models import FeatureStore, train_pairwise_model


ROOT = Path(__file__).resolve().parents[2]
NZIP = ROOT / "data/processed/nzip_snv_intervention_pairs.csv.gz"
DEV = ROOT / "results/internal/development_predictions.csv.gz"
LOCK = ROOT / "results/internal/frozen_locked_predictions.csv.gz"
OUT_DIR = ROOT / "results/internal"
OUT_MACRO = OUT_DIR / "hostile_combined_macro.csv"
OUT_PARENT = OUT_DIR / "hostile_combined_parent_metrics.csv"
OUT_SENSITIVITY = OUT_DIR / "hostile_sensitivity.csv"
OUT_SIMILARITY = OUT_DIR / "parent_similarity.csv"
OUT_REPORT = ROOT / "reports/hostile_internal_audit.md"
THRESHOLD = 0.6758642587586807


def metadata_features(frame: pd.DataFrame) -> np.ndarray:
    rows = []
    bases = "ACGT"
    for row in frame.itertuples(index=False):
        substitution = np.zeros(16)
        substitution[bases.index(row.reference_nt) * 4 + bases.index(row.alternate_nt)] = 1
        rows.append(
            np.concatenate(
                [
                    substitution,
                    [
                        row.edit_position_0based / (len(row.parent_sequence) - 1),
                        len(row.parent_sequence) / 100,
                    ],
                ]
            )
        )
    return np.vstack(rows)


def gc_features(frame: pd.DataFrame) -> np.ndarray:
    rows = []
    for row in frame.itertuples(index=False):
        parent = normalize_sequence(row.parent_sequence)
        mutant = normalize_sequence(row.mutant_sequence)
        pos = int(row.edit_position_0based)
        local_parent = parent[max(0, pos - 10) : pos + 11]
        local_mutant = mutant[max(0, pos - 10) : pos + 11]

        def gc(seq: str) -> float:
            return (seq.count("G") + seq.count("C")) / len(seq)

        rows.append([gc(parent), gc(mutant) - gc(parent), gc(local_parent), gc(local_mutant) - gc(local_parent), pos / (len(parent) - 1)])
    return np.asarray(rows)


def lopo_ridge(frame: pd.DataFrame, features: np.ndarray) -> np.ndarray:
    predictions = np.zeros(len(frame))
    for parent in sorted(frame["parent_id"].unique()):
        test = frame["parent_id"].to_numpy() == parent
        train = ~test
        model = Ridge(alpha=10.0)
        model.fit(features[train], frame.loc[train, "delta_localization"])
        predictions[test] = model.predict(features[test])
    return predictions


def main() -> None:
    labels = pd.read_csv(NZIP)
    dev = pd.read_csv(DEV)
    lock = pd.read_csv(LOCK)
    lock = lock.merge(
        labels[["source_row", "parent_id", "delta_localization"]],
        on=["source_row", "parent_id"],
        validate="one_to_one",
    )
    common = [
        "source_row",
        "parent_id",
        "gene_name",
        "parent_sequence",
        "edit_position_0based",
        "edit_position_1based",
        "reference_nt",
        "alternate_nt",
        "mutant_sequence",
        "delta_localization",
        *[f"pred_{method}" for method in ALL_METHODS],
    ]
    frame = pd.concat([dev[common], lock[common]], ignore_index=True)
    if len(frame) != 4395 or frame["parent_id"].nunique() != 15:
        raise AssertionError("Combined internal candidate set changed")

    frame["pred_metadata_only"] = lopo_ridge(frame, metadata_features(frame))
    frame["pred_gc_only"] = lopo_ridge(frame, gc_features(frame))
    rng = np.random.default_rng(20260826)
    frame["pred_shuffled_edit_identity"] = frame.groupby("parent_id")[
        "pred_pairwise_rank"
    ].transform(lambda values: rng.permutation(values.to_numpy()))

    parent_sequences = frame[["parent_id", "parent_sequence"]].drop_duplicates().sort_values("parent_id")
    kmer = np.vstack([kmer_frequencies(normalize_sequence(seq), (3,)) for seq in parent_sequences["parent_sequence"]])
    norms = np.linalg.norm(kmer, axis=1, keepdims=True)
    similarity = (kmer / norms) @ (kmer / norms).T
    clustering = KMeans(n_clusters=5, random_state=20260826, n_init=50).fit(kmer)
    cluster_by_parent = dict(zip(parent_sequences["parent_id"], clustering.labels_))
    frame["sequence_cluster"] = frame["parent_id"].map(cluster_by_parent)

    store = FeatureStore.build(frame)
    cluster_prediction = np.zeros(len(frame))
    for cluster in sorted(frame["sequence_cluster"].unique()):
        test_indices = frame.index[frame["sequence_cluster"] == cluster].to_numpy(int)
        train_indices = frame.index[frame["sequence_cluster"] != cluster].to_numpy(int)
        model = train_pairwise_model(train_indices, store, c_value=1.0)
        cluster_prediction[test_indices] = model.decision_function(
            store.intervention10[test_indices]
        )
    frame["pred_pairwise_cluster_heldout"] = cluster_prediction

    similarity_rows = []
    ids = parent_sequences["parent_id"].tolist()
    for i, parent in enumerate(ids):
        others = [j for j in range(len(ids)) if j != i]
        closest = max(others, key=lambda j: similarity[i, j])
        similarity_rows.append(
            {
                "parent_id": parent,
                "cluster": int(clustering.labels_[i]),
                "closest_parent": ids[closest],
                "closest_3mer_cosine": float(similarity[i, closest]),
                "exact_duplicate": bool(
                    parent_sequences.iloc[i]["parent_sequence"]
                    in set(parent_sequences.drop(parent_sequences.index[i])["parent_sequence"])
                ),
            }
        )
    pd.DataFrame(similarity_rows).to_csv(OUT_SIMILARITY, index=False)

    prediction_columns = {method: f"pred_{method}" for method in ALL_METHODS}
    prediction_columns.update(
        {
            "metadata_only": "pred_metadata_only",
            "gc_only": "pred_gc_only",
            "shuffled_edit_identity": "pred_shuffled_edit_identity",
            "pairwise_cluster_heldout": "pred_pairwise_cluster_heldout",
        }
    )
    metrics = evaluate_predictions(frame, prediction_columns, THRESHOLD)
    macro = parent_macro(metrics).sort_values("rank_percentile", ascending=False)
    macro.to_csv(OUT_MACRO, index=False)
    parent = metrics.groupby(["model", "parent_id"], as_index=False)[
        ["rank_percentile", "normalized_regret", "spearman", "success_at_1", "success_at_3", "success_at_5"]
    ].mean()
    parent.to_csv(OUT_PARENT, index=False)

    sensitivity = []
    pairwise_parent = parent[parent["model"] == "pairwise_rank"].set_index("parent_id")
    forward_parent = parent[parent["model"] == "forward_extratrees"].set_index("parent_id")
    differences = pairwise_parent["rank_percentile"] - forward_parent["rank_percentile"]
    for removed in [None, differences.idxmax(), differences.idxmin()]:
        keep = differences.index if removed is None else differences.index[differences.index != removed]
        sensitivity.append(
            {
                "analysis": "all_parents" if removed is None else f"remove_{removed}",
                "parents": len(keep),
                "pairwise_minus_forward_rank_percentile": float(differences.loc[keep].mean()),
            }
        )
    for threshold in [0.25, THRESHOLD, 1.0]:
        threshold_metrics = evaluate_predictions(
            frame,
            {
                "pairwise_rank": "pred_pairwise_rank",
                "forward_extratrees": "pred_forward_extratrees",
                "retrieval": "pred_retrieval",
            },
            threshold,
        )
        threshold_macro = parent_macro(threshold_metrics).set_index("model")
        for model in threshold_macro.index:
            sensitivity.append(
                {
                    "analysis": f"threshold_{threshold:.6f}_{model}",
                    "parents": 15,
                    "success_at_3": float(threshold_macro.loc[model, "success_at_3"]),
                    "success_at_5": float(threshold_macro.loc[model, "success_at_5"]),
                }
            )
    pd.DataFrame(sensitivity).to_csv(OUT_SENSITIVITY, index=False)

    table = macro.set_index("model")
    lines = [
        "# Hostile internal audit",
        "",
        "This analysis is post-lock and diagnostic. It cannot rescue the failed confirmatory gate. Astrocyte outcomes remain sealed.",
        "",
        "## Fifteen-parent cross-fitted descriptive result",
        "",
        "| Model | Rank percentile | Normalized regret | Spearman |",
        "|---|---:|---:|---:|",
    ]
    for model in [
        "pairwise_rank",
        "forward_extratrees",
        "retrieval",
        "pairwise_cluster_heldout",
        "metadata_only",
        "gc_only",
        "shuffled_edit_identity",
    ]:
        row = table.loc[model]
        lines.append(
            f"| {model} | {row['rank_percentile']:.3f} | {row['normalized_regret']:.3f} | {row['spearman']:.3f} |"
        )
    lines += [
        "",
        f"Pairwise-minus-forward rank-percentile difference across all 15 parents: {differences.mean():.3f}.",
        f"Removing its strongest supporting parent changes this to {differences.drop(differences.idxmax()).mean():.3f}; removing its weakest changes it to {differences.drop(differences.idxmin()).mean():.3f}.",
        "",
        f"The closest-parent 3-mer cosine similarity ranges from {pd.DataFrame(similarity_rows)['closest_3mer_cosine'].min():.3f} to {pd.DataFrame(similarity_rows)['closest_3mer_cosine'].max():.3f}; exact duplicate parents: {sum(row['exact_duplicate'] for row in similarity_rows)}.",
        "",
        "## Hostile verdict",
        "",
        "The custom pairwise objective has a descriptive cross-fitted signal, but it did not beat the strong forward model on the untouched three-parent lock. Any claim that the custom algorithm is necessary is rejected. The scientifically defensible conclusion is that forward-model exhaustive search is currently at least as credible, while parent-level uncertainty remains large.",
    ]
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
