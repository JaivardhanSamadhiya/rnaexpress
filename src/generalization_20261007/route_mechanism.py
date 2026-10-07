"""Fixed, literature-motivated sequence architecture features for small edits.

These are compositional/arrangement proxies, not measured binding affinities,
RNA structure predictions, or evidence that a particular RBP mediates an assay.
No source identity, endpoint labels, genes, localization, or replicate outcomes
are inputs to feature construction. The original 246 columns remain explicit.
"""

from __future__ import annotations

from functools import lru_cache
import math
import re

from src.research_20260921 import common as _runtime
import numpy as np

CONFIGS = [
    {"id": "mechanism_l2_005", "penalty": .005},
    {"id": "mechanism_l2_05", "penalty": .05},
    {"id": "mechanism_l2_5", "penalty": .5},
]
WINDOWS = (8, 16, 32, 64)
CORE_WINDOWS = (29, 42, 54)
PATTERNS = (("CCTCC", "CCTCC"), ("CCTCCC", "CCTCCC"), ("RCCTCCC", "[AG]CCTCCC"))
SUMMARY_NAMES = (
    tuple(f"affected_{width}nt_{stat}" for width in WINDOWS
          for stat in ("max_AG_fraction", "mean_squared_AG_fraction", "mean_G_fraction"))
    + ("whole_AG_fraction", "whole_G_fraction", "longest_AG_run_fraction",
       "mass_AG_runs_ge4_fraction", "AG_adjacent_pair_fraction")
    + tuple(f"whole_{name}_density" for name, _ in PATTERNS)
    + tuple(f"max_CCTCC_start_density_{width}nt" for width in CORE_WINDOWS)
    + ("CCTCC_pair_decay_10nt_density", "CCTCC_pair_decay_30nt_density")
)
BACKGROUND_INDICES = (12, 13, 17, 21)
BACKGROUND_NAMES = tuple(SUMMARY_NAMES[index] for index in BACKGROUND_INDICES)
MECHANISM_NAMES = (
    tuple("delta_" + name for name in SUMMARY_NAMES)
    + tuple("delta_" + name + "*symmetric_" + background
            for name in SUMMARY_NAMES for background in BACKGROUND_NAMES)
)


def normalize(sequence: str) -> str:
    value = str(sequence).upper().replace("U", "T")
    if not value or set(value) - set("ACGT"):
        raise ValueError("Mechanism features require exact nonempty A/C/G/T sequences")
    return value


def motif_starts(sequence: str, pattern: str) -> tuple[int, ...]:
    """Return every overlapping forward-strand match; RNA U is normalized to T."""
    return tuple(match.start() for match in re.finditer("(?=" + pattern + ")", sequence))


def affected_starts(length: int, width: int, positions: tuple[int, ...]) -> tuple[int, ...]:
    """Fixed-length sliding windows touching any changed site, without padding."""
    width = min(length, width)
    return tuple(sorted({start for position in positions
                         for start in range(max(0, position - width + 1),
                                            min(position, length - width) + 1)}))


@lru_cache(maxsize=120000)
def summarize(sequence: str, positions: tuple[int, ...]) -> tuple[float, ...]:
    """Twenty-five prespecified summaries; windows and kernels are hypotheses."""
    length = len(sequence)
    ag = np.fromiter((base in "AG" for base in sequence), dtype=float, count=length)
    guanine = np.fromiter((base == "G" for base in sequence), dtype=float, count=length)
    ag_prefix = np.r_[0., np.cumsum(ag)]
    g_prefix = np.r_[0., np.cumsum(guanine)]
    values = []
    for requested_width in WINDOWS:
        width = min(length, requested_width)
        starts = np.asarray(affected_starts(length, width, positions), dtype=int)
        if not len(starts):
            values.extend((0., 0., 0.))
            continue
        fractions = (ag_prefix[starts + width] - ag_prefix[starts]) / width
        g_fractions = (g_prefix[starts + width] - g_prefix[starts]) / width
        values.extend((float(fractions.max()), float(np.mean(fractions ** 2)), float(g_fractions.mean())))
    runs = [len(match.group()) for match in re.finditer("[AG]+", sequence)]
    values.extend((float(ag.mean()), float(guanine.mean()), max(runs, default=0) / length,
                   sum(run for run in runs if run >= 4) / length,
                   float(np.mean(ag[:-1] * ag[1:])) if length > 1 else 0.))
    starts_by_name = {}
    for name, pattern in PATTERNS:
        starts = motif_starts(sequence, pattern)
        starts_by_name[name] = starts
        motif_length = 7 if name == "RCCTCCC" else len(name)
        values.append(len(starts) / max(1, length - motif_length + 1))
    cores = starts_by_name["CCTCC"]
    for requested_width in CORE_WINDOWS:
        width = min(length, requested_width)
        # Count complete five-base cores contained in each architecture window.
        if width < 5:
            values.append(0.)
        else:
            count = max((sum(start <= core <= start + width - 5 for core in cores)
                         for start in range(length - width + 1)), default=0)
            values.append(count / max(1, width - 5 + 1))
    for decay in (10., 30.):
        values.append(sum(math.exp(-(right - left) / decay)
                          for i, left in enumerate(cores) for right in cores[i + 1:]) / length)
    assert len(values) == len(SUMMARY_NAMES) == 25
    return tuple(values)


def mechanism_delta(parent: str, mutant: str) -> np.ndarray:
    parent, mutant = normalize(parent), normalize(mutant)
    if len(parent) != len(mutant):
        raise ValueError("Mechanism route supports corresponding-coordinate substitutions only")
    positions = tuple(index for index, (left, right) in enumerate(zip(parent, mutant)) if left != right)
    if not positions:
        return np.zeros(len(MECHANISM_NAMES), dtype=float)
    before = np.asarray(summarize(parent, positions))
    after = np.asarray(summarize(mutant, positions))
    delta = after - before
    # Symmetric sequence context makes reversing the entire edit exactly negate
    # this block, and uses neither a WT outcome nor a measured parent quantity.
    background = (before[list(BACKGROUND_INDICES)] + after[list(BACKGROUND_INDICES)]) / 2
    result = np.r_[delta, np.outer(delta, background).ravel()]
    if not np.isfinite(result).all():
        raise ValueError("Nonfinite mechanism features")
    return result


def build_features(frame, base246) -> np.ndarray:
    baseline = np.asarray(base246, dtype=float)
    if baseline.shape != (len(frame), 246) or not np.isfinite(baseline).all():
        raise ValueError("Mechanism route requires row-aligned finite historical 246-column features")
    block = np.asarray([mechanism_delta(parent, mutant)
                        for parent, mutant in zip(frame["parent_sequence"], frame["mutant_sequence"])], dtype=float)
    if len(frame) == 0:
        block = np.zeros((0, len(MECHANISM_NAMES)), dtype=float)
    return np.column_stack((baseline, block))


def feature_schema() -> dict:
    return {
        "historical_columns": 246,
        "additional_columns": len(MECHANISM_NAMES),
        "total_columns": 246 + len(MECHANISM_NAMES),
        "columns": list(MECHANISM_NAMES),
        "affected_windows_nt": list(WINDOWS),
        "C_core_architecture_windows_nt": list(CORE_WINDOWS),
        "patterns": dict(PATTERNS),
        "background": "arithmetic mean of parent and mutant sequence summaries; four fixed summaries",
        "normalization": "actual unpadded window length, available motif starts, or insert length; no outcome-dependent normalization",
        "claims": "literature-motivated compositional and architecture proxies; not CNBP/HNRNPK binding predictions",
        "PRRE_5TOP": "excluded: published efficient PRRE localization requires 5primeUTR context, absent from admitted 3primeUTR/core inputs",
        "model_selection": "one feature block, three prespecified L2 penalties; nested source-only selection",
    }


def fit_model(frame, features, config):
    from .route_scaling import fit_model as fit_shared
    return fit_shared(frame, features, config)


def predict_model(model, features):
    from .route_scaling import predict_model as predict_shared
    return predict_shared(model, features)
