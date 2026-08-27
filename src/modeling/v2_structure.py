"""ViennaRNA ensemble and edit-accessibility features for RNAddress v2."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import RNA

from .features import normalize_sequence
from .v2_features import V2Features


def _sequence_key(sequence: str) -> str:
    return hashlib.sha256(sequence.encode()).hexdigest()


def fold_sequence(sequence: str) -> dict[str, object]:
    rna = sequence.replace("T", "U")
    compound = RNA.fold_compound(rna)
    _, mfe = compound.mfe()
    _, ensemble_energy = compound.pf()
    matrix = compound.bpp()
    unpaired = []
    for position in range(1, len(rna) + 1):
        paired = sum(matrix[min(position, other)][max(position, other)] for other in range(1, len(rna) + 1) if other != position)
        unpaired.append(max(0.0, min(1.0, 1.0 - paired)))
    return {
        "length": len(rna),
        "mfe_per_nt": float(mfe / len(rna)),
        "ensemble_energy_per_nt": float(ensemble_energy / len(rna)),
        "ensemble_diversity_per_nt": float(compound.mean_bp_distance() / len(rna)),
        "mean_unpaired": float(np.mean(unpaired)),
        "unpaired": unpaired,
    }


def _load_cache(path: Path) -> dict[str, dict[str, object]]:
    return json.loads(path.read_text()) if path.exists() else {}


def _save_cache(path: Path, cache: dict[str, dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, separators=(",", ":")))


def build_structure_augmented_features(
    frame: pd.DataFrame,
    base: V2Features,
    cache_path: Path,
    radius: int = 10,
) -> V2Features:
    cache = _load_cache(cache_path)
    sequences = {
        normalize_sequence(sequence)
        for column in ["parent_sequence", "mutant_sequence"]
        for sequence in frame[column]
    }
    missing = 0
    for index, sequence in enumerate(sorted(sequences), start=1):
        key = _sequence_key(sequence)
        if key not in cache:
            cache[key] = fold_sequence(sequence)
            missing += 1
            if missing % 250 == 0:
                _save_cache(cache_path, cache)
                print(f"folded {missing} new RNA sequences ({index}/{len(sequences)})", flush=True)
    _save_cache(cache_path, cache)

    parent_extra: list[np.ndarray] = []
    edit_extra: list[np.ndarray] = []
    summary_names = [
        "mfe_per_nt",
        "ensemble_energy_per_nt",
        "ensemble_diversity_per_nt",
        "mean_unpaired",
    ]
    for row in frame.itertuples(index=False):
        parent = normalize_sequence(row.parent_sequence)
        mutant = normalize_sequence(row.mutant_sequence)
        changed = [i for i, (left, right) in enumerate(zip(parent, mutant)) if left != right]
        center = int(round(float(np.mean(changed))))
        window = range(max(0, center - radius), min(len(parent), center + radius + 1))
        parent_fold = cache[_sequence_key(parent)]
        mutant_fold = cache[_sequence_key(mutant)]
        parent_summary = np.asarray([parent_fold[name] for name in summary_names], np.float32)
        mutant_summary = np.asarray([mutant_fold[name] for name in summary_names], np.float32)
        parent_unpaired = np.asarray(parent_fold["unpaired"], np.float32)
        mutant_unpaired = np.asarray(mutant_fold["unpaired"], np.float32)
        changed_parent = float(parent_unpaired[changed].mean())
        changed_mutant = float(mutant_unpaired[changed].mean())
        local_parent = float(parent_unpaired[list(window)].mean())
        local_mutant = float(mutant_unpaired[list(window)].mean())
        parent_extra.append(parent_summary)
        edit_extra.append(
            np.concatenate(
                [
                    mutant_summary - parent_summary,
                    np.asarray(
                        [
                            changed_parent,
                            changed_mutant,
                            changed_mutant - changed_parent,
                            local_parent,
                            local_mutant,
                            local_mutant - local_parent,
                        ],
                        np.float32,
                    ),
                ]
            )
        )
    parent = np.column_stack([base.parent, np.vstack(parent_extra)]).astype(np.float32)
    edit = np.column_stack([base.edit, np.vstack(edit_extra)]).astype(np.float32)
    return V2Features(parent=parent, edit=edit, joint=np.column_stack([parent, edit]))
