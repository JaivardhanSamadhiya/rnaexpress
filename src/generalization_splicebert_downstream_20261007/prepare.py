"""Plan without encoder imports; production freeze requires admitted parity."""
import sys
from .common import *
from .producer import THREADS, BATCH, SHARD_ALLELES, projections, requirements, backend_check, GLOBAL_PROJECTION, LOCAL_PROJECTION, BACKEND_RECEIPT, IR


def plan():
    original, encoded = sequence_frames()
    pglobal, plocal = projections()
    required, alleles = requirements(encoded)
    assert len(alleles) == 18220
    lengths = {str(length): sum(len(sequence) == length for sequence in alleles) for length in (46, 150, 190, 260)}
    assert lengths == {"46":742, "150":9318, "190":3991, "260":4169}
    csvsave(OUT / "row_index.csv.gz", original, True)
    spec = {"status": "FIXED_OUTCOME_FREE_FEATURE_SPECIFICATION", "encoder": "Author-verified SpliceBERT.1024nt",
        "rows": 26258, "alleles": 18220, "hidden_dimensions": 512, "projected_global": 128, "projected_changed_base": 128,
        "columns": 256, "threads": THREADS, "batch_size": BATCH, "shard_alleles": SHARD_ALLELES,
        "execution_setting": "Exact native/IR synthetic backend probe setting; no outcome-based performance selection",
        "seed": SEED, "projection_generation": "NumPy default_rng(20261007), two float64 standard_normal((512,128))/sqrt(128), global then local, each cast float32",
        "global_projection_path": GLOBAL_PROJECTION.relative_to(ROOT).as_posix(), "global_projection_sha256": sha256(GLOBAL_PROJECTION),
        "local_projection_path": LOCAL_PROJECTION.relative_to(ROOT).as_posix(), "local_projection_sha256": sha256(LOCAL_PROJECTION),
        "global_pool": "Mean last-layer single-base tokens, excluding CLS/SEP/padding, mutant minus parent",
        "local_pool": "Mean corresponding last-layer single-base tokens at exact changed nucleotide coordinates, mutant minus parent",
        "lookup": "A/C/G/T vocabulary order one-hot in first4of512, same two projections and pools; unprojected rank<=4 per block",
        "cache": "Per-allele projected global128 and only required projected changed-position128 vectors; length/hash-sorted shards, creation-time SHA sidecars",
        "context": "Unchanged admitted encoded150/190/260nt inserts; SRLE certified46nt HBB-vector junction20+6+20; no extra flanks/padding",
        "SRLE46nt_OOD": True, "training_domain": "Author recommended64-1024nt inputs; below64nt may fail",
        "encoded_row_identity_sha256": row_identity(encoded), "original_metadata_identity_sha256": metadata_identity(original),
        "outcomes_used": False, "fine_tuning": False, "PCA": False, "learned_endpoint_signs": False,
        "layer_seed_model_feature_search": False, "original_alleles_retained_for_purge": True}
    jsave(OUT / "feature_spec.json", spec)
    jsave(OUT / "plan_receipt.json", {"status": "PASS", "scope": "Metadata/projection planning only; no encoder or feature extraction",
        "rows": len(original), "unique_alleles": len(alleles), "alleles_per_length": lengths,
        "encoded_row_identity_sha256": row_identity(encoded), "original_metadata_identity_sha256": metadata_identity(original),
        "row_index_sha256": sha256(OUT / "row_index.csv.gz"), "required_projected_tokens": sum(len(required[sequence]) for sequence in alleles),
        "tracks": TRACKS, "shapes": SHAPES, "spec_sha256": sha256(OUT / "feature_spec.json"),
        "files": {path.relative_to(ROOT).as_posix(): sha256(path) for path in (NEXT_ART / "sequence_inventory.csv.gz", NEXT_ART / "encoded_sequence_inventory.csv.gz", GLOBAL_PROJECTION, LOCAL_PROJECTION)},
        "outcomes_read": False, "encoder_imported": False, "project_features_extracted": 0, "models_fit": 0})
    print("SpliceBERT downstream metadata plan PASS; no encoder import, extraction or fitting", flush=True)


def freeze_production():
    """Root invokes only after synthetic backend PASS, then commits this freeze."""
    from src.generalization_20261007.verify import preservation
    preservation(); backend = backend_check(); projections()
    assert not (OUT / "feature_production_manifest.json").exists()
    assert not any((OUT / track / "fits").exists() for track in TRACKS)
    assert readj(OUT / "plan_receipt.json")["status"] == readj(OUT / "synthetic_tests_receipt_final_review.json")["status"] == "PASS"
    tests = readj(OUT / "synthetic_tests_receipt_final_review.json")
    for name, expected in tests["source_hashes"].items():
        assert sha256(SRC / name) == expected, name
    paths = [path for folder in (SRC, REP, OUT) for path in folder.glob("*") if path.is_file()]
    paths += [GLOBAL_PROJECTION, LOCAL_PROJECTION, BACKEND_RECEIPT, IR, IR.with_suffix(".bin"),
        BACK_OUT / "backend_preparation_manifest.json", BACK_OUT / "resource_audit.json", BACK_OUT / "feature_proposal.json",
        NEXT_OUT / "feature_production_manifest.json", NEXT_OUT / "short_feature_receipt.json", NEXT_OUT / "bert_runtime_integrity.json",
        NEXT_ART / "sequence_inventory.csv.gz", NEXT_ART / "encoded_sequence_inventory.csv.gz",
        ROOT / "artifacts/generalization_20261007/reporter_context_metadata.json",
        ROOT / "src/generalization_next_20261007/route_structure.py", ROOT / "src/generalization_next_20261007/common.py",
        ROOT / "src/generalization_splicebert_20261007/features.py", ROOT / "src/generalization_splicebert_20261007/backend_probe.py",
        ROOT / "src/generalization_splicebert_20261007/resources.py", ROOT / "src/generalization_20261007/common.py"]
    paths += [ROOT / name for name in readj(BACK_OUT / "backend_preparation_manifest.json")["files"]]
    jsave(OUT / "feature_production_manifest.json", {"status": "FROZEN_SPLICEBERT_FEATURE_PRODUCTION",
        "files": {path.relative_to(ROOT).as_posix(): sha256(path) for path in sorted(set(paths))},
        "rows": 26258, "unique_alleles": 18220, "columns": 256, "threads": THREADS, "batch_size": BATCH,
        "native_IR_synthetic_parity_required_and_passed": True, "backend_receipt_sha256": sha256(BACKEND_RECEIPT),
        "fresh_3GiB_RAM_and_5GiB_disk_required": True, "root_start_required": True,
        "no_supervised_fit_authorized": True, "SRLE46nt_OOD": True, "independent_confirmation": False})
    print("SpliceBERT feature-production freeze written; root commits before --root-start", flush=True)


if __name__ == "__main__":
    assert sys.argv[1:] in (["plan"], ["freeze-production"])
    (plan if sys.argv[1] == "plan" else freeze_production)()
