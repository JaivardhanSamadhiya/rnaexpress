"""Frozen context-residual components for RNAddress v4 Phase B2.

The module intentionally contains no data-loading path.  Callers must provide
the certified Phase B rows and frozen embedding blocks.  This keeps protected
datasets outside the B2 modeling surface and makes the leakage invariants easy
to test in isolation.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from src.modeling.v4_decision_models import source_set_weights


SEED = 42_017
ALPHAS = (10.0, 100.0, 1_000.0)
RANKS = (4, 8, 16)
EDIT_BANDS = ("1", "2-5", "6-10", "11-25", "26-50", ">50")


def edit_band(values: pd.Series | np.ndarray) -> pd.Series:
    """Return the frozen Phase B2 edit-cost bands."""
    series = pd.Series(values, copy=False)
    return pd.cut(
        series,
        bins=[0, 1, 5, 10, 25, 50, np.inf],
        labels=list(EDIT_BANDS),
        include_lowest=True,
        right=True,
    ).astype(str)


def operation_signature(frame: pd.DataFrame) -> pd.Series:
    fields = (
        ("S", "substitution_count"),
        ("I", "insertion_length"),
        ("D", "deletion_length"),
        ("R", "replacement_length"),
    )
    values = []
    for row in frame[list(column for _, column in fields)].itertuples(index=False, name=None):
        token = "".join(label for (label, _), value in zip(fields, row) if float(value) > 0)
        values.append(token or "none")
    return pd.Series(values, index=frame.index, dtype=str)


def add_matching_keys(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    output["phaseB2_edit_band"] = edit_band(output["edit_cost"]).to_numpy()
    output["phaseB2_operation_signature"] = operation_signature(output).to_numpy()
    output["phaseB2_motif"] = output["motif_family"].fillna("none").astype(str)
    cross = [
        "dataset",
        "assay_context",
        "intervention_class",
        "phaseB2_motif",
        "phaseB2_edit_band",
        "phaseB2_operation_signature",
    ]
    within = [
        "decision_set_id",
        "intervention_class",
        "phaseB2_motif",
        "phaseB2_edit_band",
        "phaseB2_operation_signature",
    ]
    output["phaseB2_cross_stratum"] = output[cross].astype(str).agg("||".join, axis=1)
    output["phaseB2_within_stratum"] = output[within].astype(str).agg("||".join, axis=1)
    return output


def _stable_hash(value: object) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def matched_pairs(frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    """Freeze outcome-blind cross-parent and within-parent contrast pairs.

    Returned indices are positional indices into ``frame``.  Cross-parent
    strata satisfy the prespecified 20-row/five-unit threshold and retain no
    more than two rows per unit.  Within-parent strata require four candidates
    and contribute no more than four deterministic adjacent pairs.
    """
    keyed = add_matching_keys(frame.reset_index(drop=True))
    cross_pairs: list[tuple[int, int]] = []
    audit: list[dict[str, object]] = []
    for stratum, raw_indices in keyed.groupby("phaseB2_cross_stratum", sort=True).indices.items():
        indices = np.asarray(raw_indices, dtype=int)
        units = keyed.iloc[indices]["biological_unit"].astype(str)
        eligible = len(indices) >= 20 and units.nunique() >= 5
        retained: list[int] = []
        if eligible:
            for _, unit_indices in keyed.iloc[indices].groupby("biological_unit", sort=True).indices.items():
                absolute = indices[np.asarray(unit_indices, dtype=int)]
                ordered = sorted(absolute, key=lambda i: _stable_hash(keyed.iloc[i]["candidate_id"]))
                retained.extend(ordered[:2])
            retained.sort(key=lambda i: (_stable_hash(keyed.iloc[i]["candidate_id"]), str(keyed.iloc[i]["biological_unit"])))
            # Pair neighboring rows after rotating until units differ.  Every
            # retained row is used at most once in this cross-parent pass.
            available = retained.copy()
            while len(available) >= 2:
                left = available.pop(0)
                right_position = next(
                    (j for j, value in enumerate(available)
                     if keyed.iloc[value]["biological_unit"] != keyed.iloc[left]["biological_unit"]),
                    None,
                )
                if right_position is None:
                    break
                right = available.pop(right_position)
                cross_pairs.append((left, right))
        audit.append(
            {
                "kind": "cross_parent",
                "stratum": stratum,
                "rows": int(len(indices)),
                "biological_units": int(units.nunique()),
                "eligible": bool(eligible),
                "retained_rows": int(len(retained)),
            }
        )

    within_pairs: list[tuple[int, int]] = []
    for stratum, raw_indices in keyed.groupby("phaseB2_within_stratum", sort=True).indices.items():
        indices = np.asarray(raw_indices, dtype=int)
        eligible = len(indices) >= 4
        ordered = sorted(indices, key=lambda i: _stable_hash(keyed.iloc[i]["candidate_id"]))
        pairs = [(ordered[j], ordered[j + 1]) for j in range(min(4, len(ordered) - 1))] if eligible else []
        within_pairs.extend(pairs)
        audit.append(
            {
                "kind": "within_parent",
                "stratum": stratum,
                "rows": int(len(indices)),
                "biological_units": int(keyed.iloc[indices]["biological_unit"].nunique()),
                "eligible": bool(eligible),
                "retained_pairs": int(len(pairs)),
            }
        )
    return (
        np.asarray(cross_pairs, dtype=int).reshape(-1, 2),
        np.asarray(within_pairs, dtype=int).reshape(-1, 2),
        pd.DataFrame(audit),
    )


def deterministic_projection(input_size: int, output_size: int, seed: int) -> np.ndarray:
    """Outcome-independent orthonormal Gaussian projection."""
    if output_size > input_size:
        raise ValueError("Projection output cannot exceed input size")
    rng = np.random.default_rng(seed)
    matrix = rng.normal(size=(input_size, output_size))
    q, r = np.linalg.qr(matrix)
    signs = np.where(np.diag(r) < 0, -1.0, 1.0)
    return (q * signs).astype(np.float32)


@dataclass(frozen=True)
class ContextBlocks:
    parent: np.ndarray
    delta: np.ndarray
    numeric: np.ndarray
    parent_main: np.ndarray
    delta_main: np.ndarray
    parent_interaction: np.ndarray
    delta_interaction: np.ndarray

    def features(self, family: str, rank: int = 0) -> tuple[np.ndarray, slice | None]:
        base = np.column_stack([self.parent_main, self.delta_main, self.numeric]).astype(np.float32)
        if family == "M1" or rank == 0:
            return base, None
        if family not in {"M2", "M3", "M4"}:
            raise ValueError(f"Unknown context family: {family}")
        interaction = self.parent_interaction[:, :rank] * self.delta_interaction[:, :rank]
        start = base.shape[1]
        return np.column_stack([base, interaction]).astype(np.float32), slice(start, start + rank)

    def parent_invariant(self) -> np.ndarray:
        return np.column_stack([self.delta_main, self.numeric]).astype(np.float32)


def build_context_blocks(parent: np.ndarray, delta: np.ndarray, frame: pd.DataFrame) -> ContextBlocks:
    if parent.shape != delta.shape or parent.shape[1] != 128:
        raise ValueError("B2 expects aligned 128-dimensional parent and contextual-delta blocks")
    parent_projection = deterministic_projection(128, 32, SEED)
    delta_projection = deterministic_projection(128, 32, SEED + 1)
    parent_interaction = deterministic_projection(128, 16, SEED + 2)
    delta_interaction = deterministic_projection(128, 16, SEED + 3)
    length = frame["parent_sequence"].str.len().to_numpy(float)
    numeric = np.column_stack(
        [
            np.log1p(frame["edit_cost"].to_numpy(float)),
            frame["edit_fraction"].to_numpy(float),
            frame["mean_edit_position_1based"].to_numpy(float) / length,
            frame["edit_span_length"].to_numpy(float) / length,
        ]
    ).astype(np.float32)
    return ContextBlocks(
        parent=np.asarray(parent, dtype=np.float32),
        delta=np.asarray(delta, dtype=np.float32),
        numeric=numeric,
        parent_main=np.asarray(parent @ parent_projection, dtype=np.float32),
        delta_main=np.asarray(delta @ delta_projection, dtype=np.float32),
        parent_interaction=np.asarray(parent @ parent_interaction, dtype=np.float32),
        delta_interaction=np.asarray(delta @ delta_interaction, dtype=np.float32),
    )


@dataclass
class NuisanceModel:
    scaler: StandardScaler
    global_model: Ridge
    source_models: dict[str, Ridge]
    training_units: frozenset[str]
    training_sources: frozenset[str]

    def predict(self, features: np.ndarray, contexts: pd.Series, use_source: bool) -> np.ndarray:
        transformed = self.scaler.transform(features)
        prediction = np.asarray(self.global_model.predict(transformed), dtype=float)
        if use_source:
            context_values = contexts.astype(str).to_numpy()
            for context, model in self.source_models.items():
                mask = context_values == context
                if mask.any():
                    prediction[mask] += model.predict(transformed[mask])
        return prediction


def fit_nuisance(features: np.ndarray, frame: pd.DataFrame, source_specific: bool) -> NuisanceModel:
    if len(features) != len(frame):
        raise ValueError("Nuisance features and rows are misaligned")
    scaler = StandardScaler().fit(features)
    transformed = scaler.transform(features)
    weights = source_set_weights(frame)
    target = frame["localization_effect"].to_numpy(float)
    global_model = Ridge(alpha=100.0)
    global_model.fit(transformed, target, sample_weight=weights)
    source_models: dict[str, Ridge] = {}
    if source_specific:
        residual = target - global_model.predict(transformed)
        contexts = frame["assay_context"].astype(str).to_numpy()
        for context in sorted(set(contexts)):
            mask = contexts == context
            if mask.sum() < 20:
                continue
            model = Ridge(alpha=100.0)
            model.fit(transformed[mask], residual[mask], sample_weight=weights[mask])
            source_models[context] = model
    return NuisanceModel(
        scaler=scaler,
        global_model=global_model,
        source_models=source_models,
        training_units=frozenset(frame["biological_unit"].astype(str)),
        training_sources=frozenset(frame["dataset"].astype(str)),
    )


def cross_fitted_nuisance(
    features: np.ndarray,
    frame: pd.DataFrame,
    source_specific: bool,
    fold_column: str = "biological_fold",
) -> tuple[np.ndarray, pd.DataFrame]:
    """Generate nuisance predictions with each complete biological fold held out."""
    predictions = np.full(len(frame), np.nan, dtype=float)
    audit: list[dict[str, object]] = []
    fold_values = frame[fold_column].to_numpy()
    for fold in sorted(pd.unique(fold_values)):
        test = fold_values == fold
        train = ~test
        if not train.any() or not test.any():
            raise ValueError(f"Invalid cross-fitting fold {fold}")
        train_rows = frame.loc[train].reset_index(drop=True)
        test_rows = frame.loc[test].reset_index(drop=True)
        overlap = set(train_rows["biological_unit"]) & set(test_rows["biological_unit"])
        if overlap:
            raise ValueError(f"Biological-unit leakage in nuisance fold {fold}")
        model = fit_nuisance(features[train], train_rows, source_specific)
        predictions[test] = model.predict(
            features[test], test_rows["assay_context"], use_source=source_specific
        )
        audit.append(
            {
                "fold": int(fold) if isinstance(fold, (int, np.integer)) else str(fold),
                "train_rows": int(train.sum()),
                "test_rows": int(test.sum()),
                "train_units": int(train_rows["biological_unit"].nunique()),
                "test_units": int(test_rows["biological_unit"].nunique()),
                "unit_overlap": 0,
                "source_specific": bool(source_specific),
            }
        )
    if not np.isfinite(predictions).all():
        raise ValueError("Cross-fitted nuisance predictions are incomplete")
    return predictions, pd.DataFrame(audit)


@dataclass
class ContextModel:
    scaler: StandardScaler
    model: Ridge
    family: str
    rank: int
    alpha: float
    interaction_slice: slice | None
    training_units: frozenset[str]
    group_factors: dict[str, float]

    def predict(self, features: np.ndarray, interaction_knockout: bool = False) -> np.ndarray:
        values = np.asarray(features, dtype=np.float32)
        if interaction_knockout and self.interaction_slice is not None:
            values = values.copy()
            values[:, self.interaction_slice] = 0.0
        return np.asarray(self.model.predict(self.scaler.transform(values)), dtype=float)


def _augment_contrasts(
    transformed: np.ndarray,
    target: np.ndarray,
    pairs: tuple[np.ndarray, np.ndarray] | None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if pairs is None:
        return transformed, target, np.empty(0, dtype=float)
    valid = [pair for block in pairs for pair in np.asarray(block, dtype=int).reshape(-1, 2)]
    if not valid:
        return transformed, target, np.empty(0, dtype=float)
    pair_array = np.asarray(valid, dtype=int)
    differences = transformed[pair_array[:, 0]] - transformed[pair_array[:, 1]]
    targets = target[pair_array[:, 0]] - target[pair_array[:, 1]]
    return np.row_stack([transformed, differences]), np.concatenate([target, targets]), np.full(len(pair_array), 0.5)


def fit_context(
    features: np.ndarray,
    target: np.ndarray,
    frame: pd.DataFrame,
    family: str,
    rank: int,
    alpha: float,
    interaction_slice: slice | None,
    pairs: tuple[np.ndarray, np.ndarray] | None = None,
    group_robust: bool = False,
) -> ContextModel:
    scaler = StandardScaler().fit(features)
    transformed = scaler.transform(features)
    ordinary_weights = source_set_weights(frame)
    group_factors: dict[str, float] = {}
    if group_robust:
        first = Ridge(alpha=alpha)
        first.fit(transformed, target, sample_weight=ordinary_weights)
        errors = (target - first.predict(transformed)) ** 2
        groups = frame["dataset"].astype(str).to_numpy()
        group_mse = {group: float(errors[groups == group].mean()) for group in sorted(set(groups))}
        inverse = {group: 1.0 / max(value, 1e-12) for group, value in group_mse.items()}
        normalizer = float(np.mean(list(inverse.values())))
        group_factors = {
            group: float(np.clip(value / normalizer, 0.5, 2.0)) for group, value in inverse.items()
        }
        ordinary_weights = ordinary_weights * np.asarray([group_factors[group] for group in groups])
    x_fit, y_fit, contrast_weights = _augment_contrasts(transformed, target, pairs)
    weights = ordinary_weights
    if len(contrast_weights):
        weights = np.concatenate([ordinary_weights, contrast_weights])
    model = Ridge(alpha=alpha)
    model.fit(x_fit, y_fit, sample_weight=weights)
    return ContextModel(
        scaler=scaler,
        model=model,
        family=family,
        rank=rank,
        alpha=alpha,
        interaction_slice=interaction_slice,
        training_units=frozenset(frame["biological_unit"].astype(str)),
        group_factors=group_factors,
    )


def control_donor_indices(frame: pd.DataFrame, seed: int = SEED) -> tuple[np.ndarray, np.ndarray]:
    """Map each eligible row to a geometry-matched row from another unit."""
    keyed = add_matching_keys(frame.reset_index(drop=True))
    donors = np.arange(len(keyed), dtype=int)
    eligible = np.zeros(len(keyed), dtype=bool)
    for stratum, raw_indices in keyed.groupby("phaseB2_cross_stratum", sort=True).indices.items():
        indices = np.asarray(raw_indices, dtype=int)
        by_unit = {
            str(unit): sorted(values, key=lambda i: _stable_hash(f"{seed}|{stratum}|{keyed.iloc[i]['candidate_id']}"))
            for unit, local in keyed.iloc[indices].groupby("biological_unit", sort=True).indices.items()
            for values in [indices[np.asarray(local, dtype=int)].tolist()]
        }
        units = sorted(by_unit)
        if len(units) < 2:
            continue
        for position, unit in enumerate(units):
            donor_unit = units[(position + 1) % len(units)]
            donor_rows = by_unit[donor_unit]
            for j, row_index in enumerate(by_unit[unit]):
                donors[row_index] = donor_rows[j % len(donor_rows)]
                eligible[row_index] = True
    if np.any(keyed.loc[eligible, "biological_unit"].to_numpy() == keyed.iloc[donors[eligible]]["biological_unit"].to_numpy()):
        raise ValueError("Context control retained the same biological unit")
    return donors, eligible


def assert_held_out(train: pd.DataFrame, test: pd.DataFrame, column: str) -> None:
    overlap = set(train[column].astype(str)) & set(test[column].astype(str))
    if overlap:
        raise ValueError(f"Held-out {column} leaked into training: {sorted(overlap)[:3]}")

