"""Synthetic-only timing and feature QA before any supervised comparison."""

from .route_structure import *
import time
import unittest
import pandas as pd


def run():
    from src.generalization_20261007.common import freeze_check
    from .test_structure import StructureTests
    previous = freeze_check()
    assert not (OUT / "structure_benchmark_receipt.json").exists(), "Preserve completed benchmark"
    # Persist every model/feature choice before tests, core inventory counting,
    # or the timing benchmark; none depends on comparative research outcomes.
    jsave(OUT / "structure_config.json", SPEC)
    tests = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(StructureTests))
    assert tests.wasSuccessful()
    ensemble.cache_clear()
    rng = np.random.default_rng(20261007)
    timings, synthetic_features = [], []
    left_arm, right_arm = certified_arms()
    for length in (46, 150, 190, 260):
        for pair in range(5):
            if length == 46:
                core = "".join(rng.choice(list("ACGT"), 6))
                parent = left_arm + core + right_arm
            else:
                parent = "".join(rng.choice(list("ACGT"), length))
            mutant = list(parent)
            index = length // 2
            mutant[index] = "ACGT"[("ACGT".index(mutant[index]) + 1) % 4]
            mutant = "".join(mutant)
            for label, sequence in (("parent", parent), ("mutant", mutant)):
                began = time.perf_counter()
                unpaired, entropy, distance, energy = ensemble(sequence)
                elapsed = time.perf_counter() - began
                timings.append({"length_nt": length, "pair": pair, "allele": label,
                                "seconds": elapsed, "ensemble_energy_kcal_mol": energy,
                                "sequence_sha256": hashlib.sha256(sequence.encode()).hexdigest()})
            delta = summaries(mutant, (index,)) - summaries(parent, (index,))
            synthetic_features.append({"length_nt": length, "pair": pair,
                                       **dict(zip(FEATURE_NAMES, delta))})
    timing_frame, feature_frame = pd.DataFrame(timings), pd.DataFrame(synthetic_features)
    # Sequence-only inventory: no localization, replicate, gene, or fold column
    # is read, and no full-core feature matrix is generated in this benchmark.
    core_path = ROOT / "results/probabilistic_ranking_20260928/candidate_index.csv"
    core = pd.read_csv(core_path, usecols=["dataset", "parent_sequence", "mutant_sequence"])
    assert len(core) == 26258 and set(core.dataset) == set(STUDIES)
    alleles = set()
    for parent, mutant, dataset in zip(core.parent_sequence, core.mutant_sequence, core.dataset):
        parent, mutant, _ = encoded_pair(parent, mutant, dataset)
        alleles.update((parent, mutant))
    lengths = pd.Series([len(sequence) for sequence in alleles]).value_counts().sort_index()
    medians = timing_frame.groupby("length_nt").seconds.median()
    maxima = timing_frame.groupby("length_nt").seconds.max()
    median_estimate = sum(int(count) * float(medians.loc[int(length)]) for length, count in lengths.items())
    maximum_estimate = sum(int(count) * float(maxima.loc[int(length)]) for length, count in lengths.items())
    save(OUT / "structure_synthetic_timings.csv", timing_frame.to_csv(index=False, lineterminator="\n").encode())
    save(OUT / "structure_synthetic_features.csv", feature_frame.to_csv(index=False, lineterminator="\n").encode())
    receipt = {"status": "PASS", "benchmark_role": "SYNTHETIC_FEATURE_QA_AND_TIMING_ONLY",
        "tests_passed": tests.testsRun, "synthetic_alleles": len(timings), "synthetic_pairs": len(synthetic_features),
        "synthetic_lengths_nt": [46, 150, 190, 260], "median_seconds_by_length": {str(k): float(v) for k, v in medians.items()},
        "maximum_seconds_by_length": {str(k): float(v) for k, v in maxima.items()},
        "unique_encoded_core_alleles": len(alleles), "unique_alleles_by_length": {str(k): int(v) for k, v in lengths.items()},
        "serial_fold_time_median_seconds_estimate": median_estimate, "serial_fold_time_sample_maximum_seconds_estimate": maximum_estimate,
        "estimate_limit": "timing extrapolation from ten synthetic alleles per length; not guaranteed actual data runtime or total Python feature/persistence cost",
        "cached_summary_memory_bytes_estimate": sum(int(length) * int(count) * 3 * 8 for length, count in lengths.items()),
        "RNA_version": RNA.__version__, "RNA_module_path": str(Path(RNA.__file__)), "RNA_module_sha256": sha256(Path(RNA.__file__)),
        "config_sha256": sha256(OUT / "structure_config.json"), "context_metadata_sha256": sha256(CONTEXT_SOURCE),
        "source_sha256": sha256(core_path), "code_sha256": {path.name: sha256(path) for path in SRC.glob("*.py")},
        "models_fit": 0, "full_core_features_built": False, "outcomes_used": False, "protected_outcomes_opened": False,
        "previous_prefit_files_unchanged": len(freeze_check()["files"])}
    if hasattr(RNA, "_RNA") and hasattr(RNA._RNA, "__file__"):
        receipt["RNA_extension_path"] = str(Path(RNA._RNA.__file__))
        receipt["RNA_extension_sha256"] = sha256(Path(RNA._RNA.__file__))
    jsave(OUT / "structure_benchmark_receipt.json", receipt)
    report = ["# Local ensemble-accessibility route: benchmark and prespecified design", "",
        "This branch is prepared independently after the five-track generalization generation. Only synthetic feature tests and timing were run; no supervised fit or full-core comparative feature analysis was performed.", "",
        "The 11 added features measure mutant-minus-parent differences in mean/min/max changed-site unpaired marginals; mean unpaired probability in the union of changed-site ±10-nt neighborhoods; changed-site pairing-partner entropy (including the unpaired state); expected pairing distance normalized by input length; accessibility-weighted A/G nucleotide content; AG and GA dinucleotide densities; and CCTCCC motif density and maximum accessibility. Motif weights average constituent unpaired marginals. They are not joint motif-opening or RBP-binding probabilities.", "",
        "ViennaRNA2.7.2 uses the global equilibrium ensemble, explicit Turner2004 parameters, 37°C, dangles2, canonical GU pairing enabled, minimum loop3, linear RNA, salt1.021M, and unrestricted base-pair span within the exact supplied sequence. One fixed ±10-nt neighborhood is used; no temperature/window/layer search is allowed. The future ranker preserves the historical246 features and appends these11; candidate pair-RMS scaling and three L2 penalties(.005/.05/.5) use source-only nested selection.", "",
        "Mikl, Astrocyte, and Moffatt inputs are exact admitted inserts. SRLE uses the certified20+6+20-nt local construction template from the reporter metadata certificate. This is not a complete mature HBB reconstruction. All contexts are truncated to available boundaries without padding. Unknown backbone, splicing, cellular RBP binding, and cotranscriptional folding can make predicted insert ensembles differ from the physical RNA. No claim is made that these RNAs fold alone in cells.", "",
        "Independent synthetic QA checks the unpaired marginal against a constrained partition-function ratio, including a nucleotide represented only in the upper-triangle column of ViennaRNA's base-pair matrix. Other tests check complete motif/accessibility normalization, no-edit zeros, edit reversal, the certified SRLE coordinate shift, and invalid inputs.", "",
        f"Four tests passed. Forty synthetic alleles(ten per length46/150/190/260) were folded at fixed settings. The sequence-only inventory contains {len(alleles):,} unique encoded alleles. Median-based serial folding estimate: {median_estimate / 60:.2f} minutes; sample-maximum-based estimate: {maximum_estimate / 60:.2f} minutes. These are estimates from a small synthetic sample, excluding Python feature aggregation, disk/cache overhead, and contention.", "",
        "| Input length | Unique core alleles | Synthetic median seconds/allele |", "|---:|---:|---:|"]
    for length, count in lengths.items():
        report.append(f"| {length} | {count:,} | {medians.loc[length]:.5f} |")
    report += ["", "The configuration was saved before tests and timing. Code/runtime/configuration/context hashes are recorded in the receipt. Full-core feature construction and supervised comparisons require the root's subsequent freeze/start instruction. No new data or paid resource was used; all prior frozen inputs remained unchanged.", "",
        "Primary grounding: [Sequence, Structure, and Context Preferences of Human RNA Binding Proteins](https://pmc.ncbi.nlm.nih.gov/articles/PMC6062212/); [ViennaRNA official repository](https://github.com/ViennaRNA/ViennaRNA); [free-use copyright terms](https://raw.githubusercontent.com/ViennaRNA/ViennaRNA/master/COPYING). Predicted accessibility is a computational hypothesis whose transfer value must be tested against the same baseline and controls.", ""]
    save(REP / "structure_protocol.md", "\n".join(report).encode())
    print(json.dumps(receipt, indent=2), flush=True)


if __name__ == "__main__":
    run()
