"""Additive post-production cache certification; never retrospective proof.

Only the committed encoded sequence inventory is read. The original cache
producer remains frozen. A new immutable index certifies the bytes observed by
this audit, with predetermined exact fresh-fold checks on 32 alleles.
"""
from __future__ import annotations

from pathlib import Path
from collections import Counter
import csv
import gzip
import hashlib
import json
import os
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "artifacts/generalization_next_20261007"
OUT = ROOT / "results/generalization_next_20261007"
INVENTORY = ART / "encoded_sequence_inventory.csv.gz"
CONFIG = OUT / "structure_config_v2.json"
INDEX = ART / "structure_postproduction_sha256_index.json"
RECEIPT = OUT / "structure_postproduction_audit_receipt.json"
TEST_RECEIPT = OUT / "structure_integrity_tests_receipt.json"
PROTOCOL = ROOT / "reports/generalization_next_20261007/structure_integrity_audit_protocol.md"
TEST_SOURCE = Path(__file__).with_name("test_structure_integrity_audit.py")
LENGTHS = (46, 150, 190, 260)
EXPECTED_COUNTS = {46: 742, 150: 9318, 190: 3991, 260: 4169}
INVENTORY_COLUMNS = ("intervention_id", "dataset", "biological_component", "parent_context_id",
                     "parent_sequence", "mutant_sequence")
CACHE_FIELDS = {"sequence", "sequence_sha256", "config_sha256", "unpaired", "entropy", "distance", "energy"}


def file_hash(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def sequence_hash(sequence):
    return hashlib.sha256(sequence.encode("ascii")).hexdigest()


def select_refolds(sequences, per_length=8):
    """Predetermined first sequence hashes, separately within each length."""
    assert isinstance(per_length, int) and per_length > 0
    result = []
    unique = set(sequences)
    for length in LENGTHS:
        ordered = sorted((sequence for sequence in unique if len(sequence) == length),
                         key=sequence_hash)
        assert len(ordered) >= per_length
        result.extend(ordered[:per_length])
    return result


def validate_npz(path, sequence, config_sha256):
    """Independently inspect the frozen producer's numeric and identity schema."""
    from .route_structure import np
    with np.load(path, allow_pickle=False) as data:
        assert set(data.files) == CACHE_FIELDS
        for key, expected in (("sequence", sequence), ("sequence_sha256", sequence_hash(sequence)),
                              ("config_sha256", config_sha256)):
            assert data[key].shape == () and str(data[key]) == expected, key
        arrays = tuple(data[key].copy() for key in ("unpaired", "entropy", "distance"))
        assert data["energy"].shape == () and data["energy"].dtype == np.float64
        energy = float(data["energy"])
    assert np.isfinite(energy)
    for array in arrays:
        assert array.shape == (len(sequence),) and array.dtype == np.float64
        assert np.isfinite(array).all()
    unpaired, entropy, distance = arrays
    assert ((unpaired >= 0) & (unpaired <= 1)).all()
    assert (entropy >= -1e-10).all()
    assert ((distance >= -1e-10) & (distance <= 1 + 1e-10)).all()
    return (*arrays, energy)


def exact_comparison(cached, fresh):
    from .route_structure import np
    assert len(cached) == len(fresh) == 4
    for name, left, right in zip(("unpaired", "entropy", "distance"), cached[:3], fresh[:3]):
        assert np.array_equal(left, right), "Fresh fold differs exactly for " + name
    assert cached[3] == fresh[3], "Fresh ensemble energy differs exactly"


def validate_entry(entry, expected_path=None):
    """Recheck actual bytes against the new index; detects later alterations."""
    path = (ROOT / entry["path"]).resolve()
    assert path.is_relative_to((ART / "structure_ensemble_cache").resolve())
    if expected_path is not None:
        assert path == Path(expected_path).resolve()
    assert path.stat().st_size == entry["bytes"]
    assert file_hash(path) == entry["sha256"], "Post-audit structure bytes changed: " + str(path)


def committed(path):
    relative = Path(path).relative_to(ROOT).as_posix()
    value = subprocess.check_output(["git", "show", "HEAD:" + relative], cwd=ROOT)
    assert value == Path(path).read_bytes(), "Commit additive audit artifact before execution: " + relative


def run():
    # Imports occur only after the resource thread setting has been checked.
    assert os.environ.get("OPENBLAS_NUM_THREADS") == os.environ.get("OMP_NUM_THREADS") == "1"
    from .common import production_check, readj, jsave
    from . import route_structure as route
    from .structure_cache import cache_path
    production = production_check()
    for path in (Path(__file__), TEST_SOURCE, PROTOCOL, TEST_RECEIPT):
        committed(path)
    tests = readj(TEST_RECEIPT)
    assert tests["status"] == "PASS"
    assert tests["audit_source_sha256"] == file_hash(__file__)
    assert tests["tests_source_sha256"] == file_hash(TEST_SOURCE)
    source_receipt_path = OUT / "structure_cache_production_receipt.json"
    source_receipt = readj(source_receipt_path)
    assert source_receipt["status"] == "PASS" and source_receipt["outcomes_used"] is False
    assert source_receipt["unique_alleles"] == 18220
    assert source_receipt["protocol_sha256"] == file_hash(OUT / "feature_production_manifest.json")
    config_sha = file_hash(CONFIG)
    assert source_receipt["config_sha256"] == config_sha
    assert route.SPEC == readj(CONFIG)
    relative_inventory = INVENTORY.relative_to(ROOT).as_posix()
    assert production["files"][relative_inventory] == file_hash(INVENTORY)
    assert not INDEX.exists() and not RECEIPT.exists(), "Preserve prior audit/index; do not overwrite"

    sequences, row_ids = set(), []
    with gzip.open(INVENTORY, "rt", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert tuple(reader.fieldnames) == INVENTORY_COLUMNS
        studies = set()
        for row in reader:
            row_ids.append(row["intervention_id"]); studies.add(row["dataset"])
            parent, mutant = row["parent_sequence"], row["mutant_sequence"]
            assert parent != mutant and len(parent) == len(mutant)
            assert set(parent) <= set("ACGT") and set(mutant) <= set("ACGT")
            sequences.update((parent, mutant))
    assert len(row_ids) == len(set(row_ids)) == 26258
    assert studies == set(route.STUDIES)
    assert len(sequences) == 18220 and dict(Counter(map(len, sequences))) == EXPECTED_COUNTS
    samples = select_refolds(sequences)
    ordered = sorted(sequences, key=sequence_hash)
    started = time.perf_counter(); records = []
    for index, sequence in enumerate(ordered):
        path = cache_path(sequence)
        assert path.resolve().is_relative_to((ART / "structure_ensemble_cache").resolve())
        before = file_hash(path)
        validate_npz(path, sequence, config_sha)
        assert file_hash(path) == before, "Cache changed during identity/probability audit"
        records.append({"sequence_sha256": sequence_hash(sequence), "length_nt": len(sequence),
                        "path": path.relative_to(ROOT).as_posix(), "sha256": before,
                        "bytes": path.stat().st_size})
        if (index + 1) % 1000 == 0 or index + 1 == len(ordered):
            print("structure audit", index + 1, "of", len(ordered), "cache identities checked", flush=True)

    by_hash = {entry["sequence_sha256"]: entry for entry in records}
    refold_records = []
    for index, sequence in enumerate(samples):
        entry = by_hash[sequence_hash(sequence)]
        validate_entry(entry, cache_path(sequence))
        cached = validate_npz(cache_path(sequence), sequence, config_sha)
        # Bypass the LRU cache explicitly: only the frozen physics function runs.
        fresh = route.ensemble.__wrapped__(sequence)
        exact_comparison(cached, fresh)
        validate_entry(entry, cache_path(sequence))
        refold_records.append({"sequence_sha256": sequence_hash(sequence), "length_nt": len(sequence),
                               "vectors_exactly_equal": True, "energy_exactly_equal": True})
        print("structure audit fresh fold", index + 1, "of", len(samples), "PASS", flush=True)
    # The index is not published if a file changed while the fresh checks ran.
    for entry in records:
        validate_entry(entry)
    index_payload = {"status": "PASS", "scope": "POST_PRODUCTION_OBSERVED_BYTES_INDEX",
                     "config_sha256": config_sha, "inventory_sha256": file_hash(INVENTORY),
                     "source_production_receipt_sha256": file_hash(source_receipt_path),
                     "alleles": records}
    jsave(INDEX, index_payload)
    jsave(RECEIPT, {"status": "PASS", "scope": "POST_PRODUCTION_IDENTITY_NUMERIC_AND_SAMPLED_FRESH_FOLD_AUDIT",
                    "unique_alleles": len(records), "rows": len(row_ids),
                    "row_ids_sha256": hashlib.sha256("|".join(row_ids).encode()).hexdigest(),
                    "allele_counts_by_length": EXPECTED_COUNTS, "fresh_fold_count": len(samples),
                    "fresh_fold_selection": "First8 ascending sequence SHA256 independently within46/150/190/260nt",
                    "fresh_folds": refold_records, "index_path": INDEX.relative_to(ROOT).as_posix(),
                    "index_sha256": file_hash(INDEX), "config_sha256": config_sha,
                    "inventory_sha256": file_hash(INVENTORY),
                    "source_production_receipt_sha256": file_hash(source_receipt_path),
                    "audit_source_sha256": file_hash(__file__), "tests_receipt_sha256": file_hash(TEST_RECEIPT),
                    "protocol_sha256": file_hash(PROTOCOL), "elapsed_seconds": time.perf_counter() - started,
                    "workers": 1, "numerical_threads": 1, "outcomes_used": False, "models_fit": 0,
                    "existing_cache_entries_modified": False, "retrospective_creation_proof": False,
                    "limitation": "No producer creation sidecars existed. This index pins bytes observed now; 32 exact fresh folds do not prove historical integrity or refold all18220 alleles."})
    print("Post-production structure audit PASS", flush=True)


if __name__ == "__main__":
    run()
