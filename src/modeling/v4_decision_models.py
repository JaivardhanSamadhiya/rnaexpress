"""Leakage-safe candidate-selection models and metrics for RNAddress v4."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
import torch
from scipy.stats import rankdata, spearmanr
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.preprocessing import StandardScaler


INTERVENTION_CLASSES = (
    "motif_random_replacement",
    "tdp43_motif_complement_replacement",
    "sufficiency_background_replacement",
    "necessity_deletion_with_inactive_padding",
    "random_substitution",
    "regional_shuffle",
    "shape_structure_perturbation",
)
EDIT_TIERS = (
    "exact_snv",
    "small_local_edit",
    "motif_scale_edit",
    "regional_edit",
    "large_element_edit",
)
GOOD_REGRET = 0.10


def geometry_features(frame: pd.DataFrame, categories: bool = True) -> np.ndarray:
    length = frame["parent_sequence"].str.len().to_numpy(float)
    numeric = np.column_stack(
        [
            np.log1p(frame["edit_distance"].to_numpy(float)),
            frame["edit_fraction"].to_numpy(float),
            np.log1p(frame["edit_cost"].to_numpy(float)),
            np.log1p(frame["substitution_count"].to_numpy(float)),
            np.log1p(frame["insertion_length"].to_numpy(float)),
            np.log1p(frame["deletion_length"].to_numpy(float)),
            np.log1p(frame["replacement_length"].to_numpy(float)),
            np.log1p(frame["changed_block_count"].to_numpy(float)),
            frame["mean_edit_position_1based"].to_numpy(float) / length,
            frame["first_edit_position_1based"].to_numpy(float) / length,
            frame["last_edit_position_1based"].to_numpy(float) / length,
            frame["edit_span_length"].to_numpy(float) / length,
        ]
    )
    composition = np.asarray(
        [
            [(mutant.count(base) - parent.count(base)) / len(parent) for base in "ACGT"]
            for parent, mutant in zip(frame["parent_sequence"], frame["mutant_sequence"])
        ],
        dtype=np.float32,
    )
    blocks = [numeric, composition]
    if categories:
        blocks.extend(
            frame["intervention_class"].eq(value).to_numpy(float)[:, None]
            for value in INTERVENTION_CLASSES
        )
        blocks.extend(
            frame["edit_tier"].eq(value).to_numpy(float)[:, None] for value in EDIT_TIERS
        )
    output = np.column_stack(blocks).astype(np.float32)
    if not np.isfinite(output).all():
        raise ValueError("Edit geometry contains non-finite values")
    return output


def assay_context(frame: pd.DataFrame) -> pd.Series:
    return frame[["dataset", "assay", "reporter", "cell_type"]].astype(str).agg("|".join, axis=1)


def biological_unit(frame: pd.DataFrame) -> pd.Series:
    values = []
    for row in frame.to_dict("records"):
        if row["dataset"] == "mikl_gse173098":
            values.append(f"mikl_gene:{str(row['gene_name']).lower()}")
        elif row["dataset"] == "tdp43_gse288185":
            values.append(f"tdp_gene:{row['gene_id']}")
        else:
            parent_sequence_hash = hashlib.sha256(
                str(row["parent_sequence"]).encode("ascii")
            ).hexdigest()
            values.append(f"moffatt_parent_sequence:{parent_sequence_hash}")
    return pd.Series(values, index=frame.index, dtype=str)


def biological_fold(unit: str, folds: int = 5) -> int:
    return int(hashlib.sha256(unit.encode("utf-8")).hexdigest()[:8], 16) % folds


def add_model_keys(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    output["biological_unit"] = biological_unit(output)
    output["biological_fold"] = output["biological_unit"].map(biological_fold).astype(int)
    output["assay_context"] = assay_context(output)
    return output


def normalized_utility(frame: pd.DataFrame, sign: int) -> np.ndarray:
    signed = frame["localization_effect"].to_numpy(float) * sign
    values = pd.Series(signed, index=frame.index)
    minimum = values.groupby(frame["decision_set_id"]).transform("min").to_numpy()
    maximum = values.groupby(frame["decision_set_id"]).transform("max").to_numpy()
    scale = maximum - minimum
    if not np.all(scale > 0):
        raise ValueError("A training/evaluation decision set has zero utility range")
    return (signed - minimum) / scale


def source_set_weights(frame: pd.DataFrame) -> np.ndarray:
    set_sizes = frame.groupby("decision_set_id")["candidate_id"].transform("size").to_numpy(float)
    unit_sets = frame.groupby("biological_unit")["decision_set_id"].transform("nunique").to_numpy(float)
    source_units = frame.groupby("dataset")["biological_unit"].transform("nunique").to_numpy(float)
    weights = 1.0 / (set_sizes * unit_sets * source_units)
    return weights / weights.mean()


@dataclass
class HierarchicalModel:
    scaler: StandardScaler
    global_model: object
    residuals: dict[str, Ridge]
    kind: str

    def global_scores(self, features: np.ndarray) -> np.ndarray:
        transformed = self.scaler.transform(features)
        if self.kind == "pairwise":
            return np.asarray(self.global_model.decision_function(transformed), dtype=float)
        if self.kind == "dfl":
            weight, bias = self.global_model
            return transformed @ weight + bias
        return np.asarray(self.global_model.predict(transformed), dtype=float)

    def predict(
        self,
        features: np.ndarray,
        contexts: pd.Series,
        use_residual: bool,
    ) -> np.ndarray:
        transformed = self.scaler.transform(features)
        scores = self.global_scores(features)
        if use_residual:
            context_values = contexts.astype(str).to_numpy()
            for context, residual in self.residuals.items():
                mask = context_values == context
                if mask.any():
                    scores[mask] += residual.predict(transformed[mask])
        return scores


def _fit_residuals(
    transformed: np.ndarray,
    frame: pd.DataFrame,
    target: np.ndarray,
    global_scores: np.ndarray,
) -> dict[str, Ridge]:
    residuals: dict[str, Ridge] = {}
    context_values = frame["assay_context"].astype(str).to_numpy()
    for context in sorted(set(context_values)):
        mask = context_values == context
        if mask.sum() < 20:
            continue
        model = Ridge(alpha=100.0)
        model.fit(
            transformed[mask],
            target[mask] - global_scores[mask],
            sample_weight=source_set_weights(frame.loc[mask]),
        )
        residuals[context] = model
    return residuals


def fit_predict_then_rank(
    features: np.ndarray,
    frame: pd.DataFrame,
    sign: int,
) -> HierarchicalModel:
    scaler = StandardScaler().fit(features)
    transformed = scaler.transform(features)
    target = normalized_utility(frame, sign)
    model = Ridge(alpha=100.0)
    model.fit(transformed, target, sample_weight=source_set_weights(frame))
    global_scores = model.predict(transformed)
    residuals = _fit_residuals(transformed, frame, target, global_scores)
    return HierarchicalModel(scaler, model, residuals, "ridge")


def _pairwise_training_data(
    transformed: np.ndarray,
    frame: pd.DataFrame,
    sign: int,
    seed: int,
    maximum_pairs_per_set: int = 2_048,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    utility = normalized_utility(frame, sign)
    rows: list[np.ndarray] = []
    labels: list[int] = []
    weights: list[float] = []
    source_set_counts = frame.groupby("dataset")["decision_set_id"].nunique().to_dict()
    for decision_id, raw_indices in frame.groupby("decision_set_id", sort=True).indices.items():
        indices = np.asarray(raw_indices, dtype=int)
        if len(indices) < 2:
            continue
        pair_count = min(maximum_pairs_per_set, len(indices) * (len(indices) - 1))
        dataset = str(frame.iloc[indices[0]]["dataset"])
        ordered = indices[np.lexsort((indices, utility[indices]))]
        offset = (
            seed + int(hashlib.sha256(decision_id.encode()).hexdigest()[:8], 16)
        ) % len(ordered)
        created = 0
        cursor = 0
        while created < pair_count and cursor < len(ordered) * (len(ordered) - 1):
            left_rank = (cursor + offset) % len(ordered)
            gap = 1 + ((cursor // len(ordered)) % (len(ordered) - 1))
            right_rank = (left_rank + gap) % len(ordered)
            left, right = int(ordered[left_rank]), int(ordered[right_rank])
            cursor += 1
            if utility[left] == utility[right]:
                continue
            if (created + seed) % 2:
                left, right = right, left
            rows.append(transformed[left] - transformed[right])
            labels.append(int(utility[left] > utility[right]))
            weights.append(1.0 / (source_set_counts[dataset] * pair_count))
            created += 1
    x = np.asarray(rows, dtype=np.float32)
    y = np.asarray(labels, dtype=int)
    weight = np.asarray(weights, dtype=float)
    if set(y) != {0, 1}:
        raise ValueError("Pairwise sampling failed to produce both orientations")
    return x, y, weight / weight.mean()


def fit_pairwise(
    features: np.ndarray,
    frame: pd.DataFrame,
    sign: int,
    seed: int,
) -> HierarchicalModel:
    scaler = StandardScaler().fit(features)
    transformed = scaler.transform(features)
    x_pair, y_pair, weights = _pairwise_training_data(transformed, frame, sign, seed)
    model = LogisticRegression(C=0.1, max_iter=500, solver="liblinear", random_state=seed)
    model.fit(x_pair, y_pair, sample_weight=weights)
    global_scores = model.decision_function(transformed)
    target = normalized_utility(frame, sign)
    residuals = _fit_residuals(transformed, frame, target, global_scores)
    return HierarchicalModel(scaler, model, residuals, "pairwise")


def fit_dfl(
    features: np.ndarray,
    frame: pd.DataFrame,
    sign: int,
    seed: int,
    temperature: float = 0.25,
    l2: float = 1e-3,
    maximum_epochs: int = 75,
) -> HierarchicalModel:
    torch.manual_seed(seed)
    scaler = StandardScaler().fit(features)
    transformed = scaler.transform(features).astype(np.float32)
    x = torch.from_numpy(transformed)
    utility_numpy = normalized_utility(frame, sign).astype(np.float32)
    utility = torch.from_numpy(utility_numpy)
    linear = torch.nn.Linear(transformed.shape[1], 1)
    optimizer = torch.optim.Adam(linear.parameters(), lr=1e-3)
    set_indices = [
        torch.as_tensor(np.asarray(indices, dtype=int))
        for _, indices in frame.groupby("decision_set_id", sort=True).indices.items()
    ]
    set_sources = [str(frame.iloc[int(indices[0])]["dataset"]) for indices in set_indices]
    source_counts = pd.Series(set_sources).value_counts().to_dict()
    best = math.inf
    best_state: dict[str, torch.Tensor] | None = None
    stale = 0
    for _ in range(maximum_epochs):
        optimizer.zero_grad()
        scores = linear(x).squeeze(1)
        losses = []
        loss_weights = []
        for indices, source in zip(set_indices, set_sources):
            probabilities = torch.softmax(scores[indices] / temperature, dim=0)
            losses.append(1.0 - torch.sum(probabilities * utility[indices]))
            loss_weights.append(1.0 / source_counts[source])
        weights = torch.as_tensor(loss_weights, dtype=torch.float32)
        decision_loss = torch.sum(torch.stack(losses) * weights) / weights.sum()
        penalty = sum(torch.sum(parameter * parameter) for parameter in linear.parameters())
        loss = decision_loss + l2 * penalty
        loss.backward()
        torch.nn.utils.clip_grad_norm_(linear.parameters(), 5.0)
        optimizer.step()
        observed = float(loss.detach())
        if observed < best - 1e-6:
            best = observed
            best_state = {
                name: value.detach().clone() for name, value in linear.state_dict().items()
            }
            stale = 0
        else:
            stale += 1
        if stale >= 10:
            break
    if best_state is None:
        raise ValueError("DFL optimization did not produce a finite training state")
    linear.load_state_dict(best_state)
    weight = linear.weight.detach().numpy()[0].astype(float)
    bias = float(linear.bias.detach().numpy()[0])
    global_scores = transformed @ weight + bias
    residuals = _fit_residuals(transformed, frame, utility_numpy, global_scores)
    return HierarchicalModel(scaler, (weight, bias), residuals, "dfl")


def decision_set_metrics(
    frame: pd.DataFrame,
    score: np.ndarray,
    model_name: str,
    direction: str,
    seed: int,
    evaluation: str,
) -> pd.DataFrame:
    work = frame.copy()
    work["score"] = score
    sign = 1 if direction == "increase" else -1
    records = []
    for decision_id, group in work.groupby("decision_set_id", sort=True):
        utility = group["localization_effect"].to_numpy(float) * sign
        predicted = group["score"].to_numpy(float)
        order = np.lexsort((group["candidate_id"].astype(str).to_numpy(), -predicted))
        best = float(utility.max())
        worst = float(utility.min())
        scale = best - worst
        if scale <= 0:
            continue
        regrets = (best - utility) / scale
        selected = int(order[0])
        ranks = rankdata(-utility, method="average")
        rank_percentile = 1.0 - (ranks[selected] - 1.0) / (len(group) - 1.0)
        good = regrets <= GOOD_REGRET
        good_count = int(good.sum())
        random_good = {}
        for k in (1, 3, 5):
            k_eff = min(k, len(group))
            random_good[k] = 1.0 - (
                math.comb(len(group) - good_count, k_eff) / math.comb(len(group), k_eff)
                if len(group) - good_count >= k_eff
                else 0.0
            )
        records.append(
            {
                "model": model_name,
                "seed": seed,
                "evaluation": evaluation,
                "dataset": group["dataset"].iloc[0],
                "decision_set_id": decision_id,
                "biological_unit": group["biological_unit"].iloc[0],
                "requested_direction": direction,
                "candidate_count": len(group),
                "directional_rank_percentile": float(rank_percentile),
                "normalized_regret": float(regrets[selected]),
                "selected_normalized_utility": float(1.0 - regrets[selected]),
                "selected_experimental_utility": float(utility[selected]),
                "good_selection_at_1": float(good[order[:1]].any()),
                "good_selection_at_3": float(good[order[: min(3, len(group))]].any()),
                "good_selection_at_5": float(good[order[: min(5, len(group))]].any()),
                "oracle_recovered": float(regrets[selected] == 0),
                "random_expected_regret": float(regrets.mean()),
                "random_good_selection_at_1": random_good[1],
                "random_good_selection_at_3": random_good[3],
                "random_good_selection_at_5": random_good[5],
                "spearman": float(spearmanr(predicted, utility).statistic)
                if np.unique(predicted).size > 1 and np.unique(utility).size > 1
                else np.nan,
            }
        )
    return pd.DataFrame(records)
