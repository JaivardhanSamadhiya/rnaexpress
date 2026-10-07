"""Guarded sequence-only raw/accessibility allele scoring and matrix assembly."""
from .common import *
from .projection import load_projections
from .scoring import load_groups, scan
import os, sys, time


def sequence_hash(sequence):
    return hashlib.sha256(sequence.encode("ascii")).hexdigest()


def positions_key(positions):
    return ",".join(str(int(position)) for position in positions)


def request_hash(position_sets):
    keys = [positions_key(positions) for positions in position_sets]
    return hashlib.sha256(json.dumps(keys, separators=(",", ":")).encode()).hexdigest()


def creation_receipt(payload, sequence, position_sets, mode, manifest_sha256):
    return {"npz_sha256": hashlib.sha256(payload).hexdigest(),
            "sequence_sha256": sequence_hash(sequence), "request_sha256": request_hash(position_sets),
            "mode": mode, "production_manifest_sha256": manifest_sha256,
            "role": "IMMUTABLE_CACHE_CREATION_RECEIPT_NOT_RECONSTRUCTED_FROM_RESUME"}


def validate_creation_bytes(payload, receipt, sequence, position_sets, mode, manifest_sha256):
    assert receipt == creation_receipt(payload, sequence, position_sets, mode, manifest_sha256), "Cache creation digest/identity changed"


def requests(encoded):
    result = {}
    row_positions = []
    for parent, mutant in zip(encoded.parent_sequence, encoded.mutant_sequence):
        assert len(parent) == len(mutant)
        positions = tuple(i for i, (a, b) in enumerate(zip(parent, mutant)) if a != b)
        assert positions, "Original candidate must be an actual aligned substitution"
        row_positions.append(positions)
        for sequence in (parent, mutant):
            result.setdefault(sequence, set()).add(positions)
    return {sequence: sorted(values) for sequence, values in result.items()}, row_positions


def pooled_blocks(blocks, length, positions, unpaired):
    """Pool existing scans without rescanning a shared parent for every edit."""
    positions = np.asarray(positions, int)
    assert positions.ndim == 1 and ((positions >= 0) & (positions < length)).all()
    unpaired = np.asarray(unpaired, float)
    assert unpaired.shape == (length,) and np.isfinite(unpaired).all()
    assert ((unpaired >= 0) & (unpaired <= 1)).all()
    prefix = np.r_[0., np.cumsum(unpaired)]
    result = np.zeros((421, 4))
    for width, indices, values in blocks:
        count = values.shape[1]
        if not count:
            continue
        starts = np.arange(count)
        weights = (prefix[starts + width] - prefix[starts]) / width
        weighted = values * weights[None]
        affected = np.any((starts[:, None] <= positions[None]) &
                          (positions[None] < (starts + width)[:, None]), axis=1)
        result[indices, 0] = weighted.mean(1)
        result[indices, 1] = weighted.max(1)
        if affected.any():
            result[indices, 2] = weighted[:, affected].mean(1)
            result[indices, 3] = weighted[:, affected].max(1)
    return result


def cache_path(sequence, mode):
    assert mode in ("raw", "access")
    stamp = sha256(OUT / "feature_production_manifest.json")
    checksum = sequence_hash(sequence)
    return ART / ("allele_cache_" + mode) / stamp / checksum[:2] / (checksum + ".npz")


def structure_probability(sequence):
    from src.generalization_next_20261007.structure_cache import cache_path as structure_path, validate_cached
    from src.generalization_next_20261007.common import production_check as next_check
    # The source cache requires a completed PASS production receipt; this
    # function validates and reads probabilities, and never refolds an allele.
    receipt = readj(NEXT_OUT / "structure_cache_production_receipt.json")
    assert receipt["status"] == "PASS" and receipt["outcomes_used"] is False
    assert receipt["config_sha256"] == sha256(NEXT_OUT / "structure_config_v2.json")
    path = structure_path(sequence)
    probability = validate_cached(sequence, path)[0]
    return probability, sha256(path), path.relative_to(ROOT).as_posix()


def validate_cached(sequence, position_sets, mode, path=None, new_creation_receipt=None):
    path = cache_path(sequence, mode) if path is None else Path(path)
    payload = path.read_bytes()
    receipt_path = path.with_suffix(".json")
    if new_creation_receipt is None:
        assert receipt_path.exists(), "Preserve orphan cache without creation receipt " + str(path)
        receipt = readj(receipt_path)
    else:
        assert path.name.endswith(".pending.npz"), "Creation override applies only to unpublished pending file"
        receipt = new_creation_receipt
    validate_creation_bytes(payload, receipt, sequence, position_sets, mode, sha256(OUT / "feature_production_manifest.json"))
    with np.load(io.BytesIO(payload), allow_pickle=False) as data:
        assert str(data["sequence"]) == sequence
        assert str(data["sequence_sha256"]) == sequence_hash(sequence)
        assert str(data["mode"]) == mode
        assert str(data["production_manifest_sha256"]) == sha256(OUT / "feature_production_manifest.json")
        keys = data["positions_keys"].tolist()
        assert keys == [positions_key(positions) for positions in position_sets]
        global_score = data["global_projected"].copy()
        local_score = data["affected_projected"].copy()
        source_hash, source_path = str(data["source_structure_sha256"]), str(data["source_structure_path"])
    assert global_score.shape == (128,) and local_score.shape == (len(position_sets), 128)
    assert global_score.dtype == local_score.dtype == np.float64
    assert np.isfinite(global_score).all() and np.isfinite(local_score).all()
    if mode == "raw":
        assert source_hash == source_path == "NONE"
    else:
        assert sha256(ROOT / source_path) == source_hash
    return global_score, dict(zip(keys, local_score)), source_hash, source_path


def score_allele(sequence, position_sets, mode, matrices, groups):
    if cache_path(sequence, mode).exists():
        return validate_cached(sequence, position_sets, mode)
    if mode == "raw":
        unpaired, structure_hash, structure_path = np.ones(len(sequence)), "NONE", "NONE"
    else:
        unpaired, structure_hash, structure_path = structure_probability(sequence)
    blocks = scan(sequence, groups)
    baseline = pooled_blocks(blocks, len(sequence), (), unpaired)
    global_score = np.r_[baseline[:, 0] @ matrices[0], baseline[:, 1] @ matrices[1]]
    local_scores = []
    for positions in position_sets:
        pooled = pooled_blocks(blocks, len(sequence), positions, unpaired)
        local_scores.append(np.r_[pooled[:, 2] @ matrices[2], pooled[:, 3] @ matrices[3]])
    payload = io.BytesIO()
    np.savez_compressed(payload, sequence=sequence, sequence_sha256=sequence_hash(sequence), mode=mode,
                        production_manifest_sha256=sha256(OUT / "feature_production_manifest.json"),
                        positions_keys=np.asarray([positions_key(positions) for positions in position_sets]),
                        global_projected=np.asarray(global_score, dtype=np.float64),
                        affected_projected=np.asarray(local_scores, dtype=np.float64),
                        source_structure_sha256=structure_hash, source_structure_path=structure_path)
    path = cache_path(sequence, mode)
    assert path.resolve().is_relative_to(ART.resolve())
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(".pending.npz")
    receipt_path = path.with_suffix(".json")
    assert not pending.exists(), "Preserve unresolved partial cache " + str(pending)
    assert not receipt_path.exists(), "Preserve orphan creation receipt " + str(receipt_path)
    receipt = creation_receipt(payload.getvalue(), sequence, position_sets, mode, sha256(OUT / "feature_production_manifest.json"))
    with pending.open("xb") as handle:
        handle.write(payload.getvalue()); handle.flush(); os.fsync(handle.fileno())
    validate_cached(sequence, position_sets, mode, pending, receipt)
    assert not path.exists(), "Concurrent completed cache must be preserved"
    pending.rename(path)
    jsave(receipt_path, receipt)
    return validate_cached(sequence, position_sets, mode)


def produce(mode):
    production_check()
    assert mode in ("raw", "access")
    assert os.environ.get("OPENBLAS_NUM_THREADS") == os.environ.get("OMP_NUM_THREADS") == "1", "RBP scoring requires one numerical thread"
    assert not any((OUT / track / "fits").exists() for track in TRACKS)
    original, encoded = inventories()
    roster, _ = requests(encoded)
    assert len(roster) == 18220
    if mode == "access":
        assert readj(NEXT_OUT / "structure_cache_production_receipt.json")["status"] == "PASS"
    matrices, groups = load_projections(), load_groups()
    ordered = sorted(roster, key=lambda sequence: (-len(sequence), sequence_hash(sequence)))
    cached = sum(cache_path(sequence, mode).exists() for sequence in ordered)
    began = time.perf_counter(); records = []
    for i, sequence in enumerate(ordered):
        _, _, source_hash, source_path = score_allele(sequence, roster[sequence], mode, matrices, groups)
        path = cache_path(sequence, mode)
        records.append({"sequence_sha256": sequence_hash(sequence), "length_nt": len(sequence),
                        "requests": len(roster[sequence]), "cache_path": path.relative_to(ROOT).as_posix(),
                        "cache_sha256": sha256(path), "source_structure_sha256": source_hash,
                        "cache_creation_receipt_sha256": sha256(path.with_suffix(".json")),
                        "source_structure_path": source_path})
        if (i + 1) % 250 == 0 or i + 1 == len(ordered):
            print(mode, i + 1, "of", len(ordered), "alleles; seconds", round(time.perf_counter() - began, 1), flush=True)
    index_path = ART / (mode + "_cache_index.json")
    jsave(index_path, {"mode": mode, "alleles": records})
    receipt_path = OUT / (mode + "_production_receipt.json")
    receipt = {"status": "PASS", "role": "OUTCOME_FREE_PROJECT_ALLELE_SCORING", "mode": mode,
               "unique_alleles": len(ordered), "cached_at_start": cached,
               "elapsed_seconds": time.perf_counter() - began,
               "cache_index_sha256": sha256(index_path),
               "production_manifest_sha256": sha256(OUT / "feature_production_manifest.json"),
               "original_row_ids_sha256": rowhash(original),
               "projection_receipt_sha256": sha256(OUT / "projection_receipt.json"),
               "scoring_workers": 1, "numerical_threads": 1,
               "outcomes_used": False, "supervised_models_fit": 0}
    if mode == "access":
        receipt["structure_production_receipt_sha256"] = sha256(NEXT_OUT / "structure_cache_production_receipt.json")
    if receipt_path.exists():
        assert readj(receipt_path)["cache_index_sha256"] == receipt["cache_index_sha256"]
    else:
        jsave(receipt_path, receipt)
    print(mode, "production PASS", flush=True)


def assemble():
    production_check()
    assert not any((OUT / track / "fits").exists() for track in TRACKS)
    original, encoded = inventories()
    roster, row_positions = requests(encoded)
    with np.load(NEXT_ART / "base_features.npz", allow_pickle=False) as archive:
        base = archive["features"].astype(float)
    assert base.shape == (26258, 246) and np.isfinite(base).all()
    blocks, cache_indexes = {}, {}
    for mode in ("raw", "access"):
        receipt = readj(OUT / (mode + "_production_receipt.json"))
        assert receipt["status"] == "PASS" and receipt["outcomes_used"] is False
        index_path = ART / (mode + "_cache_index.json")
        assert sha256(index_path) == receipt["cache_index_sha256"]
        index = readj(index_path)
        assert len(index["alleles"]) == len(roster)
        for entry in index["alleles"]:
            assert sha256(ROOT / entry["cache_path"]) == entry["cache_sha256"]
            assert sha256((ROOT / entry["cache_path"]).with_suffix(".json")) == entry["cache_creation_receipt_sha256"]
            if mode == "access":
                assert sha256(ROOT / entry["source_structure_path"]) == entry["source_structure_sha256"]
        cache_indexes[mode] = sha256(index_path)
        # Only256 projected dimensions per allele request stay in memory.
        summaries = {sequence: validate_cached(sequence, positions, mode)[:2]
                     for sequence, positions in roster.items()}
        result = np.empty((len(encoded), 256), dtype=np.float32)
        for i, (parent, mutant, positions) in enumerate(zip(encoded.parent_sequence, encoded.mutant_sequence, row_positions)):
            parent_global, parent_local = summaries[parent]
            mutant_global, mutant_local = summaries[mutant]
            key = positions_key(positions)
            result[i] = np.r_[mutant_global - parent_global, mutant_local[key] - parent_local[key]]
        assert np.isfinite(result).all()
        blocks[mode] = result
        matrixsave(ART / (mode + "_projected_delta.npz"), result)
        del summaries
    matrixsave(ART / "base_model_features.npz", base)
    matrixsave(ART / "raw_model_features.npz", np.column_stack((base, blocks["raw"])))
    matrixsave(ART / "access_model_features.npz", np.column_stack((base, blocks["raw"], blocks["access"])))
    csvsave(ART / "model_row_index.csv.gz", original, True)
    paths = [ART / (track + "_model_features.npz") for track in TRACKS]
    paths += [ART / "model_row_index.csv.gz", ART / "raw_projected_delta.npz", ART / "access_projected_delta.npz"]
    jsave(OUT / "prepare_receipt.json", {
        "status": "PASS", "rows": len(original), "dimensions": {"base": 246, "raw": 502, "access": 758},
        "row_ids_sha256": rowhash(original), "cache_index_sha256": cache_indexes,
        "outcomes_used_for_features": False, "original_alleles_used_for_purge": True,
        "files": {path.relative_to(ROOT).as_posix(): sha256(path) for path in paths},
        "structure_production_receipt_sha256": sha256(NEXT_OUT / "structure_cache_production_receipt.json"),
        "production_manifest_sha256": sha256(OUT / "feature_production_manifest.json"),
    })
    print("All row-aligned RBP matrices assembled; no model fitted", flush=True)


if __name__ == "__main__":
    assert len(sys.argv) == 2 and sys.argv[1] in ("raw", "access", "assemble")
    assemble() if sys.argv[1] == "assemble" else produce(sys.argv[1])
