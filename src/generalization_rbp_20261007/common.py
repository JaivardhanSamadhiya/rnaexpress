"""Disjoint namespace guards and frozen input/row identity for RBP transfer."""
from src.generalization_20261007.common import (
    ROOT, np, pd, sha256, clean, readj, decisions, summary, inner_regret,
)
from pathlib import Path
import gzip, hashlib, io, json, subprocess

NS = "generalization_rbp_20261007"
SRC, OUT, REP, ART = [ROOT / folder / NS for folder in ("src", "results", "reports", "artifacts")]
NEXT_ART = ROOT / "artifacts/generalization_next_20261007"
NEXT_OUT = ROOT / "results/generalization_next_20261007"
STUDIES = ["astrocyte_gse330741", "mikl_gse173098", "moffatt_gse334718", "srle"]
TRACKS = ["base", "raw", "access"]
SEED = 20261007
INVENTORY_COLUMNS = ["intervention_id", "dataset", "biological_component", "parent_context_id",
                     "parent_sequence", "mutant_sequence"]


def save(path, payload):
    path = Path(path).resolve()
    assert any(path.is_relative_to(folder) for folder in (SRC, OUT, REP, ART))
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == payload, "Preserve existing artifact " + str(path)
    else:
        path.write_bytes(payload)


def jsave(path, data):
    save(path, (json.dumps(clean(data), indent=2, sort_keys=True, allow_nan=False) + "\n").encode())


def csvsave(path, frame, compressed=False):
    payload = frame.to_csv(index=False, lineterminator="\n").encode()
    save(path, gzip.compress(payload, mtime=0) if compressed else payload)


def matrixsave(path, matrix):
    assert np.isfinite(matrix).all()
    buffer = io.BytesIO(); np.savez_compressed(buffer, features=np.asarray(matrix))
    save(path, buffer.getvalue())


def rowhash(frame):
    return hashlib.sha256("|".join(frame.intervention_id).encode()).hexdigest()


def check_manifest(filename, committed=True):
    from src.generalization_20261007.verify import preservation
    from src.generalization_next_20261007.common import production_check as next_production_check
    preservation(); next_production_check()
    path = OUT / filename
    manifest = readj(path)
    for name, checksum in manifest["files"].items():
        assert sha256(ROOT / name) == checksum, name
    if committed:
        content = subprocess.check_output(["git", "show", "HEAD:" + path.relative_to(ROOT).as_posix()], cwd=ROOT)
        assert content == path.read_bytes(), "Commit separate RBP manifest before execution"
    return manifest


def production_check():
    return check_manifest("feature_production_manifest.json")


def freeze_check():
    return check_manifest("prefit_manifest.json")


def inventories():
    receipt = readj(NEXT_OUT / "short_feature_receipt.json")
    assert receipt["status"] == "PASS"
    for name, checksum in receipt["files"].items():
        assert sha256(ROOT / name) == checksum, name
    original, encoded = [pd.read_csv(NEXT_ART / name, low_memory=False)
                         for name in ("sequence_inventory.csv.gz", "encoded_sequence_inventory.csv.gz")]
    assert list(original) == list(encoded) == INVENTORY_COLUMNS
    assert len(original) == len(encoded) == 26258
    assert not original.intervention_id.duplicated().any()
    pd.testing.assert_frame_equal(original[INVENTORY_COLUMNS[:4]], encoded[INVENTORY_COLUMNS[:4]])
    assert rowhash(original) == receipt["row_ids_sha256"]
    assert set(original.dataset) == set(STUDIES)
    assert all(set(s) <= set("ACGT") for s in encoded.parent_sequence)
    assert all(set(s) <= set("ACGT") for s in encoded.mutant_sequence)
    return original, encoded


def load():
    from src.generalization_20261007.common import load as prior_load
    frame, _ = prior_load()
    original, _ = inventories()
    assert len(frame) == len(original) and rowhash(frame) == rowhash(original)
    pd.testing.assert_frame_equal(frame[INVENTORY_COLUMNS].reset_index(drop=True), original)
    return frame
