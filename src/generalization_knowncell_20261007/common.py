"""Additive evaluation guards; no fitting or new feature production."""
from src.generalization_crosscell_20261007.common import (
    ROOT, np, pd, sha256, clean, readj, decisions, TRACKS, WIDTHS, META,
    CORE, FOLDS,
)
from pathlib import Path
import gzip, hashlib, json, subprocess

NS = "generalization_knowncell_20261007"
SRC, OUT, REP, ART = [ROOT / name / NS for name in ("src", "results", "reports", "artifacts")]
SOURCE_OUT = ROOT / "results/generalization_crosscell_20261007"
SOURCE_ART = ROOT / "artifacts/generalization_crosscell_20261007"
TASKS = {"CAD_known": ("CAD", "CAD_to_N2A"), "N2A_known": ("Neuro-2a", "N2A_to_CAD")}
INFORMED = ["structure", "bert", "combined"]
SEED = 20261007


def save(path, payload):
    path = Path(path).resolve()
    assert any(path.is_relative_to(p.resolve()) for p in (SRC, OUT, REP, ART))
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists(): assert path.read_bytes() == payload, "Preserve existing " + str(path)
    else: path.write_bytes(payload)


def jsave(path, data):
    save(path, (json.dumps(clean(data), indent=2, sort_keys=True, allow_nan=False) + "\n").encode())


def csvsave(path, frame, compressed=False):
    raw = frame.to_csv(index=False, lineterminator="\n").encode()
    save(path, gzip.compress(raw, mtime=0) if compressed else raw)


def rowhash(frame):
    return hashlib.sha256("|".join(frame.intervention_id).encode()).hexdigest()


def load(outcomes=False):
    # Explicit metadata only; never invoke legacy replicate/feature readers.
    original = pd.read_csv(CORE, usecols=META, low_memory=False)
    assert len(original) == 26258 and original.intervention_id.is_unique
    original["original_core_row"] = np.arange(len(original))
    frame = original[original.dataset.eq("mikl_gse173098")].reset_index(drop=True)
    assert len(frame) == 13781 and frame.biological_component.nunique() == 187
    assert set(frame.cell_type) == {"CAD", "Neuro-2a"} and set(frame.endpoint_class) == {"projection"}
    assert frame.groupby("biological_component").held_parent_fold.nunique().eq(1).all()
    assert frame.groupby("parent_context_id").cell_type.nunique().eq(1).all()
    if outcomes:
        keep = set(frame.original_core_row.astype(int) + 1)
        values = pd.read_csv(CORE, usecols=["intervention_id", "measured_delta"],
            low_memory=False, skiprows=lambda number: number > 0 and number not in keep)
        assert list(values.intervention_id) == list(frame.intervention_id)
        frame["measured_delta"] = values.measured_delta.to_numpy(float)
        assert np.isfinite(frame.measured_delta).all()
    return frame


def freeze_check():
    from src.generalization_crosscell_20261007.common import freeze_check as source_freeze
    source_freeze()
    path = OUT / "evaluation_manifest.json"; manifest = readj(path)
    assert manifest["status"] == "FROZEN_EVALUATION_KNOWN_CELL"
    for name, expected in manifest["files"].items(): assert sha256(ROOT / name) == expected, name
    assert subprocess.check_output(["git", "show", "HEAD:" + path.relative_to(ROOT).as_posix()], cwd=ROOT) == path.read_bytes()
    return manifest
