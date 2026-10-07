"""Synthetic parallel benchmark and guarded, restartable ensemble cache.

Worker entry points import only NumPy/ViennaRNA through route_structure. Core
production reads sequence columns only, and requires a committed production
protocol whose hashes certify the code, configuration, runtime, and input.
"""

from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import lru_cache
import argparse
import ctypes
import hashlib
import io
import json
import multiprocessing
import os
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
NS = "generalization_next_20261007"
OUT, ART, REP = [ROOT / folder / NS for folder in ("results", "artifacts", "reports")]
CONFIG_PATH = OUT / "structure_config_v2.json"
CORE_PATH = ROOT / "results/probabilistic_ranking_20260928/candidate_index.csv"
PROTOCOL_PATH = OUT / "feature_production_manifest.json"
THREAD_ENV = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")
PRODUCTION_WORKERS = 2
_route = None


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sequence_hash(sequence):
    return hashlib.sha256(sequence.encode("ascii")).hexdigest()


def worker_initialize():
    global _route
    for name in THREAD_ENV:
        os.environ[name] = "1"
    from . import route_structure
    _route = route_structure


def windows_peak_memory():
    """Peak working set, available without another package on Windows."""
    if os.name != "nt":
        return None
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
    counters = Counters(); counters.cb = ctypes.sizeof(counters)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return int(counters.PeakWorkingSetSize)


def fold_worker(sequence):
    if _route is None:
        worker_initialize()
    began = time.perf_counter()
    result = _route.ensemble(sequence)
    return {"sequence": sequence, "sequence_sha256": sequence_hash(sequence), "summary": result,
            "fold_seconds": time.perf_counter() - began, "pid": os.getpid(),
            "peak_working_set_bytes": windows_peak_memory(),
            "thread_environment": {name: os.environ.get(name) for name in THREAD_ENV}}


def pool_fold(sequences, workers):
    for name in THREAD_ENV:
        os.environ[name] = "1"
    with ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn"),
                             initializer=worker_initialize) as pool:
        tasks = {pool.submit(fold_worker, sequence): sequence for sequence in sequences}
        for future in as_completed(tasks):
            result = future.result()
            assert result["sequence"] == tasks[future]
            yield result


def cache_path(sequence):
    checksum = sequence_hash(sequence)
    return ART / "structure_ensemble_cache" / file_hash(CONFIG_PATH) / checksum[:2] / (checksum + ".npz")


def validate_cached(sequence, path=None):
    from . import route_structure as route
    path = cache_path(sequence) if path is None else Path(path)
    with route.np.load(path, allow_pickle=False) as data:
        assert str(data["sequence"]) == sequence and str(data["sequence_sha256"]) == sequence_hash(sequence)
        assert str(data["config_sha256"]) == file_hash(CONFIG_PATH)
        unpaired, entropy, distance = [data[key].copy() for key in ("unpaired", "entropy", "distance")]
        energy = float(data["energy"])
    for array in (unpaired, entropy, distance):
        assert array.shape == (len(sequence),) and route.np.isfinite(array).all()
    assert route.np.isfinite(energy) and ((unpaired >= 0) & (unpaired <= 1)).all()
    assert (entropy >= -1e-10).all() and ((distance >= -1e-10) & (distance <= 1 + 1e-10)).all()
    return unpaired, entropy, distance, energy


def persist_fold(result):
    from . import route_structure as route
    sequence = result["sequence"]
    path = cache_path(sequence)
    if path.exists():
        old = validate_cached(sequence, path)
        assert all(route.np.array_equal(left, right) for left, right in zip(old, result["summary"]))
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    unpaired, entropy, distance, energy = result["summary"]
    payload = io.BytesIO()
    route.np.savez_compressed(payload, sequence=sequence, sequence_sha256=sequence_hash(sequence),
                            config_sha256=file_hash(CONFIG_PATH), unpaired=unpaired, entropy=entropy,
                            distance=distance, energy=energy)
    # Publish only a complete file. Never replace a completed allele cache.
    temporary = path.with_suffix(".pending." + str(os.getpid()) + ".npz")
    if temporary.exists():
        raise FileExistsError("Unresolved temporary cache " + str(temporary))
    with temporary.open("xb") as handle:
        handle.write(payload.getvalue()); handle.flush(); os.fsync(handle.fileno())
    validate_cached(sequence, temporary)
    if path.exists():
        raise FileExistsError("Concurrent completed cache " + str(path))
    temporary.rename(path)
    return path


@lru_cache(maxsize=20000)
def cached_summary(sequence):
    from .route_structure import normalize
    sequence = normalize(sequence)
    return validate_cached(sequence)


def build_features(frame, base246):
    from .route_structure import build_features as build
    return build(frame, base246, summary_provider=cached_summary)


def certify_production_protocol():
    """Root writes/commits this certificate before the first real core fold."""
    from . import route_structure as route
    from .common import production_check
    expected = [CONFIG_PATH, CORE_PATH, route.CONTEXT_SOURCE, Path(__file__), Path(route.__file__),
                Path(route.RNA.__file__), Path(route.RNA._RNA.__file__), REP / "protocol.md"]
    protocol = production_check()
    for path in expected:
        key = path.relative_to(ROOT).as_posix()
        assert protocol["files"][key] == file_hash(path), key
    assert protocol["files"][str(Path(__file__).relative_to(ROOT).as_posix())] == file_hash(__file__)
    assert route.SPEC == json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return protocol


def produce():
    from . import route_structure as route
    from src.generalization_20261007.common import freeze_check
    import pandas as pd
    protocol = certify_production_protocol()
    freeze_check()
    core = pd.read_csv(CORE_PATH, usecols=["dataset", "parent_sequence", "mutant_sequence"])
    assert len(core) == 26258 and set(core.dataset) == set(route.STUDIES)
    sequences = set()
    for parent, mutant, dataset in zip(core.parent_sequence, core.mutant_sequence, core.dataset):
        parent, mutant, _ = route.encoded_pair(parent, mutant, dataset)
        sequences.update((parent, mutant))
    assert len(sequences) == 18220
    ordered = sorted(sequences, key=lambda sequence: (-len(sequence), sequence_hash(sequence)))
    existing = 0; missing = []
    for sequence in ordered:
        if cache_path(sequence).exists():
            validate_cached(sequence); existing += 1
        else:
            missing.append(sequence)
    print(json.dumps({"production": "START", "unique_alleles": len(ordered), "cached": existing,
                      "pending": len(missing), "workers": PRODUCTION_WORKERS}), flush=True)
    began = time.perf_counter(); completed = 0; worker_peak = {}; fold_seconds = 0.
    for result in pool_fold(missing, PRODUCTION_WORKERS):
        persist_fold(result); completed += 1; fold_seconds += result["fold_seconds"]
        worker_peak[result["pid"]] = max(worker_peak.get(result["pid"], 0), result["peak_working_set_bytes"] or 0)
        if completed % 100 == 0 or completed == len(missing):
            print(json.dumps({"production": "PROGRESS", "completed_this_run": completed,
                              "total_cached": existing + completed, "elapsed_seconds": time.perf_counter() - began}), flush=True)
    for sequence in ordered:
        validate_cached(sequence)
    receipt = {"status": "PASS", "role": "UNSUPERVISED_SEQUENCE_ONLY_FEATURE_PRODUCTION",
               "unique_alleles": len(ordered), "cached_at_start": existing, "folded_this_run": completed,
               "workers": PRODUCTION_WORKERS, "worker_threads": 1,
               "elapsed_seconds": time.perf_counter() - began, "sum_worker_fold_seconds": fold_seconds,
               "worker_peak_working_set_bytes": {str(key): value for key, value in worker_peak.items()},
               "protocol_sha256": file_hash(PROTOCOL_PATH), "config_sha256": file_hash(CONFIG_PATH),
               "models_fit": 0, "outcomes_used": False, "full_core_feature_matrix_built": False,
               "previous_prefit_files_unchanged": len(freeze_check()["files"])}
    receipt_path = OUT / "structure_cache_production_receipt.json"
    if receipt_path.exists():
        # Preserve the first successful production record. Revalidation is
        # idempotent and reports to stdout, without overwriting timings.
        assert completed == 0
        receipt["role"] = "COMPLETED_CACHE_REVALIDATION"
    else:
        route.jsave(receipt_path, receipt)
    print(json.dumps(receipt, indent=2), flush=True)


def benchmark_parallel():
    from . import route_structure as route
    from src.generalization_20261007.common import freeze_check
    from .test_structure import StructureTests
    import unittest
    freeze_check()
    assert not (OUT / "structure_parallel_benchmark_receipt.json").exists(), "Preserve completed parallel benchmark"
    route.jsave(CONFIG_PATH, route.SPEC)
    tests = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(StructureTests))
    assert tests.wasSuccessful()
    rng = route.np.random.default_rng(20261007)
    sequences = []
    left, right = route.certified_arms()
    for length in (46, 150, 190, 260):
        for _ in range(5):
            parent = (left + "".join(rng.choice(list("ACGT"), 6)) + right if length == 46 else
                      "".join(rng.choice(list("ACGT"), length)))
            mutant = list(parent); index = length // 2
            mutant[index] = "ACGT"[("ACGT".index(mutant[index]) + 1) % 4]
            sequences.extend((parent, "".join(mutant)))
    assert len(set(sequences)) == 40
    route.ensemble.cache_clear()
    began = time.perf_counter()
    serial = {sequence: route.ensemble(sequence) for sequence in sequences}
    serial_elapsed = time.perf_counter() - began
    comparisons = []
    for workers in (2, 4):
        began = time.perf_counter(); results = list(pool_fold(sequences, workers))
        elapsed = time.perf_counter() - began; peaks = {}; folds_by_length = {}; max_difference = 0.
        for result in results:
            assert all(value == "1" for value in result["thread_environment"].values())
            reference = serial[result["sequence"]]
            for expected, actual in zip(reference, result["summary"]):
                max_difference = max(max_difference, float(route.np.max(route.np.abs(expected - actual))))
                assert route.np.array_equal(expected, actual), "Spawned worker summary changed"
            pid = result["pid"]
            peaks[pid] = max(peaks.get(pid, 0), result["peak_working_set_bytes"] or 0)
            folds_by_length.setdefault(len(result["sequence"]), []).append(result["fold_seconds"])
        medians = {str(length): float(route.np.median(times)) for length, times in folds_by_length.items()}
        lengths = json.loads((OUT / "structure_benchmark_receipt.json").read_text())["unique_alleles_by_length"]
        weighted_seconds = sum(lengths[length] * value for length, value in medians.items()) / workers
        comparisons.append({"workers": workers, "wall_seconds_including_spawn": elapsed,
                            "speedup_vs_current_serial": serial_elapsed / elapsed,
                            "exact_array_and_energy_parity": True, "maximum_absolute_difference": max_difference,
                            "worker_peak_working_set_bytes": {str(key): value for key, value in peaks.items()},
                            "sum_worker_peak_working_set_bytes": sum(peaks.values()),
                            "median_fold_seconds_by_length_under_contention": medians,
                            "weighted_core_fold_seconds_divided_by_workers_estimate": weighted_seconds})
    receipt = {"status": "PASS", "role": "SYNTHETIC_SPAWN_PARALLEL_BENCHMARK_ONLY",
               "tests_passed": tests.testsRun, "synthetic_alleles": len(sequences),
               "current_serial_wall_seconds": serial_elapsed, "benchmark_worker_counts": [2, 4],
               "fixed_production_workers": PRODUCTION_WORKERS, "worker_threads": 1,
               "parent_peak_working_set_bytes": windows_peak_memory(), "comparisons": comparisons,
               "models_fit": 0, "full_core_folds": 0,
               "estimate_limit": "40 synthetic folds; weighted medians assume balanced scheduling and exclude per-file writes/validation; not guaranteed data runtime",
               "config_sha256": file_hash(CONFIG_PATH), "route_code_sha256": file_hash(route.__file__),
               "parallel_cache_code_sha256": file_hash(__file__),
               "previous_prefit_files_unchanged": len(freeze_check()["files"])}
    route.jsave(OUT / "structure_parallel_benchmark_receipt.json", receipt)
    lines = ["# Synthetic structure parallel benchmark and cache producer", "",
             "Two and four spawned processes use one numerical thread each. Only the same forty synthetic alleles were folded. All three summary vectors and ensemble energies must be exactly identical to serial results. Worker imports need only NumPy and ViennaRNA; dense pairing matrices are transient and never persisted.", "",
             f"Current serial forty-allele time: {serial_elapsed:.3f} seconds. Production is fixed to two workers so another CPU representation route can run concurrently on the four-core machine.", "",
             "| Workers | Wall seconds including spawn | Observed speedup | Summed worker peak MiB | Estimated full-core folding minutes |",
             "|---:|---:|---:|---:|---:|"]
    for result in comparisons:
        lines.append(f"| {result['workers']} | {result['wall_seconds_including_spawn']:.3f} | {result['speedup_vs_current_serial']:.2f} | {result['sum_worker_peak_working_set_bytes']/2**20:.1f} | {result['weighted_core_fold_seconds_divided_by_workers_estimate']/60:.1f} |")
    lines += ["", "Timing estimates use ten alleles per length; they exclude per-file storage and validation overhead. They are planning estimates rather than runtime guarantees. Exact feature choices, context arms, and physics remain those in structure_config.json.", "",
              "The producer stores one compressed NPZ per SHA-256 of the exact encoded sequence, under its configuration SHA-256 directory. Each contains only the exact sequence, identity/config hashes, three per-nucleotide summary vectors, and ensemble energy. Completed files are validated and skipped on restart. Writes use a temporary file and publish only after validation, preserving completed entries.", "",
              "Core production requires the committed feature_production_manifest.json certificate pinning configuration, code, runtime, context metadata and core sequence input and protocol.md. Exactly26,258 rows/18,220 alleles, two workers, and one thread per worker are asserted by the producer. It reads only dataset/parent_sequence/mutant_sequence columns. Its command does no supervised fitting or full-core feature-matrix construction. Five accessibility-off motif deltas use identical masks/normalization with every weight1; correctedbase246+raw5+ensemble11 gives262 columns.", ""]
    route.save(REP / "structure_parallel_protocol.md", "\n".join(lines).encode())
    print(json.dumps(receipt, indent=2), flush=True)


def main():
    for name in THREAD_ENV:
        os.environ[name] = "1"
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("benchmark", "produce"))
    args = parser.parse_args()
    (benchmark_parallel if args.command == "benchmark" else produce)()


if __name__ == "__main__":
    main()
