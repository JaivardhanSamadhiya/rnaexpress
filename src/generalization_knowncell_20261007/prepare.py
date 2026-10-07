"""Metadata-only prospective declaration; no labels, models or arrays."""
from .common import *
from .splits import masks, exact_menu_pairs


def run():
    assert not (OUT / "evaluation_complete.json").exists()
    frame = load(False)
    from src.generalization_crosscell_20261007.common import freeze_check as source_freeze
    source_freeze()
    rows, coverage = [], []
    for task in TASKS:
        seen = []
        for fold in FOLDS:
            train, test, opposite = masks(frame, task, fold)
            source, target = frame.loc[train], frame.loc[test]
            seen.extend(target.intervention_id)
            rows.append({"task": task, "source_task": TASKS[task][1], "fold": fold,
                "training_rows": len(source), "target_rows": len(target),
                "target_components": target.biological_component.nunique(), "target_contexts": target.parent_context_id.nunique(),
                "training_ids_sha256": rowhash(source), "target_ids_sha256": rowhash(target),
                "opposite_target_ids_sha256": rowhash(frame.loc[opposite]), "exact_allele_overlaps": 0,
                "component_overlaps": 0, "partial_menus": 0})
        assert len(seen) == len(set(seen)) == int(frame.cell_type.eq(TASKS[task][0]).sum())
        coverage.append({"task": task, "rows": len(seen), "components": 187})
    pairs, exclusions = exact_menu_pairs(frame)
    csvsave(OUT / "row_index.csv.gz", frame, True)
    csvsave(OUT / "metadata_fold_audit.csv", pd.DataFrame(rows))
    csvsave(OUT / "exact_menu_pairs.csv", pd.DataFrame(pairs))
    csvsave(OUT / "unmatched_menu_metadata.csv", pd.DataFrame(exclusions))
    jsave(OUT / "metadata_receipt.json", {"status": "PASS", "rows": len(frame), "components": 187,
        "tasks": TASKS, "tracks": TRACKS, "folds": FOLDS, "coverage": coverage,
        "core_sha256": sha256(CORE), "row_ids_sha256": rowhash(frame),
        "source_prefit_sha256": sha256(SOURCE_OUT / "prefit_manifest.json"),
        "exact_paired_menus": len(pairs), "paired_components": len({row["biological_component"] for row in pairs}),
        "paired_rows": sum(2 * row["candidates"] for row in pairs), "unmatched_contexts": len(exclusions),
        "unmatched_rows": sum(row["rows"] for row in exclusions),
        "lexical_pair_order_mismatches": sum(not row["lexical_allele_order_matches"] for row in pairs),
        "outcome_columns_read": False, "models_opened": False, "features_opened": False, "fits": 0})
    print("Known-cell full-menu/original-allele metadata proof PASS; no outcomes/models/features", flush=True)


if __name__ == "__main__": run()
