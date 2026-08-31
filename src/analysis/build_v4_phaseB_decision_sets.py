"""Build provenance-safe RNAddress v4 Phase B decision sets.

This script constructs candidate landscapes and deterministic edit geometry only.
It does not fit a model and never reads N-zip or Astrocyte data.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import platform
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PHASE_A = ROOT / "results" / "v4_phaseA"
OUT = ROOT / "results" / "v4_phaseB"
COMMON = PHASE_A / "common_intervention_outcomes.csv.gz"
SOURCE_TABLES = {
    "mikl_gse173098": PHASE_A / "mikl_interventions.csv.gz",
    "tdp43_gse288185": PHASE_A / "tdp_interventions.csv.gz",
    "moffatt_gse334718": PHASE_A / "moffatt_interventions.csv.gz",
}
MINIMUM_CANDIDATES = 5
GOOD_NORMALIZED_REGRET_TOLERANCE = 0.10
GZIP_OPTIONS = {"method": "gzip", "mtime": 0}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_id(prefix: str, fields: list[str]) -> str:
    payload = "\x1f".join(fields)
    return f"{prefix}:{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:20]}"


def changed_positions(parent: str, mutant: str) -> list[int]:
    if len(parent) != len(mutant):
        raise ValueError("Phase B currently requires aligned fixed-length intervention pairs")
    return [index for index, (left, right) in enumerate(zip(parent, mutant)) if left != right]


def changed_blocks(positions: list[int]) -> int:
    if not positions:
        return 0
    return 1 + sum(right != left + 1 for left, right in zip(positions, positions[1:]))


def decision_fields(row: pd.Series) -> tuple[str, list[str]]:
    dataset = str(row["dataset"])
    if dataset == "mikl_gse173098":
        kind = "gene_cell_landscape"
        fields = [dataset, str(row["assay"]), str(row["reporter"]), str(row["cell_type"]), str(row["gene_name"])]
    elif dataset == "tdp43_gse288185":
        kind = "gene_landscape"
        fields = [dataset, str(row["assay"]), str(row["reporter"]), str(row["cell_type"]), str(row["gene_id"])]
    elif dataset == "moffatt_gse334718":
        kind = "parent_assay_reporter_landscape"
        fields = [dataset, str(row["assay"]), str(row["reporter"]), str(row["cell_type"]), str(row["parent_id"])]
    else:
        raise ValueError(f"Unauthorized Phase B dataset: {dataset}")
    return kind, fields


def load_geometry() -> pd.DataFrame:
    frames = []
    wanted = [
        "dataset",
        "parent_id",
        "mutant_id",
        "substitution_count",
        "insertion_length",
        "deletion_length",
        "operation_size",
    ]
    for dataset, path in SOURCE_TABLES.items():
        frame = pd.read_csv(path)
        frame["dataset"] = dataset
        for column in wanted:
            if column not in frame:
                frame[column] = np.nan
        frames.append(frame[wanted])
    geometry = pd.concat(frames, ignore_index=True)
    if geometry[["dataset", "parent_id", "mutant_id"]].duplicated().any():
        raise ValueError("Source intervention geometry is not unique")
    return geometry


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    common = pd.read_csv(COMMON)
    authorized = set(SOURCE_TABLES)
    if set(common["dataset"]) != authorized:
        raise ValueError("Unexpected dataset entered Phase B common outcomes")
    if not common["outcome_valid"].all() or not np.isfinite(common["localization_effect"]).all():
        raise ValueError("Phase B common outcomes contain invalid or non-finite effects")
    geometry = load_geometry()
    candidates = common.merge(
        geometry,
        on=["dataset", "parent_id", "mutant_id"],
        how="left",
        validate="many_to_one",
    )
    if candidates["substitution_count"].isna().any():
        raise ValueError("Intervention geometry join is incomplete")

    kinds: list[str] = []
    decision_ids: list[str] = []
    for _, row in candidates.iterrows():
        kind, fields = decision_fields(row)
        kinds.append(kind)
        decision_ids.append(stable_id("decision", fields))
    candidates["decision_set_kind"] = kinds
    candidates["decision_set_id"] = decision_ids
    candidates["candidate_id"] = [
        stable_id("candidate", [str(decision), str(dataset), str(mutant)])
        for decision, dataset, mutant in zip(
            candidates["decision_set_id"], candidates["dataset"], candidates["mutant_id"]
        )
    ]
    if candidates[["decision_set_id", "mutant_id"]].duplicated().any():
        raise ValueError("A decision set contains duplicate candidate interventions")

    positions_all: list[list[int]] = []
    for parent, mutant, declared in zip(
        candidates["parent_sequence"],
        candidates["mutant_sequence"],
        candidates["edit_distance"],
    ):
        positions = changed_positions(str(parent), str(mutant))
        if len(positions) != int(declared):
            raise ValueError("Exact sequence edit distance disagrees with Phase A")
        positions_all.append(positions)
    candidates["changed_block_count"] = [changed_blocks(value) for value in positions_all]
    candidates["mean_edit_position_1based"] = [float(np.mean(value) + 1) for value in positions_all]
    candidates["edit_span_length"] = [max(value) - min(value) + 1 for value in positions_all]
    candidates["first_edit_position_1based"] = [min(value) + 1 for value in positions_all]
    candidates["last_edit_position_1based"] = [max(value) + 1 for value in positions_all]
    candidates["reference_subsequence"] = [
        str(parent)[min(pos) : max(pos) + 1]
        for parent, pos in zip(candidates["parent_sequence"], positions_all)
    ]
    candidates["alternate_subsequence"] = [
        str(mutant)[min(pos) : max(pos) + 1]
        for mutant, pos in zip(candidates["mutant_sequence"], positions_all)
    ]
    candidates["replacement_length"] = candidates["operation_size"].fillna(
        candidates["edit_distance"]
    ).astype(int)
    candidates["insertion_length"] = candidates["insertion_length"].fillna(0).astype(int)
    candidates["deletion_length"] = candidates["deletion_length"].fillna(0).astype(int)
    candidates["substitution_count"] = candidates["substitution_count"].astype(int)

    sizes = candidates.groupby("decision_set_id")["candidate_id"].size()
    candidates["candidate_set_size"] = candidates["decision_set_id"].map(sizes).astype(int)
    candidates["selection_eligible"] = candidates["candidate_set_size"].ge(MINIMUM_CANDIDATES)
    group = candidates.groupby("decision_set_id", sort=True)
    summary = group.agg(
        dataset=("dataset", "first"),
        decision_set_kind=("decision_set_kind", "first"),
        assay=("assay", "first"),
        reporter=("reporter", "first"),
        cell_type=("cell_type", "first"),
        gene_id=("gene_id", "first"),
        gene_name=("gene_name", "first"),
        biological_parent_count=("parent_id", "nunique"),
        candidate_count=("candidate_id", "size"),
        increase_candidate_count=("localization_effect", lambda values: int((values > 0).sum())),
        decrease_candidate_count=("localization_effect", lambda values: int((values < 0).sum())),
        minimum_effect=("localization_effect", "min"),
        maximum_effect=("localization_effect", "max"),
        effect_range=("localization_effect", lambda values: float(values.max() - values.min())),
        minimum_edit_cost=("edit_cost", "min"),
        maximum_edit_cost=("edit_cost", "max"),
    ).reset_index()
    summary["selection_eligible"] = summary["candidate_count"].ge(MINIMUM_CANDIDATES) & summary[
        "effect_range"
    ].gt(0)
    if not summary.loc[summary["selection_eligible"], "effect_range"].gt(0).all():
        raise ValueError("Eligible decision set has zero outcome range")

    candidates.to_csv(OUT / "phaseB_candidates.csv.gz", index=False, compression=GZIP_OPTIONS)
    summary.to_csv(OUT / "decision_set_summary.csv", index=False)
    eligible = summary[summary["selection_eligible"]]
    by_source: dict[str, object] = {}
    for dataset, frame in summary.groupby("dataset"):
        eligible_source = frame[frame["selection_eligible"]]
        by_source[dataset] = {
            "all_decision_sets": len(frame),
            "eligible_decision_sets": len(eligible_source),
            "eligible_candidate_rows": int(eligible_source["candidate_count"].sum()),
            "minimum_candidates": int(eligible_source["candidate_count"].min()),
            "median_candidates": float(eligible_source["candidate_count"].median()),
            "mean_candidates": float(eligible_source["candidate_count"].mean()),
            "maximum_candidates": int(eligible_source["candidate_count"].max()),
            "sets_with_increase_candidate": int(eligible_source["increase_candidate_count"].gt(0).sum()),
            "sets_with_decrease_candidate": int(eligible_source["decrease_candidate_count"].gt(0).sum()),
        }
    audit = {
        "phase": "v4_phaseB_decision_set_audit",
        "git_commit_at_run": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "minimum_candidate_count": MINIMUM_CANDIDATES,
        "good_normalized_regret_tolerance": GOOD_NORMALIZED_REGRET_TOLERANCE,
        "eligible_base_decision_sets": len(eligible),
        "eligible_directional_decision_tasks": len(eligible) * 2,
        "all_base_decision_sets": len(summary),
        "independent_gene_labels": int(candidates["gene_name"].astype(str).str.lower().nunique()),
        "independent_parent_contexts": int(candidates["parent_id"].nunique()),
        "by_source": by_source,
        "scope_guards": {
            "nzip_outcomes_used": False,
            "astrocyte_outcomes_opened": False,
            "model_fit_performed": False,
        },
    }
    (OUT / "decision_set_audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "phase": "v4_phaseB_decision_set_construction",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "inputs": {
            path.relative_to(ROOT).as_posix(): {"bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in [COMMON, *SOURCE_TABLES.values(), Path(__file__)]
        },
        "outputs": {},
    }
    for path in sorted(OUT.glob("*")):
        if path.is_file() and path.name != "decision_set_manifest.json":
            manifest["outputs"][path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    (OUT / "decision_set_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
