"""Exact ordered motif deltas and a sparse pairwise utility ranker.

Feature construction accepts sequences only. It never accepts localization
outcomes, source identifiers, gene identifiers, or model scores. The 4--6-mer
block contains exact overlapping mutant-minus-parent counts; it is distinct
from the existing 1--3-mer and parent composition interaction representation.
All fitting is invoked by the shared, frozen experiment runner.
"""

from __future__ import annotations

from collections import Counter
import hashlib
import itertools
from typing import Iterable, Sequence

from src.research_20260921 import common as _runtime
import numpy as np
from scipy import sparse
from scipy.optimize import minimize
from scipy.special import expit

K_VALUES = (4, 5, 6)
ALPHABET = "ACGT"
CONFIGS = [
    {"id": "ordered_456_l2_0.005", "penalty": .005},
    {"id": "ordered_456_l2_0.05", "penalty": .05},
    {"id": "ordered_456_l2_0.5", "penalty": .5},
]
WORDS = tuple(
    "".join(word)
    for length in K_VALUES
    for word in itertools.product(ALPHABET, repeat=length)
)
WORD_INDEX = {word: index for index, word in enumerate(WORDS)}


def normalize(sequence: str) -> str:
    value = str(sequence).upper().replace("U", "T")
    if not value or set(value) - set(ALPHABET):
        raise ValueError("Only nonempty exact A/C/G/T RNA sequences are supported")
    return value


def delta_counts(parent: str, mutant: str) -> dict[int, int]:
    """Count only affected starts, exactly equivalent to full-sequence deltas."""
    parent, mutant = normalize(parent), normalize(mutant)
    if len(parent) != len(mutant):
        raise ValueError("Ordered motif deltas require aligned substitutions")
    positions = [i for i, (a, b) in enumerate(zip(parent, mutant)) if a != b]
    result: Counter[int] = Counter()
    for length in K_VALUES:
        starts = {
            start
            for position in positions
            for start in range(max(0, position - length + 1), min(position, len(parent) - length) + 1)
        }
        for start in sorted(starts):
            reference = parent[start : start + length]
            edited = mutant[start : start + length]
            if reference != edited:
                result[WORD_INDEX[edited]] += 1
                result[WORD_INDEX[reference]] -= 1
    return {index: count for index, count in result.items() if count}


def build_ordered_deltas(parents: Sequence[str], mutants: Sequence[str]) -> sparse.csr_matrix:
    """Return n x 5,376 sparse integer deltas in the fixed lexical schema."""
    if len(parents) != len(mutants):
        raise ValueError("Parent and mutant row counts differ")
    indices, values, indptr = [], [], [0]
    for parent, mutant in zip(parents, mutants):
        counts = delta_counts(parent, mutant)
        for index in sorted(counts):
            indices.append(index)
            values.append(counts[index])
        indptr.append(len(indices))
    return sparse.csr_matrix(
        (np.asarray(values, dtype=np.float64), np.asarray(indices, dtype=np.int32), np.asarray(indptr, dtype=np.int32)),
        shape=(len(parents), len(WORDS)),
    )


def feature_schema() -> dict:
    return {
        "feature_family": "exact_ordered_mutant_minus_parent_motif_counts",
        "columns": ["delta_" + word for word in WORDS],
        "k_values": list(K_VALUES),
        "columns_count": len(WORDS),
        "count_convention": "all overlapping starts; affected-start evaluation is exact",
        "input_constraint": "equal-length aligned substitutions with exact A/C/G/T",
        "outcome_inputs": False,
        "absolute_parent_features": False,
        "missing_feature_fill": False,
    }


def pair_sequence_hash(parents: Iterable[str], mutants: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for parent, mutant in zip(parents, mutants):
        digest.update((normalize(parent) + ">" + normalize(mutant) + "\n").encode("ascii"))
    return digest.hexdigest()


def combine_with_baseline(baseline: np.ndarray, ordered: sparse.csr_matrix) -> sparse.csr_matrix:
    baseline = np.asarray(baseline, dtype=np.float64)
    if baseline.ndim != 2 or baseline.shape[0] != ordered.shape[0] or not np.isfinite(baseline).all():
        raise ValueError("Baseline feature block is not row-aligned and finite")
    return sparse.hstack((sparse.csr_matrix(baseline), ordered), format="csr")


def build_features(frame, base246: np.ndarray) -> sparse.csr_matrix:
    """Shared runner feature API; only the two sequence columns are read."""
    base246 = np.asarray(base246)
    if base246.shape != (len(frame), 246):
        raise ValueError("The matched baseline must have exactly 246 columns")
    return combine_with_baseline(
        base246,
        build_ordered_deltas(frame.parent_sequence.tolist(), frame.mutant_sequence.tolist()),
    )


def pair_objective(beta: np.ndarray, differences: sparse.csr_matrix, labels: np.ndarray, weights: np.ndarray, penalty: float):
    score = np.asarray(differences @ beta).ravel()
    margins = labels * score
    loss = float(weights @ np.logaddexp(0, -margins) + penalty * (beta @ beta) / 2)
    residual = -weights * labels * expit(-margins)
    gradient = np.asarray(differences.T @ residual).ravel() + penalty * beta
    return loss, gradient


def fit_pairwise(features, left, right, labels, weights, penalty: float = .05) -> dict:
    """Fit one convex utility model; every supplied pair must be training-only.

    Scaling uses weighted RMS candidate differences, with no centering. Parent
    constants therefore cannot inflate the regularizer. Unsupported columns
    are recorded, left at scale one, and have exactly zero fitted coefficient.
    """
    matrix = sparse.csr_matrix(features, dtype=np.float64)
    left, right = np.asarray(left, dtype=int), np.asarray(right, dtype=int)
    labels, weights = np.asarray(labels, dtype=float), np.asarray(weights, dtype=float)
    if not (len(left) == len(right) == len(labels) == len(weights)) or not len(labels):
        raise ValueError("Training preference arrays are empty or inconsistent")
    if set(np.unique(labels)) - {-1., 1.}:
        raise ValueError("Training labels must be historical non-tie signed preferences")
    if not np.isfinite(matrix.data).all() or not np.isfinite(weights).all() or np.any(weights < 0) or weights.sum() <= 0:
        raise ValueError("Invalid training features or loss weights")
    if not np.isfinite(penalty) or penalty <= 0:
        raise ValueError("Positive finite L2 penalty is required")
    weights = weights / weights.sum()
    differences = matrix[left] - matrix[right]
    scale = np.sqrt(np.asarray(differences.power(2).T @ weights).ravel())
    active = scale >= 1e-8
    scale[~active] = 1.
    scaled = differences.multiply(1 / scale).tocsr()
    result = minimize(
        pair_objective,
        np.zeros(matrix.shape[1]),
        args=(scaled, labels, weights, float(penalty)),
        jac=True,
        method="L-BFGS-B",
        options={"maxiter": 500, "ftol": 1e-11, "gtol": 1e-7},
    )
    if not result.success:
        raise RuntimeError(str(result.message))
    if np.any(result.x[~active] != 0):
        raise AssertionError("Unsupported training features received nonzero coefficients")
    return {
        "kind": "sparse_linear_bradley_terry",
        "beta": result.x.tolist(),
        "pair_scale": scale.tolist(),
        "active_columns": np.flatnonzero(active).tolist(),
        "unsupported_columns": np.flatnonzero(~active).tolist(),
        "penalty": float(penalty),
        "objective": float(result.fun),
        "iterations": int(result.nit),
        "training_pairs": len(labels),
        "feature_columns": matrix.shape[1],
        "scaling": "training-only hierarchically weighted pair RMS; no intercept or centering",
    }


def predict_pairwise(model: dict, features) -> np.ndarray:
    matrix = sparse.csr_matrix(features, dtype=np.float64)
    scale, beta = np.asarray(model["pair_scale"]), np.asarray(model["beta"])
    if matrix.shape[1] != len(beta) or scale.shape != beta.shape:
        raise ValueError("Model and feature schema dimensions differ")
    return np.asarray(matrix @ (beta / scale)).ravel()


def fit_model(frame, features, config: dict) -> dict:
    """Shared runner fit API; historical pair sampling and source weights."""
    from src.cross_assay_20260927.models import pair_indices

    frame = frame.reset_index(drop=True)
    if len(frame) != features.shape[0] or features.shape[1] != 5622:
        raise ValueError("Training frame and ordered motif feature rows differ")
    if config not in CONFIGS:
        raise ValueError("The representation config is outside the fixed grid")
    left, right, labels, weights, _ = pair_indices(frame)
    model = fit_pairwise(features, left, right, labels, weights, penalty=config['penalty'])
    model.update({
        'config': dict(config),
        'training_studies': sorted(frame.dataset.unique()),
        'training_components': sorted(frame.biological_component.unique()),
        'training_rows': len(frame),
        'training_ids_sha256': hashlib.sha256('|'.join(frame.intervention_id).encode()).hexdigest(),
        'pair_roster_sha256': hashlib.sha256(left.tobytes() + right.tobytes() + labels.tobytes() + weights.tobytes()).hexdigest(),
        'feature_schema': 'base246_plus_exact_delta_456_5376',
    })
    return model


def predict_model(model: dict, features) -> np.ndarray:
    return predict_pairwise(model, features)
