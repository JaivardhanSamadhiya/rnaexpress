"""Outcome-free assembly with shared immutable baseline/structure controls."""
from .common import *


def source_controls():
    reference_path = NEXT_OUT / "prefit_manifest.json"
    committed(reference_path)
    reference = readj(reference_path)
    for filename in ("structure_cache_production_receipt.json", "bert_features_receipt.json", "assembly_integrity_receipt.json", "prepare_receipt.json", "structure_postproduction_audit_receipt.json"):
        assert readj(NEXT_OUT / filename)["status"] == "PASS", filename
    receipt = readj(NEXT_OUT / "prepare_receipt.json")
    actual = {(NEXT_OUT / "prepare_receipt.json").relative_to(ROOT).as_posix(): sha256(NEXT_OUT / "prepare_receipt.json")}
    paths = {}
    for track in CONTROL_TRACKS:
        path = NEXT_ART / (track + "_model_features.npz")
        assert sha256(path) == receipt["files"][path.relative_to(ROOT).as_posix()]
        actual[path.relative_to(ROOT).as_posix()] = sha256(path)
        paths[track] = path
    validate_control_reference(reference, actual)
    return paths


def validate_control_reference(reference, actual):
    """Pure selected-byte binding, after the caller verifies committed JSON."""
    assert reference["status"] == "FROZEN_PREFIT"
    required = {(NEXT_OUT / "prepare_receipt.json").relative_to(ROOT).as_posix()}
    required |= {(NEXT_ART / (track + "_model_features.npz")).relative_to(ROOT).as_posix() for track in CONTROL_TRACKS}
    assert set(actual) == required
    for name, expected in actual.items():
        assert reference["files"][name] == expected, "Reused controls/receipt differ from original committed prefit freeze: " + name


def checked_block(path, expected_sha, columns):
    assert sha256(path) == expected_sha
    with np.load(path, allow_pickle=False) as data:
        assert data.files == ["features"]
        values = data["features"].copy()
    assert values.shape == (26258, columns) and np.isfinite(values).all()
    return values


def run():
    production_check()
    assert not (OUT / "input_receipt.json").exists()
    assert not any((OUT / track / "fits").exists() for track in TRACKS)
    original, encoded = sequence_frames()
    rows = pd.read_csv(OUT / "row_index.csv.gz", usecols=IDENTITY)[IDENTITY]
    pd.testing.assert_frame_equal(original, rows)
    receipt = readj(OUT / "features_receipt.json")
    assert receipt["status"] == "PASS" and receipt["production_manifest_sha256"] == sha256(OUT / "feature_production_manifest.json")
    assert receipt["encoded_row_identity_sha256"] == row_identity(encoded)
    assert receipt["original_metadata_identity_sha256"] == metadata_identity(original)
    assert receipt["cache_index_sha256"] == sha256(ART / "compact_cache/index.json")
    for shard in receipt["compact_shards"]:
        assert sha256(ROOT / shard["path"]) == shard["sha256"]
        assert sha256(ROOT / shard["sidecar_path"]) == shard["sidecar_sha256"]
        sidecar = readj(ROOT / shard["sidecar_path"])
        assert sidecar["sha256"] == shard["sha256"] and sidecar["spec_sha256"] == receipt["spec_sha256"]
    paths = source_controls()
    previous_rows = pd.read_csv(NEXT_OUT / "row_index.csv.gz")
    pd.testing.assert_frame_equal(original[IDENTITY[:4]], previous_rows[IDENTITY[:4]])
    previous = readj(NEXT_OUT / "prepare_receipt.json")
    base = checked_block(paths["base"], previous["files"][paths["base"].relative_to(ROOT).as_posix()], 246)
    structured = checked_block(paths["structure"], previous["files"][paths["structure"].relative_to(ROOT).as_posix()], 262)
    np.testing.assert_array_equal(structured[:, :246], base)
    lookup = checked_block(ART / "lookup_features.npz", receipt["lookup_features_sha256"], 256)
    splicebert = checked_block(ART / "splicebert_features.npz", receipt["splicebert_features_sha256"], 256)
    for track, matrix in {"lookup": np.column_stack((base, lookup)), "splicebert": np.column_stack((base, splicebert)), "combined": np.column_stack((structured, splicebert))}.items():
        path = ART / (track + "_model_features.npz")
        assert matrix.shape == (26258, SHAPES[track])
        matrixsave(path, matrix); paths[track] = path
    # Read/hash every shared control now; do not copy large matrices unnecessarily.
    for track in CONTROL_TRACKS:
        checked_block(paths[track], previous["files"][paths[track].relative_to(ROOT).as_posix()], SHAPES[track])
    jsave(OUT / "input_receipt.json", {"status": "PASS", "rows": 26258, "shapes": SHAPES,
        "encoded_row_identity_sha256": row_identity(encoded), "original_metadata_identity_sha256": metadata_identity(original),
        "row_index_sha256": sha256(OUT / "row_index.csv.gz"), "production_manifest_sha256": sha256(OUT / "feature_production_manifest.json"),
        "source_control_prefit_manifest_sha256": sha256(NEXT_OUT / "prefit_manifest.json"),
        "features_receipt_sha256": sha256(OUT / "features_receipt.json"), "source_controls_byte_identical": True,
        "feature_paths": {track: path.relative_to(ROOT).as_posix() for track, path in paths.items()},
        "files": {path.relative_to(ROOT).as_posix(): sha256(path) for path in paths.values()},
        "outcomes_read": False, "models_fit": 0})
    print("SpliceBERT fixed six-track inputs assembled; no outcomes or fitting", flush=True)


if __name__ == "__main__":
    run()
