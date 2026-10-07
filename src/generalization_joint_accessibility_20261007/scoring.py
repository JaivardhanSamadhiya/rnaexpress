"""Whole-site opening is a specificity modulation hypothesis, not occupancy."""
from .common import np
from .feasibility import normalize
from src.generalization_rbp_20261007.scoring import scan, FEATURE_POOLS
from src.generalization_rbp_20261007.projection import WIDTH, generate

PLAN = {
    'version': 'global_joint_opening_pfm_v1', 'motifs': 421, 'interval_widths': [4, 25],
    'score': 'Exact historical specificity proxy multiplied by global ensemble probability that every nucleotide of the complete motif interval is unpaired',
    'pools': list(FEATURE_POOLS), 'affected_pool': 'Union of corresponding complete motif windows overlapping any actual changed nucleotide',
    'empty_pool': 0., 'projection': 'Four original independent421x64 float32 Gaussian matrices; summarize float64 BEFORE projection; delta castfloat32 only after subtraction',
    'clip_probability': False, 'rounding_bound': 1e-10,
    'inputs': 'Exact frozen encoded alleles, SRLE46nt HBB-vector junction; no guessed flanks',
    'occupancy_or_cell_binding': False, 'outcome_use_for_features': False,
}

def pooled_blocks(blocks, length, positions, probability, width=WIDTH):
    positions = np.asarray(positions, dtype=int)
    assert positions.ndim == 1 and np.all((positions >= 0) & (positions < length))
    probability = np.asarray(probability, dtype=float)
    assert probability.ndim == 2 and probability.shape[0] == length
    result = np.zeros((width, 4), dtype=np.float64)
    for window, indices, values in blocks:
        count = values.shape[1]
        assert count == max(0, length - window + 1) and values.shape[0] == len(indices)
        if not count:
            continue
        weights = probability[:count, window]
        assert np.isfinite(weights).all() and np.all((weights >= -1e-10) & (weights <= 1 + 1e-10))
        weighted = values * weights[None, :]
        starts = np.arange(count)
        affected = np.any((starts[:, None] <= positions[None, :]) & (positions[None, :] < (starts + window)[:, None]), axis=1)
        result[indices, 0] = weighted.mean(1); result[indices, 1] = weighted.max(1)
        if affected.any():
            result[indices, 2] = weighted[:, affected].mean(1); result[indices, 3] = weighted[:, affected].max(1)
    return result

def project(summary, matrices):
    assert summary.shape == (WIDTH, 4) and len(matrices) == 4
    return np.concatenate([summary[:, i] @ matrix for i, matrix in enumerate(matrices)])

def allele_delta(parent, mutant, parent_probability, mutant_probability, groups=None, matrices=None):
    parent, mutant = normalize(parent), normalize(mutant)
    assert len(parent) == len(mutant)
    positions = tuple(i for i, (left, right) in enumerate(zip(parent, mutant)) if left != right)
    matrices = generate() if matrices is None else matrices
    if not positions:
        return np.zeros(256, dtype=np.float32)
    a = pooled_blocks(scan(parent, groups), len(parent), positions, parent_probability)
    b = pooled_blocks(scan(mutant, groups), len(mutant), positions, mutant_probability)
    return (project(b, matrices) - project(a, matrices)).astype(np.float32)
