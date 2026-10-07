"""Immutable input and original-allele identity for factorial alignment."""
from src.generalization_20261007.common import ROOT, np, pd, sha256, clean, readj, decisions, summary, inner_regret
from pathlib import Path
import gzip, hashlib, json, subprocess

NS = "generalization_alignment_20261007"
SRC, OUT, REP, ART = [ROOT / folder / NS for folder in ("src", "results", "reports", "artifacts")]
NEXT_ART, NEXT_OUT = ROOT / "artifacts/generalization_next_20261007", ROOT / "results/generalization_next_20261007"
CORE = ROOT / "results/probabilistic_ranking_20260928/candidate_index.csv"
STUDIES = ["astrocyte_gse330741", "mikl_gse173098", "moffatt_gse334718", "srle"]
TRACKS = ["base", "raw", "structure", "lookup", "bert", "combined"]
SHAPES = {"base":246, "raw":251, "structure":262, "lookup":502, "bert":502, "combined":518}
IDENTITY = ["intervention_id", "dataset", "biological_component", "parent_context_id", "parent_sequence", "mutant_sequence"]
ROW_COLUMNS = IDENTITY + ["endpoint_class"]
SEED = 20261007


def save(path, payload):
    path = Path(path).resolve()
    assert any(path.is_relative_to(folder.resolve()) for folder in (SRC, OUT, REP, ART))
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == payload, "Preserve existing artifact " + str(path)
    else:
        path.write_bytes(payload)


def jsave(path, data):
    save(path, (json.dumps(clean(data), indent=2, sort_keys=True, allow_nan=False) + "\n").encode())


def csvsave(path, frame, compressed=False):
    value = frame.to_csv(index=False, lineterminator="\n").encode()
    save(path, gzip.compress(value, mtime=0) if compressed else value)


def rowhash(frame):
    return hashlib.sha256("|".join(frame.intervention_id).encode()).hexdigest()


def identity_hash(frame):
    payload = frame[ROW_COLUMNS].to_csv(index=False, lineterminator="\n").encode()
    return hashlib.sha256(payload).hexdigest()


def label_hash(values):
    return hashlib.sha256(np.asarray(values, dtype="<f8").tobytes()).hexdigest()


def load():
    # The fixed source arrays already exist: do not reopen historical replicate
    # or pair-evidence tables just to obtain the admitted mean-effect truth.
    fields = ROW_COLUMNS + ["measured_delta", "primary_eligible"]
    frame = pd.read_csv(CORE, usecols=fields, low_memory=False)[fields]
    assert len(frame) == 26258 and frame.intervention_id.is_unique and set(frame.dataset) == set(STUDIES)
    assert frame.primary_eligible.all() and np.isfinite(frame.measured_delta.to_numpy(float)).all()
    rows = pd.read_csv(OUT / "row_index.csv.gz", low_memory=False)
    pd.testing.assert_frame_equal(frame[ROW_COLUMNS].reset_index(drop=True), rows[ROW_COLUMNS])
    return frame


def source_arrays_check():
    from src.generalization_next_20261007.common import production_check
    production_check()
    for filename in ("structure_cache_production_receipt.json", "bert_features_receipt.json",
                     "assembly_integrity_receipt.json", "prepare_receipt.json"):
        assert readj(NEXT_OUT / filename)["status"] == "PASS", filename
    receipt = readj(NEXT_OUT / "prepare_receipt.json")
    assert receipt["rows"] == 26258 and receipt["shapes"] == SHAPES
    for track in TRACKS:
        path = NEXT_ART / (track + "_model_features.npz")
        assert sha256(path) == receipt["files"][path.relative_to(ROOT).as_posix()], track
    return receipt


def freeze_check():
    from src.generalization_20261007.verify import preservation
    preservation()
    path = OUT / "prefit_manifest.json"
    manifest = readj(path)
    assert manifest["status"] == "FROZEN_PREFIT_ALIGNMENT_FOLLOWUP"
    for name, expected in manifest["files"].items():
        assert sha256(ROOT / name) == expected, name
    committed = subprocess.check_output(["git", "show", "HEAD:" + path.relative_to(ROOT).as_posix()], cwd=ROOT)
    assert committed == path.read_bytes(), "Root commits alignment freeze before fitting"
    return manifest
