"""Outcome-blind alignment, deterministic selection and exact null permutations."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
import numpy as np
import pandas as pd


def edit_band(cost):
    x = np.asarray(cost)
    if not np.isfinite(x).all() or (x < 0).any() or (x != np.floor(x)).any():
        raise ValueError('Edit sizes must be finite nonnegative integers')
    return np.select([x == 0, x == 1, x <= 5, x <= 10, x <= 25, x <= 50],
                     ['0', '1', '2-5', '6-10', '11-25', '26-50'], default='>50')


def choose_recipe(records, tolerance=0.002):
    """Regret window -> rank -> simpler model -> lexical ID; no hidden tie rules."""
    if not records or tolerance < 0:
        raise ValueError('Nonempty recipes and nonnegative tolerance required')
    if len({r['recipe_id'] for r in records}) != len(records):
        raise ValueError('Recipe identifiers must be unique')
    for r in records:
        if not all(np.isfinite(r[k]) for k in ('regret', 'rank', 'complexity')):
            raise ValueError('Selection metrics must be finite')
    best = min(r['regret'] for r in records)
    tied = [r for r in records if r['regret'] <= best + tolerance]
    return min(tied, key=lambda r: (-r['rank'], r['complexity'], r['recipe_id']))['recipe_id']


def _seed(seed, key):
    return (int(hashlib.sha256(str(key).encode()).hexdigest()[:16], 16) + seed) % 2**64


def bijective_map(frame, *, partition, strata=(), unit=None, seed=20260909):
    """Donor permutation over UNIQUE interventions, separately per partition/stratum.

    unit requests a cross-unit derangement. An impossible stratum is wholly
    ineligible, retaining identity only as a sentinel, never used for comparison.
    A plain permutation allows fixed points and reports them explicitly.
    """
    if frame.index.has_duplicates or not frame.index.equals(pd.RangeIndex(len(frame))):
        raise ValueError('Require unique positional RangeIndex')
    if 'intervention_id' not in frame or frame.intervention_id.duplicated().any():
        raise ValueError('Permute unique intervention blocks, not replicated rows')
    keys = [partition, *strata]
    if not keys or len(keys) != len(set(keys)) or frame[keys].isna().any().any():
        raise ValueError('Explicit, nonmissing partition/stratum keys required')
    donors = np.arange(len(frame))
    eligible = np.zeros(len(frame), dtype=bool)
    audit = []
    for key, idx in frame.groupby(keys, sort=True, dropna=False).indices.items():
        idx = np.asarray(idx, dtype=int)
        rng = np.random.default_rng(_seed(seed, key))
        reason = None
        if len(idx) < 2:
            reason = 'singleton'
        elif unit is not None:
            units = frame.iloc[idx][unit].astype(str).to_numpy()
            groups = [rng.permutation(idx[units == u]) for u in sorted(set(units))]
            largest = max(map(len, groups))
            if largest * 2 > len(idx):
                reason = 'cross_unit_derangement_impossible'
            else:
                order = rng.permutation(len(groups))
                sequence = np.concatenate([groups[i] for i in order])
                donors[sequence] = np.roll(sequence, largest)
                eligible[idx] = True
        else:
            donors[idx] = rng.permutation(idx)
            eligible[idx] = True
        audit.append({'stratum': str(key), 'rows': len(idx), 'eligible': reason is None,
                      'reason': reason, 'fixed_points': int((donors[idx] == idx).sum())})
    if not np.array_equal(np.sort(donors), np.arange(len(frame))):
        raise AssertionError('Donors are not a bijection')
    if not frame.iloc[donors][keys].reset_index(drop=True).equals(frame[keys]):
        raise AssertionError('Donor crosses partition or stratum')
    if unit and np.any(frame[unit].to_numpy()[eligible] == frame.iloc[donors][unit].to_numpy()[eligible]):
        raise AssertionError('Eligible cross-unit donor retained its unit')
    return donors, eligible, audit


@dataclass(frozen=True)
class Alignment:
    reference: str
    mutant: str
    reference_indices: tuple[int, ...]
    mutant_indices: tuple[int, ...]

    def windows(self, radius):
        """Paired sequence coordinate intervals surrounding the edit (half-open)."""
        if radius < 0:
            raise ValueError('Radius must be nonnegative')
        changed = [i for i, (r, m) in enumerate(zip(self.reference_indices, self.mutant_indices))
                   if r < 0 or m < 0 or self.reference[r] != self.mutant[m]]
        if not changed:
            raise ValueError('No mutation')
        start, end = min(changed), max(changed) + 1
        intervals = []
        for indices, sequence in ((self.reference_indices, self.reference), (self.mutant_indices, self.mutant)):
            # Counts of consumed bases define the boundary even for an all-gap insertion/deletion.
            left = sum(i >= 0 for i in indices[:start])
            right = sum(i >= 0 for i in indices[:end])
            intervals.append((max(0, left - radius), min(len(sequence), right + radius)))
        return tuple(intervals)


def align(reference, mutant):
    """Equal-length edits use documented assay coordinates; indels use global edit alignment.

    For indels a minimum Levenshtein path is selected with diagonal/deletion/
    insertion precedence on ties. This is a coordinate convention, not an
    inference of evolutionary history. Repetitive indels can be ambiguous.
    """
    r, m = reference.upper().replace('U', 'T'), mutant.upper().replace('U', 'T')
    if not r or not m or set(r + m) - set('ACGT'):
        raise ValueError('Nonempty unambiguous nucleotide sequences required')
    if len(r) == len(m):
        return Alignment(r, m, tuple(range(len(r))), tuple(range(len(m))))
    distance = np.zeros((len(r) + 1, len(m) + 1), dtype=np.int32)
    distance[:, 0] = np.arange(len(r) + 1)
    distance[0, :] = np.arange(len(m) + 1)
    for i in range(1, len(r) + 1):
        for j in range(1, len(m) + 1):
            distance[i, j] = min(distance[i-1, j-1] + (r[i-1] != m[j-1]),
                                  distance[i-1, j] + 1, distance[i, j-1] + 1)
    ri, mi = [], []
    i, j = len(r), len(m)
    while i or j:
        if i and j and distance[i, j] == distance[i-1, j-1] + (r[i-1] != m[j-1]):
            ri.append(i-1); mi.append(j-1); i -= 1; j -= 1
        elif i and distance[i, j] == distance[i-1, j] + 1:
            ri.append(i-1); mi.append(-1); i -= 1
        else:
            ri.append(-1); mi.append(j-1); j -= 1
    return Alignment(r, m, tuple(reversed(ri)), tuple(reversed(mi)))


def delta(reference, mutant):
    reference, mutant = np.asarray(reference), np.asarray(mutant)
    if reference.shape != mutant.shape or not np.isfinite(reference).all() or not np.isfinite(mutant).all():
        raise ValueError('Paired encoder outputs must have matching finite shapes')
    return mutant - reference
