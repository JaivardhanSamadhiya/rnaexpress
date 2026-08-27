"""Leakage-safe baselines and intervention-aware models."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.linear_model import ElasticNet, LogisticRegression, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .features import (
    centered_context,
    compact_intervention_features,
    intervention_features,
    kmer_frequencies,
    local_features,
    normalize_sequence,
    sequence_features,
)


SEED = 20260826


@dataclass
class FeatureStore:
    frame: pd.DataFrame
    local5: np.ndarray
    local10: np.ndarray
    intervention10: np.ndarray
    compact: np.ndarray
    mutant_sequence: np.ndarray
    parent_sequence: np.ndarray
    context5: np.ndarray
    context10: np.ndarray

    @classmethod
    def build(cls, frame: pd.DataFrame) -> "FeatureStore":
        mutant = np.vstack([sequence_features(seq, 100) for seq in frame["mutant_sequence"]])
        parent = np.vstack([sequence_features(seq, 100) for seq in frame["parent_sequence"]])
        contexts: dict[int, np.ndarray] = {}
        for radius in [5, 10]:
            contexts[radius] = np.array(
                [
                    centered_context(
                        normalize_sequence(row.parent_sequence),
                        int(row.edit_position_0based),
                        radius,
                    )
                    for row in frame.itertuples(index=False)
                ],
                dtype=object,
            )
        return cls(
            frame=frame,
            local5=local_features(frame, 5),
            local10=local_features(frame, 10),
            intervention10=intervention_features(frame, 10, 100),
            compact=compact_intervention_features(frame),
            mutant_sequence=mutant,
            parent_sequence=parent,
            context5=contexts[5],
            context10=contexts[10],
        )

    def subset(self, indices: np.ndarray, feature: str) -> np.ndarray:
        return getattr(self, feature)[indices]


def substitution_mean(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    means = train.groupby(["reference_nt", "alternate_nt"])["delta_localization"].mean()
    fallback = float(train["delta_localization"].mean())
    return np.array(
        [means.get((row.reference_nt, row.alternate_nt), fallback) for row in test.itertuples()],
        dtype=float,
    )


def fit_local_ridge(
    train_indices: np.ndarray,
    test_indices: np.ndarray,
    store: FeatureStore,
    radius: int,
    alpha: float,
) -> np.ndarray:
    feature = "local5" if radius == 5 else "local10"
    model = make_pipeline(StandardScaler(), Ridge(alpha=alpha))
    model.fit(store.subset(train_indices, feature), store.frame.iloc[train_indices]["delta_localization"])
    return model.predict(store.subset(test_indices, feature))


def fit_local_elastic(
    train_indices: np.ndarray,
    test_indices: np.ndarray,
    store: FeatureStore,
    alpha: float = 0.01,
    l1_ratio: float = 0.25,
) -> np.ndarray:
    model = make_pipeline(
        StandardScaler(),
        ElasticNet(alpha=alpha, l1_ratio=l1_ratio, max_iter=5000, random_state=SEED),
    )
    model.fit(store.local10[train_indices], store.frame.iloc[train_indices]["delta_localization"])
    return model.predict(store.local10[test_indices])


def fit_local_histgb(
    train_indices: np.ndarray,
    test_indices: np.ndarray,
    store: FeatureStore,
) -> np.ndarray:
    model = HistGradientBoostingRegressor(
        learning_rate=0.05,
        max_iter=50,
        max_leaf_nodes=15,
        l2_regularization=1.0,
        random_state=SEED,
    )
    model.fit(store.local10[train_indices], store.frame.iloc[train_indices]["delta_localization"])
    return model.predict(store.local10[test_indices])


def motif_events(parent: str, mutant: str, position: int, k: int) -> list[str]:
    events: list[str] = []
    first = max(0, position - k + 1)
    last = min(position, len(parent) - k)
    for start in range(first, last + 1):
        old = parent[start : start + k]
        new = mutant[start : start + k]
        if old != new:
            events.append(f"destroy:{old}")
            events.append(f"create:{new}")
    return events


def motif_delta(
    train: pd.DataFrame,
    test: pd.DataFrame,
    k: int,
    minimum_support: int,
) -> np.ndarray:
    values: dict[str, list[float]] = defaultdict(list)
    for row in train.itertuples(index=False):
        events = motif_events(
            normalize_sequence(row.parent_sequence),
            normalize_sequence(row.mutant_sequence),
            int(row.edit_position_0based),
            k,
        )
        for event in events:
            values[event].append(float(row.delta_localization))
    learned = {
        event: float(np.mean(effect))
        for event, effect in values.items()
        if len(effect) >= minimum_support
    }
    fallback = float(train["delta_localization"].mean())
    predictions = []
    for row in test.itertuples(index=False):
        events = motif_events(
            normalize_sequence(row.parent_sequence),
            normalize_sequence(row.mutant_sequence),
            int(row.edit_position_0based),
            k,
        )
        scores = [learned[event] for event in events if event in learned]
        predictions.append(float(np.mean(scores)) if scores else fallback)
    return np.array(predictions)


def retrieval(
    train: pd.DataFrame,
    test: pd.DataFrame,
    radius: int,
    neighbors: int,
) -> np.ndarray:
    train_context = np.array(
        [
            centered_context(normalize_sequence(r.parent_sequence), int(r.edit_position_0based), radius)
            for r in train.itertuples(index=False)
        ]
    )
    train_effect = train["delta_localization"].to_numpy(float)
    groups: dict[tuple[str, str], np.ndarray] = {}
    for key, idx in train.groupby(["reference_nt", "alternate_nt"]).indices.items():
        groups[key] = np.asarray(idx, int)
    fallback = float(np.mean(train_effect))
    output = []
    for row in test.itertuples(index=False):
        candidates = groups.get((row.reference_nt, row.alternate_nt))
        if candidates is None or len(candidates) == 0:
            output.append(fallback)
            continue
        context = centered_context(
            normalize_sequence(row.parent_sequence), int(row.edit_position_0based), radius
        )
        distances = np.fromiter(
            (sum(a != b for a, b in zip(context, train_context[i])) for i in candidates),
            dtype=float,
            count=len(candidates),
        )
        take = np.argsort(distances, kind="stable")[: min(neighbors, len(candidates))]
        chosen = candidates[take]
        weights = 1.0 / (1.0 + distances[take])
        output.append(float(np.average(train_effect[chosen], weights=weights)))
    return np.asarray(output)


def extra_trees(
    leaf_size: int, max_features: float, n_estimators: int = 300
) -> ExtraTreesRegressor:
    return ExtraTreesRegressor(
        n_estimators=n_estimators,
        min_samples_leaf=leaf_size,
        max_features=max_features,
        n_jobs=-1,
        random_state=SEED,
    )


def fit_forward_extratrees(
    train_indices: np.ndarray,
    test_indices: np.ndarray,
    store: FeatureStore,
    leaf_size: int,
    max_features: float,
    n_estimators: int = 300,
) -> np.ndarray:
    train = store.frame.iloc[train_indices]
    parent_first = ~train.duplicated("parent_id")
    x_train = np.vstack(
        [store.mutant_sequence[train_indices], store.parent_sequence[train_indices][parent_first]]
    )
    y_train = np.concatenate(
        [
            train["mutant_localization_log2_neurite_soma"].to_numpy(float),
            train.loc[parent_first, "parent_localization_log2_neurite_soma"].to_numpy(float),
        ]
    )
    model = extra_trees(leaf_size, max_features, n_estimators)
    model.fit(x_train, y_train)
    return model.predict(store.mutant_sequence[test_indices]) - model.predict(
        store.parent_sequence[test_indices]
    )


def fit_intervention_extratrees(
    train_indices: np.ndarray,
    test_indices: np.ndarray,
    store: FeatureStore,
    leaf_size: int,
    max_features: float,
    prior: np.ndarray | None = None,
    n_estimators: int = 300,
) -> np.ndarray:
    features = store.intervention10
    if prior is not None:
        features = np.column_stack([features, prior])
    model = extra_trees(leaf_size, max_features, n_estimators)
    model.fit(features[train_indices], store.frame.iloc[train_indices]["delta_localization"])
    return model.predict(features[test_indices])


def pairwise_training_data(
    indices: np.ndarray,
    store: FeatureStore,
    pairs_per_parent: int = 300,
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(SEED)
    frame = store.frame.iloc[indices]
    position_by_global = {global_index: position for position, global_index in enumerate(indices)}
    differences: list[np.ndarray] = []
    labels: list[int] = []
    for _, rows in frame.groupby("parent_id"):
        global_indices = rows.index.to_numpy(int)
        local_indices = np.array([position_by_global[i] for i in global_indices])
        y = rows["delta_localization"].to_numpy(float)
        order = np.argsort(y)
        low = local_indices[order[: max(1, len(order) // 2)]]
        high = local_indices[order[max(1, len(order) // 2) :]]
        for _ in range(pairs_per_parent):
            i = int(rng.choice(high))
            j = int(rng.choice(low))
            if rng.random() < 0.5:
                differences.append(store.intervention10[indices[i]] - store.intervention10[indices[j]])
                labels.append(1)
            else:
                differences.append(store.intervention10[indices[j]] - store.intervention10[indices[i]])
                labels.append(0)
    return np.vstack(differences), np.asarray(labels)


def fit_pairwise_rank(
    train_indices: np.ndarray,
    test_indices: np.ndarray,
    store: FeatureStore,
    c_value: float,
) -> np.ndarray:
    model = train_pairwise_model(train_indices, store, c_value)
    return model.decision_function(store.intervention10[test_indices])


def train_pairwise_model(
    train_indices: np.ndarray,
    store: FeatureStore,
    c_value: float,
):
    x_pairs, labels = pairwise_training_data(train_indices, store)
    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(C=c_value, max_iter=1000, solver="liblinear", random_state=SEED),
    )
    model.fit(x_pairs, labels)
    return model


def fit_mikl_model(mikl: pd.DataFrame) -> ExtraTreesRegressor:
    features = compact_intervention_features(mikl)
    target = (
        mikl["delta_cad_localization"].to_numpy(float)
        + mikl["delta_neuro2a_localization"].to_numpy(float)
    ) / 2.0
    model = ExtraTreesRegressor(
        n_estimators=300,
        min_samples_leaf=10,
        max_features=0.5,
        n_jobs=-1,
        random_state=SEED,
    )
    model.fit(features, target)
    return model


def fit_joint_nzip_mikl(
    train_indices: np.ndarray,
    test_indices: np.ndarray,
    store: FeatureStore,
    mikl: pd.DataFrame,
) -> np.ndarray:
    mikl_x = compact_intervention_features(mikl)
    mikl_y = (
        mikl["delta_cad_localization"].to_numpy(float)
        + mikl["delta_neuro2a_localization"].to_numpy(float)
    ) / 2.0
    nzip_x = store.compact[train_indices]
    nzip_y = store.frame.iloc[train_indices]["delta_localization"].to_numpy(float)
    x = np.vstack([nzip_x, mikl_x])
    y = np.concatenate([nzip_y, mikl_y])
    # Equal aggregate weight per dataset despite different row counts.
    weights = np.concatenate(
        [
            np.full(len(nzip_y), 0.5 / len(nzip_y)),
            np.full(len(mikl_y), 0.5 / len(mikl_y)),
        ]
    )
    model = ExtraTreesRegressor(
        n_estimators=100,
        min_samples_leaf=10,
        max_features=0.25,
        n_jobs=-1,
        random_state=SEED,
    )
    model.fit(x, y, sample_weight=weights)
    return model.predict(store.compact[test_indices])


def fit_joint_arrays(
    train_indices: np.ndarray,
    test_indices: np.ndarray,
    store: FeatureStore,
    mikl_x: np.ndarray,
    mikl_y: np.ndarray,
) -> np.ndarray:
    nzip_x = store.compact[train_indices]
    nzip_y = store.frame.iloc[train_indices]["delta_localization"].to_numpy(float)
    x = np.vstack([nzip_x, mikl_x])
    y = np.concatenate([nzip_y, mikl_y])
    weights = np.concatenate(
        [
            np.full(len(nzip_y), 0.5 / len(nzip_y)),
            np.full(len(mikl_y), 0.5 / len(mikl_y)),
        ]
    )
    model = ExtraTreesRegressor(
        n_estimators=50,
        min_samples_leaf=10,
        max_features=0.25,
        n_jobs=-1,
        random_state=SEED,
    )
    model.fit(x, y, sample_weight=weights)
    return model.predict(store.compact[test_indices])
