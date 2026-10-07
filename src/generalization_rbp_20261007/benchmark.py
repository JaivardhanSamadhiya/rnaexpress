"""Catalog validation and synthetic-only scorer feasibility, never core features."""

from pathlib import Path
import json
import time
import unittest

from .prepare_catalog import ART, OUT, REP, ROOT, digest, jsave, save
from .scoring import np, PLAN, load_groups, summaries, allele_delta
from .test_scoring import MotifTests


def run():
    assert not (OUT / "synthetic_feasibility.json").exists(), "Preserve completed benchmark"
    manifest = json.loads((ART / "direct_human_manifest.json").read_text())
    plan = {**PLAN, "catalog_manifest_sha256": digest((ART / "direct_human_manifest.json").read_bytes()),
            "unique_pfms": manifest["unique_normalized_pfms"],
            "raw_dimensions": 4 * manifest["unique_normalized_pfms"],
            "accessible_dimensions": 4 * manifest["unique_normalized_pfms"]}
    jsave(ART / "fixed_score_plan.json", plan)
    outcome = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(MotifTests))
    assert outcome.wasSuccessful()
    groups = load_groups()
    rng = np.random.default_rng(20261007)
    timings = []
    for length in (46, 150, 190, 260):
        for pair in range(2):
            parent = "".join(rng.choice(list("ACGU"), length))
            mutant = list(parent)
            changed = length // 2
            mutant[changed] = "ACGU"[("ACGU".index(mutant[changed]) + 1) % 4]
            mutant = "".join(mutant)
            for allele in (parent, mutant):
                began = time.perf_counter()
                features = summaries(allele, [changed], groups=groups)
                seconds = time.perf_counter() - began
                assert features.shape == (1684,) and np.isfinite(features).all()
                assert np.all((features >= 0) & (features <= 4 + 1e-12))
                timings.append({"length_nt": length, "pair": pair, "seconds": seconds})
            delta = allele_delta(parent, mutant, groups=groups)
            assert delta.shape == (1684,) and np.isfinite(delta).all()
    medians = {str(length): float(np.median([row["seconds"] for row in timings if row["length_nt"] == length]))
               for length in (46, 150, 190, 260)}
    receipt = {
        "status": "SYNTHETIC_SCORING_AND_PUBLIC_METADATA_PASS",
        "tests_passed": outcome.testsRun, "synthetic_alleles": len(timings),
        "unique_pfms": manifest["unique_normalized_pfms"], "human_rbps": manifest["retained_human_rbp_ids"],
        "timings": timings, "median_seconds_by_length": medians,
        "catalog_manifest_sha256": digest((ART / "direct_human_manifest.json").read_bytes()),
        "score_plan_sha256": digest((ART / "fixed_score_plan.json").read_bytes()),
        "source_sha256": {path.name: digest(path.read_bytes()) for path in (ROOT / "src" / "generalization_rbp_20261007").glob("*.py")},
        "raw_feature_columns": 1684, "raw_total_with_base": 1930,
        "raw_plus_accessibility_total_with_base": 3614,
        "float32_26258_by_1930_storage_bytes_arithmetic_only": 26258 * 1930 * 4,
        "float32_26258_by_3614_storage_bytes_arithmetic_only": 26258 * 3614 * 4,
        "feasibility_limit": "Sixteen synthetic alleles only; excludes actual source neighborhoods, persistence, inner fits and reused ensemble cache memory. No full-core timing claim.",
        "public_binding_metadata_only": True, "project_data_loaded": False,
        "project_features_computed": False, "supervised_models_fit": 0,
        "protected_outcomes_opened": False,
    }
    jsave(OUT / "synthetic_feasibility.json", receipt)
    report = f"""# Direct human RBP motif catalog: resource admission and scorer preparation

The official public [CisBP-RNA bulk form](https://cisbp-rna.ccbr.utoronto.ca/bulk.php) supplied a human-only archive containing PFMs and evidence annotations. The actual download URL was resolved from that form and recorded, rather than guessed. No login, payment or downloaded executable was required. The archive is 248,765 bytes; SHA256 `{manifest['archive_sha256']}`. Build 2.00 and the site's displayed update string are pinned with official page snapshots. The [resource paper](https://doi.org/10.1093/nar/gkaf1081) describes free access and is CC BY 4.0. No separate catalog license was found in the inspected pages or archive, so redistribution of catalog files is not certified; use is internal research with attribution.

The human main evidence table contains {manifest['evidence_rows']} mappings. Protein-level status D alone is insufficient: some D proteins also have JPLE-inferred motifs. Inclusion requires human species, D status and a motif-level experimental assay type, using the main evidence table rather than the homology-expanded all_motifs table. There are {manifest['eligible_mappings_before_member_check']} eligible experimental mappings. {len(manifest['missing_pfm_mappings'])} have absent or empty matrices and remain excluded, with individual reasons preserved. No missing PFM is imputed. {manifest['retained_evidence_mappings']} valid mappings represent {manifest['retained_human_rbp_ids']} proteins. Exact row-normalized float64 matrix hashing removes {manifest['duplicate_motif_ids_removed']} duplicate motif ID, leaving {manifest['unique_normalized_pfms']} matrices of widths 4–25nt. Every original mapping, gene identifier and source type is retained; the two distinct DBID columns are named separately. CNBP RNAcompete and HNRNPK RNAcompete/RBNS motifs are present. The catalog includes in vitro and direct CLIP/RIP-derived motifs, whose biological limitations differ.

The fixed scorer adds a pseudocount of 1e-4 to each normalized nucleotide probability, renormalizes each row, and computes the geometric mean likelihood ratio to a uniform A/C/G/U background across each complete forward-strand motif window. This threshold-free numerical specificity proxy lies in (0,4]; it is not an occupancy or physical affinity probability. For every motif, use mean and maximum scores over the exact encoded allele and over the union of motif windows overlapping changed nucleotides. Parent and mutant use the same start coordinates. Features are mutant-minus-parent. No reverse complement, sequence padding, outcome-selected motif, hit threshold or target normalization is admitted. This produces 1,684 raw columns.

A later separately frozen comparison can append those raw columns to the same corrected 246 baseline, then add 1,684 accessibility-weighted columns. The accessible score is the raw score times the mean of constituent unpaired marginals; it is not joint motif-opening probability. The all-unpaired=1 control recovers raw scores exactly. The SRLE certificate supplies only the 20+6+20 local construction input, and other inserts retain their exact available sequences. Cached structure marginals may be reused after code/context/hash correspondence is certified. No new structure or encoder search is proposed. Whole-assay/component/exact-allele purge and source-only nested L2 selection must be frozen before any biological feature or fitting run. A positive catalog coefficient cannot identify an active RBP where several proteins share motifs; cellular abundance, competition, splicing and full transcript context are missing.

Four independent synthetic tests check motif-level provenance filtering, explicit base order, duplicate hashing, direct enumeration of window likelihoods, accessibility-off equivalence, identity edits and reversal. Sixteen synthetic alleles were scored; median seconds per allele by length are {json.dumps(medians, sort_keys=True)}. These are tiny synthetic feasibility measurements, not measured project runtime. Float32 storage arithmetic for 26,258 rows is {26258 * 1930 * 4:,} bytes for baseline+raw and {26258 * 3614 * 4:,} bytes for baseline+raw+accessible; optimizer copies and caches add memory. No project candidate table was loaded, no full-core features were computed and no model was fitted.

The [official help](https://cisbp-rna.ccbr.utoronto.ca/help.html) distinguishes direct and inferred motifs and documents matrix formats. [ATtRACT](https://pmc.ncbi.nlm.nih.gov/articles/PMC4823821/) is an alternative mixed-assay catalog; it was not downloaded. [Dominguez et al. 2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC6062212/) provides primary evidence that RNA structure, flanking sequence and bipartite arrangement can distinguish RBPs with similar short sequence motifs. This grounds a falsifiable transfer hypothesis; it does not demonstrate localization generalization or novelty.
"""
    save(REP / "resource_and_score_plan.md", report.encode())
    print(json.dumps({key: receipt[key] for key in ("status", "tests_passed", "unique_pfms",
        "human_rbps", "synthetic_alleles", "median_seconds_by_length", "project_features_computed", "supervised_models_fit")}, indent=2), flush=True)


if __name__ == "__main__":
    run()
