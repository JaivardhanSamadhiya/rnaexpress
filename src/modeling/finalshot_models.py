"""Frozen model components for the RNAddress FinalShot evaluation.

This module contains only outcome-agnostic feature assembly and the prespecified
sparse-group linear solver.  Evaluation orchestration lives in
``src.analysis.run_finalshot_models`` so that folds and protected-data guards
remain explicit at the point where outcomes are read.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import torch

from src.modeling.v4_decision_models import geometry_features


RIDGE_FLOOR = 1e-5
MAXIMUM_ITERATIONS = 500
OBJECTIVE_TOLERANCE = 1e-6


@dataclass(frozen=True)
class FeatureLayout:
    """Column layout for one materialized FinalShot design matrix."""

    geometry: slice
    rbp_groups: tuple[slice, ...]
    group_names: tuple[str, ...]
    base_columns: tuple[np.ndarray, ...]
    interaction_columns: tuple[np.ndarray, ...]

    @property
    def feature_count(self) -> int:
        return self.rbp_groups[-1].stop if self.rbp_groups else self.geometry.stop


class FinalShotFeatureStore:
    """Memory-mapped RBP signatures with deterministic context interactions.

    M2 columns are laid out by RBP group (nine base summaries followed by the
    same nine summaries times the expression proxy when the group is eligible).
    This differs only in column order from the protocol's conceptual block
    notation and makes the group proximal operator contiguous and auditable.
    """

    def __init__(
        self,
        rows: pd.DataFrame,
        rbp_matrix_path: str | Path,
        dictionary_path: str | Path,
        expression_path: str | Path,
    ) -> None:
        self.rows = rows.reset_index(drop=True)
        self.geometry = geometry_features(self.rows, categories=True)
        self.feature_rows = self.rows["feature_row"].to_numpy(dtype=np.int64)
        self.rbp = np.load(Path(rbp_matrix_path), mmap_mode="r")
        dictionary = pd.read_csv(dictionary_path).sort_values("column_index")
        if self.rbp.shape[1] != 927 or len(dictionary) != 927:
            raise ValueError("FinalShot requires exactly 927 frozen RBP features")
        if not np.array_equal(dictionary["column_index"].to_numpy(), np.arange(927)):
            raise ValueError("RBP feature dictionary is not in canonical order")
        grouped = dictionary.groupby("group_index", sort=True)
        if len(grouped) != 103 or not np.all(grouped.size().to_numpy() == 9):
            raise ValueError("RBP dictionary must contain 103 nine-summary groups")
        self.group_names = tuple(group["human_rbp"].iloc[0] for _, group in grouped)

        expression = pd.read_csv(expression_path)
        expression = expression.drop_duplicates(["human_rbp", "cell_line"])
        lookup = expression.set_index(["human_rbp", "cell_line"])
        eligible = []
        context = np.zeros((len(self.rows), 103), dtype=np.float32)
        cell = self.rows["cell_type"].replace({"Neuro-2a": "N2A"}).astype(str).to_numpy()
        if not set(cell).issubset({"CAD", "N2A"}):
            raise ValueError(f"Unsupported FinalShot cell types: {sorted(set(cell))}")
        for group_index, rbp_name in enumerate(self.group_names):
            records = []
            is_eligible = True
            for state in ("CAD", "N2A"):
                key = (rbp_name, state)
                if key not in lookup.index or not bool(lookup.loc[key, "context_eligible"]):
                    is_eligible = False
                    break
                records.append(float(lookup.loc[key, "compartment_balanced_expression_proxy"]))
            eligible.append(is_eligible)
            if is_eligible:
                context[:, group_index] = np.where(cell == "CAD", records[0], records[1])
        self.context = context
        self.context_eligible = np.asarray(eligible, dtype=bool)
        if int(self.context_eligible.sum()) != 98:
            raise ValueError("FinalShot requires exactly 98 context-eligible RBP groups")

    def layout(self, family: str) -> FeatureLayout:
        if family not in {"M0", "M1", "M2"}:
            raise ValueError(f"Unsupported direct model family: {family}")
        geometry_count = self.geometry.shape[1]
        if family == "M0":
            return FeatureLayout(slice(0, geometry_count), (), (), (), ())
        cursor = geometry_count
        groups: list[slice] = []
        bases: list[np.ndarray] = []
        interactions: list[np.ndarray] = []
        for group_index in range(103):
            base = np.arange(cursor, cursor + 9, dtype=np.int32)
            cursor += 9
            interaction = np.empty(0, dtype=np.int32)
            if family == "M2" and self.context_eligible[group_index]:
                interaction = np.arange(cursor, cursor + 9, dtype=np.int32)
                cursor += 9
            groups.append(slice(int(base[0]), cursor))
            bases.append(base)
            interactions.append(interaction)
        return FeatureLayout(
            geometry=slice(0, geometry_count),
            rbp_groups=tuple(groups),
            group_names=self.group_names,
            base_columns=tuple(bases),
            interaction_columns=tuple(interactions),
        )

    def materialize(self, indices: np.ndarray, family: str) -> tuple[np.ndarray, FeatureLayout]:
        indices = np.asarray(indices, dtype=np.int64)
        layout = self.layout(family)
        output = np.empty((len(indices), layout.feature_count), dtype=np.float32)
        output[:, layout.geometry] = self.geometry[indices]
        if family == "M0":
            return output, layout
        selected = np.asarray(self.rbp[self.feature_rows[indices]], dtype=np.float32)
        for group_index, destination in enumerate(layout.rbp_groups):
            source = selected[:, group_index * 9 : (group_index + 1) * 9]
            output[:, layout.base_columns[group_index]] = source
            interaction = layout.interaction_columns[group_index]
            if len(interaction):
                output[:, interaction] = source * self.context[indices, group_index, None]
        if not np.isfinite(output).all():
            raise ValueError("FinalShot design matrix contains non-finite values")
        return output, layout


@dataclass(frozen=True)
class FoldScaler:
    mean: np.ndarray
    scale: np.ndarray

    @classmethod
    def fit(cls, features: np.ndarray) -> "FoldScaler":
        mean = features.mean(axis=0, dtype=np.float64)
        variance = features.var(axis=0, dtype=np.float64)
        scale = np.sqrt(variance)
        scale[scale == 0] = 1.0
        return cls(mean=mean, scale=scale)

    def transform(self, features: np.ndarray) -> np.ndarray:
        return np.asarray((features - self.mean) / self.scale, dtype=np.float32)


@dataclass
class SparseGroupModel:
    scaler: FoldScaler
    coefficient: np.ndarray
    intercept: float
    penalty: float
    group_fraction: float
    converged: bool
    iterations: int
    objective: float
    lipschitz: float
    group_names: tuple[str, ...]
    group_norms: np.ndarray

    def predict(self, features: np.ndarray) -> np.ndarray:
        return self.scaler.transform(features) @ self.coefficient + self.intercept


def finalshot_assay_heads(frame: pd.DataFrame) -> tuple[np.ndarray, tuple[str, ...]]:
    """Map the certified rows to the five frozen M3 measurement heads."""
    labels = []
    for row in frame[["dataset", "cell_type", "reporter"]].itertuples(index=False):
        if row.dataset == "mikl_gse173098" and row.cell_type == "CAD":
            labels.append("Mikl-CAD")
        elif row.dataset == "mikl_gse173098" and row.cell_type == "Neuro-2a":
            labels.append("Mikl-N2A")
        elif row.dataset == "tdp43_gse288185" and row.cell_type == "CAD":
            labels.append("TDP-CAD")
        elif row.dataset == "moffatt_gse334718" and row.cell_type == "CAD" and row.reporter == "GFP":
            labels.append("Moffatt-GFP-CAD")
        elif row.dataset == "moffatt_gse334718" and row.cell_type == "CAD" and row.reporter == "Firefly":
            labels.append("Moffatt-Firefly-CAD")
        else:
            raise ValueError(f"Row has no frozen M3 assay head: {row}")
    names = ("Mikl-CAD", "Mikl-N2A", "TDP-CAD", "Moffatt-GFP-CAD", "Moffatt-Firefly-CAD")
    lookup = {name: index for index, name in enumerate(names)}
    return np.asarray([lookup[label] for label in labels], dtype=np.int64), names


@dataclass
class LatentHeadModel:
    scaler: FoldScaler
    coefficient: np.ndarray
    latent_intercept: float
    head_intercepts: np.ndarray
    head_slopes: np.ndarray
    knots: np.ndarray
    head_form: str
    head_names: tuple[str, ...]
    penalty: float
    group_fraction: float
    seed: int
    epochs: int
    best_objective: float
    stopped_early: bool
    group_names: tuple[str, ...]
    group_norms: np.ndarray

    def latent_score(self, features: np.ndarray) -> np.ndarray:
        return self.scaler.transform(features) @ self.coefficient + self.latent_intercept

    def calibrated_prediction(self, features: np.ndarray, heads: np.ndarray) -> np.ndarray:
        phi = self.latent_score(features)
        result = self.head_intercepts[np.asarray(heads, dtype=int)].copy()
        slopes = self.head_slopes[np.asarray(heads, dtype=int)]
        result += slopes[:, 0] * phi
        if self.head_form == "two_knot":
            result += slopes[:, 1] * np.maximum(phi - self.knots[0], 0.0)
            result += slopes[:, 2] * np.maximum(phi - self.knots[1], 0.0)
        return result


def _penalty_value(
    coefficient: np.ndarray,
    groups: Iterable[slice],
    penalty: float,
    group_fraction: float,
) -> float:
    value = 0.0
    for group in groups:
        block = coefficient[group]
        value += (1.0 - group_fraction) * np.abs(block).sum()
        value += group_fraction * np.sqrt(len(block)) * np.linalg.norm(block)
    return float(penalty * value)


def _prox_sparse_group(
    values: np.ndarray,
    groups: Iterable[slice],
    step: float,
    penalty: float,
    group_fraction: float,
) -> np.ndarray:
    output = values.copy()
    l1 = step * penalty * (1.0 - group_fraction)
    for group in groups:
        block = output[group]
        block = np.sign(block) * np.maximum(np.abs(block) - l1, 0.0)
        norm = float(np.linalg.norm(block))
        group_threshold = step * penalty * group_fraction * np.sqrt(len(block))
        if norm <= group_threshold:
            block.fill(0.0)
        else:
            block *= 1.0 - group_threshold / norm
        output[group] = block
    return output


def _smooth_objective(
    features: np.ndarray,
    target: np.ndarray,
    weights: np.ndarray,
    coefficient: np.ndarray,
    ridge_floor: float,
) -> tuple[float, np.ndarray]:
    residual = features @ coefficient - target
    value = 0.5 * float(np.dot(weights, residual * residual)) / float(weights.sum())
    value += 0.5 * ridge_floor * float(np.dot(coefficient, coefficient))
    return value, residual


def _lipschitz_power(
    features: np.ndarray,
    weights: np.ndarray,
    ridge_floor: float,
    iterations: int = 24,
) -> float:
    vector = np.full(features.shape[1], 1.0 / np.sqrt(features.shape[1]), dtype=np.float32)
    total = float(weights.sum())
    estimate = 0.0
    for _ in range(iterations):
        product = features.T @ (weights * (features @ vector)) / total + ridge_floor * vector
        norm = float(np.linalg.norm(product))
        if not np.isfinite(norm) or norm <= 0:
            raise FloatingPointError("Could not estimate sparse-group Lipschitz constant")
        vector = np.asarray(product / norm, dtype=np.float32)
        estimate = float(vector @ (features.T @ (weights * (features @ vector)) / total)) + ridge_floor
    return max(estimate * 1.05, ridge_floor)


def fit_sparse_group(
    features: np.ndarray,
    target: np.ndarray,
    weights: np.ndarray,
    layout: FeatureLayout,
    penalty: float,
    group_fraction: float,
    *,
    ridge_floor: float = RIDGE_FLOOR,
    maximum_iterations: int = MAXIMUM_ITERATIONS,
    tolerance: float = OBJECTIVE_TOLERANCE,
) -> SparseGroupModel:
    """Fit the frozen weighted sparse-group objective by monotone FISTA.

    The exact objective is

    ``0.5 * weighted_mean((y-Xb)^2) + ridge_floor/2*||b||^2 +``
    ``lambda*((1-eta)*||b_RBP||_1 + eta*sum_g sqrt(p_g)||b_g||_2)``.

    Geometry is excluded from the sparse penalties but receives the frozen
    ridge floor.  The intercept is unpenalized.  Initialization is exactly zero.
    """
    if penalty not in {0.001, 0.01, 0.1} or group_fraction not in {0.25, 0.75}:
        raise ValueError("Sparse-group hyperparameter is outside the frozen grid")
    if features.ndim != 2 or len(features) != len(target) or len(target) != len(weights):
        raise ValueError("Sparse-group inputs are not aligned")
    if np.any(weights <= 0) or not np.isfinite(features).all() or not np.isfinite(target).all():
        raise ValueError("Sparse-group inputs must be finite with positive weights")

    scaler = FoldScaler.fit(features)
    transformed = scaler.transform(features)
    total_weight = float(weights.sum())
    weighted_x_mean = np.sum(transformed * weights[:, None], axis=0) / total_weight
    weighted_y_mean = float(np.dot(weights, target) / total_weight)
    transformed -= weighted_x_mean.astype(np.float32)
    centered_target = np.asarray(target - weighted_y_mean, dtype=np.float32)
    weights32 = np.asarray(weights, dtype=np.float32)

    lipschitz = _lipschitz_power(transformed, weights32, ridge_floor)
    coefficient = np.zeros(transformed.shape[1], dtype=np.float32)
    accelerated = coefficient.copy()
    momentum = 1.0
    previous_objective = np.inf
    converged = False
    objective = np.inf
    for iteration in range(1, maximum_iterations + 1):
        smooth_at_accelerated, residual = _smooth_objective(
            transformed, centered_target, weights32, accelerated, ridge_floor
        )
        gradient = transformed.T @ (weights32 * residual) / total_weight
        gradient += ridge_floor * accelerated

        # Backtracking makes the finite power estimate safe while preserving a
        # deterministic fixed update once a valid local majorizer is found.
        while True:
            candidate = _prox_sparse_group(
                accelerated - gradient / lipschitz,
                layout.rbp_groups,
                1.0 / lipschitz,
                penalty,
                group_fraction,
            )
            smooth_candidate, _ = _smooth_objective(
                transformed, centered_target, weights32, candidate, ridge_floor
            )
            difference = candidate - accelerated
            majorizer = (
                smooth_at_accelerated
                + float(np.dot(gradient, difference))
                + 0.5 * lipschitz * float(np.dot(difference, difference))
            )
            if smooth_candidate <= majorizer + 1e-9:
                break
            lipschitz *= 2.0

        objective = smooth_candidate + _penalty_value(
            candidate, layout.rbp_groups, penalty, group_fraction
        )
        relative = abs(previous_objective - objective) / max(1.0, abs(previous_objective))
        if np.isfinite(previous_objective) and objective > previous_objective + 1e-10:
            # Monotone restart; this avoids declaring convergence on an
            # acceleration oscillation and remains a standard FISTA update.
            accelerated = coefficient.copy()
            momentum = 1.0
            previous_objective = np.inf
            continue
        if np.isfinite(previous_objective) and relative <= tolerance:
            coefficient = candidate
            converged = True
            break
        next_momentum = 0.5 * (1.0 + np.sqrt(1.0 + 4.0 * momentum * momentum))
        accelerated = candidate + ((momentum - 1.0) / next_momentum) * (candidate - coefficient)
        coefficient = candidate
        momentum = next_momentum
        previous_objective = objective

    intercept = weighted_y_mean - float(weighted_x_mean @ coefficient)
    norms = np.asarray([np.linalg.norm(coefficient[group]) for group in layout.rbp_groups])
    return SparseGroupModel(
        scaler=scaler,
        coefficient=coefficient,
        intercept=intercept,
        penalty=float(penalty),
        group_fraction=float(group_fraction),
        converged=converged,
        iterations=iteration,
        objective=float(objective),
        lipschitz=float(lipschitz),
        group_names=layout.group_names,
        group_norms=norms,
    )


def _torch_sparse_penalty(
    coefficient: torch.Tensor,
    groups: Iterable[slice],
    penalty: float,
    group_fraction: float,
) -> torch.Tensor:
    blocks = [coefficient[group] for group in groups]
    l1 = torch.sum(torch.abs(torch.cat(blocks))) if blocks else coefficient.new_zeros(())
    grouped = sum(np.sqrt(block.stop - block.start) * torch.linalg.vector_norm(value)
                  for block, value in zip(groups, blocks))
    return penalty * ((1.0 - group_fraction) * l1 + group_fraction * grouped)


def fit_latent_heads(
    features: np.ndarray,
    raw_target: np.ndarray,
    weights: np.ndarray,
    heads: np.ndarray,
    head_names: tuple[str, ...],
    layout: FeatureLayout,
    penalty: float,
    group_fraction: float,
    head_form: str,
    seed: int,
    *,
    ridge_floor: float = RIDGE_FLOOR,
    learning_rate: float = 1e-3,
    batch_size: int = 2_048,
    maximum_epochs: int = 100,
    patience: int = 10,
) -> LatentHeadModel:
    """Fit frozen M3 with a shared latent score and monotone assay heads.

    Latent scores are centered and unit-scaled on each optimization minibatch.
    The final archived coefficient is exactly centered/unit-scaled on all
    training rows.  Applying the sparse penalty to that scale-normalized
    coefficient removes the otherwise degenerate coefficient/head rescaling.
    """
    if penalty not in {0.001, 0.01, 0.1} or group_fraction not in {0.25, 0.75}:
        raise ValueError("M3 hyperparameter is outside the frozen grid")
    if head_form not in {"affine", "two_knot"}:
        raise ValueError("M3 head form must be affine or two_knot")
    if seed not in {17, 41, 89}:
        raise ValueError("M3 seed is outside the frozen seed set")
    if not (len(features) == len(raw_target) == len(weights) == len(heads)):
        raise ValueError("M3 inputs are not aligned")
    if np.any(weights <= 0) or np.min(heads) < 0 or np.max(heads) >= len(head_names):
        raise ValueError("M3 weights or head indices are invalid")

    scaler = FoldScaler.fit(features)
    transformed = scaler.transform(features)
    x = torch.from_numpy(transformed)
    y = torch.as_tensor(raw_target, dtype=torch.float32)
    weight = torch.as_tensor(weights, dtype=torch.float32)
    head_index = torch.as_tensor(heads, dtype=torch.long)
    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed)
    torch.manual_seed(seed)

    coefficient = torch.nn.Parameter(torch.randn(features.shape[1], generator=generator) * 0.01)
    intercept_initial = np.zeros(len(head_names), dtype=np.float32)
    for index in range(len(head_names)):
        mask = heads == index
        if mask.any():
            intercept_initial[index] = np.average(raw_target[mask], weights=weights[mask])
    head_intercept = torch.nn.Parameter(torch.from_numpy(intercept_initial))
    slope_count = 1 if head_form == "affine" else 3
    # softplus(-2) ~= 0.127: positive but deliberately low-gain initialization.
    slope_raw = torch.nn.Parameter(torch.full((len(head_names), slope_count), -2.0))
    optimizer = torch.optim.Adam([coefficient, head_intercept, slope_raw], lr=learning_rate)

    best_objective = np.inf
    best_state: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray] | None = None
    stale = 0
    stopped_early = False
    for epoch in range(1, maximum_epochs + 1):
        order = torch.randperm(len(x), generator=generator)
        for start in range(0, len(x), batch_size):
            batch = order[start : start + batch_size]
            xb = x[batch]
            phi_raw = xb @ coefficient
            phi_mean = torch.mean(phi_raw)
            phi_scale = torch.sqrt(torch.mean((phi_raw - phi_mean) ** 2) + 1e-12)
            phi = (phi_raw - phi_mean) / phi_scale
            effective_coefficient = coefficient / phi_scale
            batch_heads = head_index[batch]
            slopes = torch.nn.functional.softplus(slope_raw)[batch_heads]
            prediction = head_intercept[batch_heads] + slopes[:, 0] * phi
            knots = torch.quantile(phi.detach(), torch.tensor([1.0 / 3.0, 2.0 / 3.0]))
            if head_form == "two_knot":
                prediction = prediction + slopes[:, 1] * torch.relu(phi - knots[0])
                prediction = prediction + slopes[:, 2] * torch.relu(phi - knots[1])
            batch_weight = weight[batch]
            mse = 0.5 * torch.sum(batch_weight * (prediction - y[batch]) ** 2) / batch_weight.sum()
            sparse = _torch_sparse_penalty(
                effective_coefficient, layout.rbp_groups, penalty, group_fraction
            )
            ridge = 0.5 * ridge_floor * torch.sum(effective_coefficient ** 2)
            loss = mse + sparse + ridge
            if not torch.isfinite(loss):
                raise FloatingPointError("M3 optimization produced a non-finite loss")
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_([coefficient, head_intercept, slope_raw], 5.0)
            optimizer.step()

        with torch.no_grad():
            phi_raw = x @ coefficient
            phi_mean = torch.mean(phi_raw)
            phi_scale = torch.sqrt(torch.mean((phi_raw - phi_mean) ** 2) + 1e-12)
            phi = (phi_raw - phi_mean) / phi_scale
            effective_coefficient = coefficient / phi_scale
            knots = torch.quantile(phi, torch.tensor([1.0 / 3.0, 2.0 / 3.0]))
            slopes = torch.nn.functional.softplus(slope_raw)[head_index]
            prediction = head_intercept[head_index] + slopes[:, 0] * phi
            if head_form == "two_knot":
                prediction = prediction + slopes[:, 1] * torch.relu(phi - knots[0])
                prediction = prediction + slopes[:, 2] * torch.relu(phi - knots[1])
            objective_tensor = (
                0.5 * torch.sum(weight * (prediction - y) ** 2) / weight.sum()
                + _torch_sparse_penalty(effective_coefficient, layout.rbp_groups, penalty, group_fraction)
                + 0.5 * ridge_floor * torch.sum(effective_coefficient ** 2)
            )
            objective = float(objective_tensor)
            if objective < best_objective - 1e-8:
                best_objective = objective
                best_state = (
                    effective_coefficient.detach().numpy().copy(),
                    np.asarray(float(-phi_mean / phi_scale), dtype=np.float32),
                    head_intercept.detach().numpy().copy(),
                    slope_raw.detach().numpy().copy(),
                )
                stale = 0
            else:
                stale += 1
            if stale >= patience:
                stopped_early = True
                break

    if best_state is None or not np.isfinite(best_objective):
        raise RuntimeError("M3 did not produce a finite training state")
    effective, latent_intercept, fitted_intercepts, fitted_slope_raw = best_state
    with torch.no_grad():
        slope_values = torch.nn.functional.softplus(torch.from_numpy(fitted_slope_raw)).numpy()
    final_phi = transformed @ effective + float(latent_intercept)
    final_knots = np.quantile(final_phi, [1.0 / 3.0, 2.0 / 3.0]).astype(np.float32)
    norms = np.asarray([np.linalg.norm(effective[group]) for group in layout.rbp_groups])
    return LatentHeadModel(
        scaler=scaler,
        coefficient=np.asarray(effective, dtype=np.float32),
        latent_intercept=float(latent_intercept),
        head_intercepts=np.asarray(fitted_intercepts, dtype=np.float32),
        head_slopes=np.asarray(slope_values, dtype=np.float32),
        knots=final_knots,
        head_form=head_form,
        head_names=head_names,
        penalty=float(penalty),
        group_fraction=float(group_fraction),
        seed=int(seed),
        epochs=int(epoch),
        best_objective=float(best_objective),
        stopped_early=stopped_early,
        group_names=layout.group_names,
        group_norms=norms,
    )
