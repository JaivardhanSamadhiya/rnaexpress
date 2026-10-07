"""Outcome-free row/sign plan now; fixed-source-array admission after PASS."""
from .common import *
from .routes import endpoint_sign, ENDPOINT_SIGNS, configurations
import sys


def plan():
    from src.generalization_20261007.verify import preservation
    from src.generalization_next_20261007.common import production_check
    preservation(); production_check()
    assert not any((OUT / track / "fits").exists() for track in TRACKS)
    frame = pd.read_csv(CORE, usecols=ROW_COLUMNS, low_memory=False)[ROW_COLUMNS]
    original = pd.read_csv(NEXT_ART / "sequence_inventory.csv.gz", low_memory=False)
    receipt = readj(NEXT_OUT / "short_feature_receipt.json")
    assert receipt["status"] == "PASS"
    for name, expected in receipt["files"].items():
        assert sha256(ROOT / name) == expected, name
    assert len(frame) == 26258 and frame.intervention_id.is_unique and set(frame.dataset) == set(STUDIES)
    pd.testing.assert_frame_equal(frame[IDENTITY], original[IDENTITY])
    assert rowhash(frame) == receipt["row_ids_sha256"]
    frame["routing_sign"] = endpoint_sign(frame)
    csvsave(OUT / "row_index.csv.gz", frame, True)
    jsave(OUT / "plan_receipt.json", {"status":"PASS", "rows":len(frame), "row_ids_sha256":rowhash(frame),
        "original_row_identity_sha256":identity_hash(frame), "core_sha256":sha256(CORE),
        "endpoint_rows":frame.groupby("endpoint_class").size().to_dict(), "endpoint_signs":ENDPOINT_SIGNS,
        "source_arrays":{track:(NEXT_ART / (track + "_model_features.npz")).relative_to(ROOT).as_posix() for track in TRACKS},
        "shapes":SHAPES, "configurations":{track:configurations(track) for track in TRACKS},
        "observed_data_followup":True, "new_feature_extraction":False, "outcomes_loaded":False,
        "fitting_started":False, "prefit_freeze_ready":False})
    print("Alignment row/sign plan prepared without outcomes, arrays or fits", flush=True)


def inputs():
    assert not any((OUT / track / "fits").exists() for track in TRACKS)
    source = source_arrays_check()
    plan_receipt = readj(OUT / "plan_receipt.json")
    rows = pd.read_csv(OUT / "row_index.csv.gz", low_memory=False)
    assert identity_hash(rows) == plan_receipt["original_row_identity_sha256"]
    source_rows = pd.read_csv(NEXT_OUT / "row_index.csv.gz", low_memory=False)
    columns = ["intervention_id", "dataset", "parent_context_id", "biological_component"]
    pd.testing.assert_frame_equal(rows[columns], source_rows[columns])
    for track in TRACKS:
        with np.load(NEXT_ART / (track + "_model_features.npz"), allow_pickle=False) as archive:
            matrix = archive["features"]
            assert matrix.shape == (26258, SHAPES[track]) and np.isfinite(matrix).all()
        del matrix
    jsave(OUT / "input_receipt.json", {"status":"PASS", "rows":26258, "dimensions":SHAPES,
        "source_files":dict(source["files"]), "source_prepare_receipt_sha256":sha256(NEXT_OUT / "prepare_receipt.json"),
        "original_row_identity_sha256":identity_hash(rows), "row_index_sha256":sha256(OUT / "row_index.csv.gz"),
        "arrays_identical_to_unflipped_next":True, "feature_extraction":False, "outcomes_loaded":False,
        "supervised_fits":0, "ready_for_separate_prefit_freeze":True})
    print("All six immutable source arrays admitted; no fits", flush=True)


if __name__ == "__main__":
    assert sys.argv[1:] in (["plan"], ["inputs"])
    plan() if sys.argv[1] == "plan" else inputs()
