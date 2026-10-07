"""Outcome-free identities and immutable namespace writes."""
from pathlib import Path
import gzip
import hashlib
import io
import json
import subprocess

from src.generalization_20261007.common import ROOT, np, pd, sha256, clean, readj
from src.generalization_20261007.common import decisions, summary, inner_regret

NS = "generalization_splicebert_downstream_20261007"
SRC, OUT, REP, ART = [ROOT / folder / NS for folder in ("src", "results", "reports", "artifacts")]
NEXT_ART = ROOT / "artifacts/generalization_next_20261007"
NEXT_OUT = ROOT / "results/generalization_next_20261007"
BACK_ART = ROOT / "artifacts/generalization_splicebert_20261007"
BACK_OUT = ROOT / "results/generalization_splicebert_20261007"
IDENTITY = ["intervention_id", "dataset", "biological_component", "parent_context_id", "parent_sequence", "mutant_sequence"]
STUDIES = ["astrocyte_gse330741", "mikl_gse173098", "moffatt_gse334718", "srle"]
TRACKS = ["base", "raw", "structure", "lookup", "splicebert", "combined"]
SHAPES = dict(zip(TRACKS, [246, 251, 262, 502, 502, 518]))
CONTROL_TRACKS = ["base", "raw", "structure"]
CORE = ROOT / "results/probabilistic_ranking_20260928/candidate_index.csv"
SEED = 20261007


def save(path, payload):
    path = Path(path).resolve()
    assert any(path.is_relative_to(root.resolve()) for root in (SRC, OUT, REP, ART))
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == payload, "Preserve existing artifact: " + str(path)
    else:
        with path.open("xb") as output:
            output.write(payload)


def jsave(path, data):
    save(path, (json.dumps(clean(data), indent=2, sort_keys=True, allow_nan=False) + "\n").encode())


def csvsave(path, frame, compressed=False):
    data = frame.to_csv(index=False, lineterminator="\n").encode()
    save(path, gzip.compress(data, mtime=0) if compressed else data)


def matrixsave(path, matrix):
    assert np.isfinite(matrix).all()
    buffer = io.BytesIO()
    np.savez_compressed(buffer, features=np.asarray(matrix))
    save(path, buffer.getvalue())


def row_identity(frame):
    payload = "\n".join(f"{i}\t{p}\t{m}" for i, p, m in zip(frame.intervention_id, frame.parent_sequence, frame.mutant_sequence))
    return hashlib.sha256(payload.encode()).hexdigest()


def metadata_identity(frame):
    return hashlib.sha256(frame[IDENTITY].to_csv(index=False, lineterminator="\n").encode()).hexdigest()


def committed(path):
    path = Path(path)
    content = subprocess.check_output(["git", "show", "HEAD:" + path.relative_to(ROOT).as_posix()], cwd=ROOT)
    assert content == path.read_bytes(), "Root must commit the exact freeze before execution"


def manifest_check(filename, status):
    from src.generalization_20261007.verify import preservation
    preservation()
    path = OUT / filename
    committed(path)
    receipt = readj(path)
    assert receipt["status"] == status
    for name, expected in receipt["files"].items():
        target = (ROOT / name).resolve()
        assert target.is_relative_to(ROOT.resolve())
        assert sha256(target) == expected, name
    return receipt


def production_check():
    return manifest_check("feature_production_manifest.json", "FROZEN_SPLICEBERT_FEATURE_PRODUCTION")


def freeze_check():
    return manifest_check("prefit_manifest.json", "FROZEN_PREFIT_SPLICEBERT_FOLLOWUP")


def rowhash(frame):
    return hashlib.sha256("|".join(frame.intervention_id).encode()).hexdigest()


def label_hash(values):
    return hashlib.sha256(np.asarray(values, dtype="<f8").tobytes()).hexdigest()


def matrix_hash(matrix):
    return hashlib.sha256(np.ascontiguousarray(matrix, dtype="<f8").tobytes()).hexdigest()


def load():
    """Exact admitted core parser; no historical replicate/auxiliary tables."""
    fields = IDENTITY + ["endpoint_class", "measured_delta", "primary_eligible"]
    frame = pd.read_csv(CORE, usecols=fields, low_memory=False)[fields]
    assert len(frame) == 26258 and frame.intervention_id.is_unique
    assert set(frame.dataset) == set(STUDIES) and frame.primary_eligible.all()
    assert np.isfinite(frame.measured_delta.to_numpy(float)).all()
    rows = pd.read_csv(OUT / "row_index.csv.gz", usecols=IDENTITY)[IDENTITY]
    pd.testing.assert_frame_equal(frame[IDENTITY], rows)
    return frame


def input_check():
    receipt = readj(OUT / "input_receipt.json")
    assert receipt["status"] == "PASS" and receipt["rows"] == 26258 and receipt["shapes"] == SHAPES
    assert receipt["production_manifest_sha256"] == sha256(OUT / "feature_production_manifest.json")
    assert receipt["features_receipt_sha256"] == sha256(OUT / "features_receipt.json")
    assert receipt["source_control_prefit_manifest_sha256"] == sha256(NEXT_OUT / "prefit_manifest.json")
    assert set(receipt["feature_paths"]) == set(TRACKS)
    for track, name in receipt["feature_paths"].items():
        path = (ROOT / name).resolve()
        assert path.is_relative_to(ROOT.resolve()) and sha256(path) == receipt["files"][name], track
    assert receipt["row_index_sha256"] == sha256(OUT / "row_index.csv.gz")
    return receipt


def sequence_frames():
    """Read sequence/identity columns only, never the supervised core table."""
    from src.generalization_next_20261007.route_structure import encoded_pair
    from src.generalization_next_20261007.common import production_check as prior_production
    prior_production()
    short = readj(NEXT_OUT / "short_feature_receipt.json")
    assert short["status"] == "PASS" and short["rows"] == 26258
    for filename in ("sequence_inventory.csv.gz", "encoded_sequence_inventory.csv.gz"):
        path = NEXT_ART / filename
        assert sha256(path) == short["files"][path.relative_to(ROOT).as_posix()]
    original = pd.read_csv(NEXT_ART / "sequence_inventory.csv.gz", usecols=IDENTITY)[IDENTITY]
    encoded = pd.read_csv(NEXT_ART / "encoded_sequence_inventory.csv.gz", usecols=IDENTITY)[IDENTITY]
    assert len(original) == len(encoded) == 26258 and original.intervention_id.is_unique
    assert set(original.dataset) == set(STUDIES)
    pd.testing.assert_frame_equal(original[IDENTITY[:4]], encoded[IDENTITY[:4]])
    pairs = [encoded_pair(parent, mutant, study) for parent, mutant, study in zip(original.parent_sequence, original.mutant_sequence, original.dataset)]
    assert [pair[0] for pair in pairs] == encoded.parent_sequence.tolist()
    assert [pair[1] for pair in pairs] == encoded.mutant_sequence.tolist()
    assert all(len(parent) == len(mutant) and set(parent + mutant) <= set("ACGT") for parent, mutant in zip(encoded.parent_sequence, encoded.mutant_sequence))
    assert set(encoded.loc[encoded.dataset.eq("srle"), "parent_sequence"].str.len()) == {46}
    assert set(encoded.loc[~encoded.dataset.eq("srle"), "parent_sequence"].str.len()) == {150, 190, 260}
    return original, encoded
