"""Create the outcome-blind v2 TDP-43 development/lock split."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data" / "processed" / "tdp43_motif_intervention_pairs.csv.gz"
DEV = ROOT / "data" / "processed" / "tdp43_v2_development_pairs.csv.gz"
LOCK_FEATURES = ROOT / "data" / "frozen" / "tdp43_v2_locked_features.csv.gz"
LOCK_OUTCOMES = ROOT / "data" / "frozen" / "outcomes" / "tdp43_v2_locked_outcomes.csv.gz"
MANIFEST = ROOT / "data" / "frozen" / "tdp43_v2_lock_manifest.json"
SEED = "rnaddress-v2-lock-2026-08-26"
OUTCOME_COLUMNS = [
    "parent_localization_log2_neurite_soma",
    "mutant_localization_log2_neurite_soma",
    "delta_localization",
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def choose_locked_genes(pairs: pd.DataFrame) -> list[str]:
    counts = pairs.groupby("gene_id").size().sort_values()
    # One outcome-blind hash-selected gene from each construct-count quartile.
    bins = pd.qcut(counts.rank(method="first"), 4, labels=False)
    locked: list[str] = []
    for bin_number in range(4):
        candidates = counts.index[bins == bin_number]
        locked.append(
            min(
                candidates,
                key=lambda gene_id: hashlib.sha256(
                    f"{SEED}|{gene_id}".encode()
                ).hexdigest(),
            )
        )
    return sorted(locked)


def freeze() -> dict[str, object]:
    pairs = pd.read_csv(SOURCE)
    locked_genes = choose_locked_genes(pairs)
    is_locked = pairs["gene_id"].isin(locked_genes)
    development = pairs.loc[~is_locked].copy()
    locked = pairs.loc[is_locked].copy()
    if development["gene_id"].nunique() != 12 or locked["gene_id"].nunique() != 4:
        raise ValueError("TDP-43 v2 split must contain 12 development and four locked genes")

    feature_columns = [column for column in pairs.columns if column not in OUTCOME_COLUMNS]
    outcome_columns = ["parent_id", "mutant_id", *OUTCOME_COLUMNS]
    if set(development["parent_id"]) & set(locked["parent_id"]):
        raise ValueError("TDP-43 parent leakage across the v2 split")

    DEV.parent.mkdir(parents=True, exist_ok=True)
    LOCK_FEATURES.parent.mkdir(parents=True, exist_ok=True)
    LOCK_OUTCOMES.parent.mkdir(parents=True, exist_ok=True)
    development.to_csv(DEV, index=False, compression="gzip")
    locked[feature_columns].to_csv(LOCK_FEATURES, index=False, compression="gzip")
    locked[outcome_columns].to_csv(LOCK_OUTCOMES, index=False, compression="gzip")

    locked_names = (
        locked[["gene_id", "gene_name"]]
        .drop_duplicates()
        .sort_values("gene_id")
        .to_dict("records")
    )
    manifest: dict[str, object] = {
        "frozen_date": "2026-08-26",
        "split_seed": SEED,
        "selection_rule": "Within each outcome-blind construct-count quartile, lock the gene with the lexicographically smallest SHA256(seed|gene_id).",
        "development_genes": int(development["gene_id"].nunique()),
        "development_pairs": int(len(development)),
        "locked_genes": locked_names,
        "locked_pairs": int(len(locked)),
        "outcome_columns": OUTCOME_COLUMNS,
        "prohibited_until_v2_freeze": "Do not read the locked outcome file during model or feature development.",
        "artifacts": {
            "development": {
                "path": DEV.relative_to(ROOT).as_posix(),
                "sha256": _sha256(DEV),
            },
            "locked_features": {
                "path": LOCK_FEATURES.relative_to(ROOT).as_posix(),
                "sha256": _sha256(LOCK_FEATURES),
            },
            "locked_outcomes": {
                "path": LOCK_OUTCOMES.relative_to(ROOT).as_posix(),
                "sha256": _sha256(LOCK_OUTCOMES),
            },
        },
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    print(json.dumps(freeze(), indent=2))
