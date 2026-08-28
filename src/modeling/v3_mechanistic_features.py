"""Prespecified outcome-free mechanistic features for RNAddress v3 Phase 3."""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import re

import numpy as np
import pandas as pd

from .features import normalize_sequence
from .v2_structure import _load_cache, _save_cache, _sequence_key, fold_sequence


MOTIF_PATTERNS = {
    "tdp_ug_rich": r"UGUGU|GUGUG|GUAUG",
    "au_rich": r"UAUUUAU|AUUUA",
    "pumilio": r"UGU[ACGU]AUA",
    "cpe": r"UUUUAU",
    "drach": r"[AGU][AG]AC[ACU]",
}
RADII = (5, 10, 20)
BASES = "ACGU"
SUBSTITUTIONS = tuple(f"{left}>{right}" for left in BASES for right in BASES if left != right)


@dataclass(frozen=True)
class MechanisticFeatures:
    values: np.ndarray
    names: tuple[str, ...]
    families: tuple[tuple[str, ...], ...]

    def keep_without(self, removed_family: str) -> np.ndarray:
        return np.asarray(
            [removed_family not in memberships for memberships in self.families], dtype=bool
        )


def _rna(sequence: str) -> str:
    return normalize_sequence(sequence).replace("T", "U")


def motif_hits(sequence: str, pattern: str) -> set[tuple[int, int, str]]:
    regex = re.compile(f"(?=({pattern}))")
    return {
        (match.start(), match.start() + len(match.group(1)), match.group(1))
        for match in regex.finditer(sequence)
    }


def _parent_state(sequence: str, counts: dict[str, int]) -> dict[str, float]:
    length = len(sequence)
    frequencies = np.asarray([sequence.count(base) / length for base in BASES], dtype=float)
    entropy = -sum(value * math.log2(value) for value in frequencies if value > 0) / 2.0
    longest = max((len(match.group(0)) for match in re.finditer(r"([ACGU])\1*", sequence)), default=0)
    state = {
        "parent_gc": (sequence.count("G") + sequence.count("C")) / length,
        "parent_au": (sequence.count("A") + sequence.count("U")) / length,
        "parent_mono_entropy": entropy,
        "parent_max_homopolymer_fraction": longest / length,
    }
    state.update({f"parent_{name}_density": count / length for name, count in counts.items()})
    return state


def _window_mean(values: np.ndarray, center: int, radius: int) -> float:
    left = max(0, center - radius)
    right = min(len(values), center + radius + 1)
    return float(values[left:right].mean())


def ensure_structure_cache(frame: pd.DataFrame, cache_path: Path) -> dict[str, dict[str, object]]:
    cache = _load_cache(cache_path)
    sequences = {
        normalize_sequence(value)
        for column in ("parent_sequence", "mutant_sequence")
        for value in frame[column]
    }
    missing = 0
    for sequence_number, sequence in enumerate(sorted(sequences), start=1):
        key = _sequence_key(sequence)
        if key not in cache:
            cache[key] = fold_sequence(sequence)
            missing += 1
            if missing % 100 == 0:
                _save_cache(cache_path, cache)
                print(
                    f"folded {missing} new Phase 3 sequences ({sequence_number}/{len(sequences)})",
                    flush=True,
                )
    _save_cache(cache_path, cache)
    return cache


def build_mechanistic_features(
    frame: pd.DataFrame,
    cache_path: Path,
    stability_prediction: np.ndarray | None = None,
) -> MechanisticFeatures:
    """Build the frozen motif/accessibility/parent-interaction block.

    Family memberships are deliberately nonexclusive. An accessibility ablation,
    for example, removes both base accessibility terms and motif-by-accessibility
    interactions rather than leaving a disguised accessibility feature behind.
    """
    if stability_prediction is not None and len(stability_prediction) != len(frame):
        raise ValueError("Stability prediction length does not match N-zip rows")
    cache = ensure_structure_cache(frame, cache_path)
    rows: list[list[float]] = []
    names: list[str] | None = None
    memberships: list[tuple[str, ...]] | None = None

    for row_number, row in enumerate(frame.itertuples(index=False)):
        parent = _rna(row.parent_sequence)
        mutant = _rna(row.mutant_sequence)
        if len(parent) != len(mutant):
            raise ValueError("Phase 3 mechanism features require length-preserving edits")
        changed = [index for index, pair in enumerate(zip(parent, mutant)) if pair[0] != pair[1]]
        if len(changed) != 1:
            raise ValueError("Primary Phase 3 mechanism block expects exact SNVs")
        center = changed[0]
        parent_fold = cache[_sequence_key(normalize_sequence(row.parent_sequence))]
        mutant_fold = cache[_sequence_key(normalize_sequence(row.mutant_sequence))]
        parent_unpaired = np.asarray(parent_fold["unpaired"], dtype=float)
        mutant_unpaired = np.asarray(mutant_fold["unpaired"], dtype=float)

        values: list[float] = []
        row_names: list[str] = []
        row_memberships: list[tuple[str, ...]] = []

        def add(name: str, value: float, *families: str) -> None:
            row_names.append(name)
            values.append(float(value))
            row_memberships.append(tuple(sorted(set(families))))

        motif_delta: dict[str, float] = {}
        parent_density: dict[str, float] = {}
        parent_counts: dict[str, int] = {}
        for motif_name, pattern in MOTIF_PATTERNS.items():
            before = motif_hits(parent, pattern)
            after = motif_hits(mutant, pattern)
            gains = after - before
            losses = before - after
            delta = float(len(after) - len(before))
            changed_fraction = (len(gains) + len(losses)) / max(1, len(before | after))
            parent_counts[motif_name] = len(before)
            parent_density[motif_name] = len(before) / len(parent)
            motif_delta[motif_name] = delta
            add(f"motif_{motif_name}_parent_count", len(before), "motif_core")
            add(f"motif_{motif_name}_mutant_count", len(after), "motif_core")
            add(f"motif_{motif_name}_delta", delta, "motif_core")
            add(f"motif_{motif_name}_gain", len(gains), "motif_core")
            add(f"motif_{motif_name}_loss", len(losses), "motif_core")
            add(
                f"motif_{motif_name}_changed_fraction",
                changed_fraction,
                "motif_core",
            )

        state = _parent_state(parent, parent_counts)
        for name, value in state.items():
            add(name, value, "parent_state")

        parent_site = float(parent_unpaired[center])
        mutant_site = float(mutant_unpaired[center])
        site_delta = mutant_site - parent_site
        add("access_parent_edit_site", parent_site, "accessibility")
        add("access_mutant_edit_site", mutant_site, "accessibility")
        add("access_delta_edit_site", site_delta, "accessibility")
        access_delta: dict[int, float] = {}
        for radius in RADII:
            parent_local = _window_mean(parent_unpaired, center, radius)
            mutant_local = _window_mean(mutant_unpaired, center, radius)
            delta_local = mutant_local - parent_local
            access_delta[radius] = delta_local
            add(f"access_parent_r{radius}", parent_local, "accessibility")
            add(f"access_mutant_r{radius}", mutant_local, "accessibility")
            add(f"access_delta_r{radius}", delta_local, "accessibility")

        for motif_name in MOTIF_PATTERNS:
            add(
                f"interaction_{motif_name}_delta_x_parent_density",
                motif_delta[motif_name] * parent_density[motif_name],
                "motif_interaction",
                "parent_state_interaction",
            )
            add(
                f"interaction_{motif_name}_delta_x_parent_site_access",
                motif_delta[motif_name] * parent_site,
                "motif_interaction",
                "accessibility",
            )
            add(
                f"interaction_{motif_name}_delta_x_access_delta_r10",
                motif_delta[motif_name] * access_delta[10],
                "motif_interaction",
                "accessibility",
            )

        substitution = f"{parent[center]}>{mutant[center]}"
        if substitution not in SUBSTITUTIONS:
            raise ValueError(f"Invalid exact substitution: {substitution}")
        for label in SUBSTITUTIONS:
            indicator = float(label == substitution)
            add(
                f"interaction_substitution_{label}_x_parent_gc",
                indicator * state["parent_gc"],
                "parent_state_interaction",
            )
            add(
                f"interaction_substitution_{label}_x_parent_au",
                indicator * state["parent_au"],
                "parent_state_interaction",
            )
        for radius in RADII:
            add(
                f"interaction_access_delta_r{radius}_x_parent_gc",
                access_delta[radius] * state["parent_gc"],
                "accessibility",
                "parent_state_interaction",
            )

        if stability_prediction is not None:
            stability = float(stability_prediction[row_number])
            add("tdp_aux_predicted_stability_delta", stability, "stability")
            add(
                "interaction_tdp_stability_x_parent_au",
                stability * state["parent_au"],
                "stability",
                "parent_state_interaction",
            )

        if names is None:
            names = row_names
            memberships = row_memberships
        elif row_names != names or row_memberships != memberships:
            raise ValueError("Mechanistic feature schema changed between rows")
        rows.append(values)

    output = np.asarray(rows, dtype=np.float32)
    if names is None or memberships is None or output.shape != (len(frame), len(names)):
        raise ValueError("Invalid Phase 3 mechanistic feature matrix")
    if not np.isfinite(output).all() or len(set(names)) != len(names):
        raise ValueError("Mechanistic features are non-finite or duplicated")
    return MechanisticFeatures(output, tuple(names), tuple(memberships))
