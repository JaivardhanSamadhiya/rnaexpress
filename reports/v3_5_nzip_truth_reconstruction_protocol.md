# RNAddress v3.5R N-zip truth-reconstruction protocol

**Analysis class:** SOURCE-OF-TRUTH RECONSTRUCTION / HISTORICAL IMPACT CLASSIFICATION  
**Protocol status:** PROSPECTIVE FREEZE WITH SOURCE-EVIDENCE AMENDMENT 1 — no full raw N-zip outcome counting has occurred  
**Frozen from repository commit:** `3de3770b1c7b6d262e77540afa238a6f6934e0ea`  
**Branch:** `rnaddress-v3-5-oracle-audit`  
**Date:** 2026-08-29

## Purpose and boundaries

This protocol governs a source-faithful reconstruction of the mutagenized N-zip experimental truth layer after the Phase 3.5 integrity incident. It is designed to determine what the supplementary-workbook zeros mean, reconcile the reported 5,679 of 6,266 coverage result, recover six sample-level count and ratio measurements, construct a separately versioned exact-SNV benchmark, and classify historical exposure. “Exact SNV” refers to design identity; raw-read matching follows the source-proven substitution-tolerant, indel-free rule in Amendment 1.

The historical Phase 3 NO-GO and every historical data, prediction, recommendation, and report artifact remain immutable. This phase will not train or evaluate a predictive model, recompute an RNAddress gate, inspect Astrocyte outcomes, or list/open/extract the Moffatt result archive. Oracle-identifiability and direction-asymmetry analyses remain paused until a corrected truth layer is committed.

## 1. Authoritative source hierarchy and pinned versions

The source hierarchy, from highest to lowest authority for the indicated fact, is:

1. Raw reads and ENA run metadata for observed molecule/read evidence.
2. The exact designed sequences in Supplementary Table 2a for construct design identity.
3. The publication Methods for the declared experimental and analysis rule.
4. The authors' pinned MPRNA implementation for operational details not contradicted by the paper.
5. Supplementary Table 2b for the published aggregate outcome and significance fields.
6. RNAddress historical processed files only for impact mapping, never for reconstructing truth.

Pinned inputs:

| Source | Identity | Planned role |
|---|---|---|
| Publication | Mendonsa et al., *Nature Neuroscience* (2023), DOI `10.1038/s41593-022-01243-x`, PMCID `PMC9991926` | Declared methods and coverage rule |
| Experiment | ArrayExpress/BioStudies `E-MTAB-10902`; ENA study `ERP133202` | Sample/run provenance |
| Untreated mutagenized runs | `ERR7337821`–`ERR7337826` | Three neurite and three soma samples |
| Supplement workbook | `data/raw/nzip/supplementary/41593_2022_1243_MOESM2_ESM.xlsx` | Full design and published aggregate values |
| Workbook SHA-256 | `15560b562c86c3d8fea8611154c4b0504a9528051b6038c19ff96bb47cd9fec9` | Integrity pin |
| Author code | `data/raw/nzip/MPRNA_v3_5` | Counting/processing audit |
| Author-code commit | `0e7118f1d4880884e6e99e4ba48a26d67f00338a` | Immutable software pin |

Before processing, an acquisition manifest will record URLs, ENA MD5 values, expected and observed bytes, FASTQ record counts, gzip integrity, and locally calculated SHA-256. The BioStudies deposition will be checked for provenance-verifiable sample-level count matrices or processed MPRNA outputs before all FASTQs are downloaded. Such intermediates may be used for comparison but do not replace raw-read reproducibility unless they are complete and exactly attributable to the six runs.

## 2. Construct dictionary and sequence canonicalization

Supplementary Table 2a must yield exactly 6,266 design rows. Every row receives a stable `design_row_id` derived from the zero-based worksheet data-row index plus the source workbook hash. Original gene, tile, mutation type, mutation position, notes, and sequence are preserved verbatim.

Sequence normalization is deterministic:

1. trim surrounding whitespace;
2. uppercase;
3. replace `U` with `T`;
4. reject any character outside `A`, `C`, `G`, `T` rather than deleting or guessing it;
5. preserve sequence length;
6. calculate SHA-256 over the normalized ASCII sequence.

The canonical measurable `sequence_id` is `nzipseq_` plus the full normalized-sequence SHA-256. Construct identity is not equated with sequence identity. All design rows sharing a normalized sequence map to one `sequence_id`, one count vector, and one experimental outcome vector. Their distinct design annotations remain in the design table and a linkage table. No duplicate design identifiers may become independent measured replicates.

The canonical design artifact is `data/processed/nzip_mutagenesis_design_v1.csv.gz`. Duplicate groups are reported in `results/v3_5r/sequence_identity_groups.csv` with group size, all design IDs, mutation labels, parent/tile annotations, and a reasoned class (WT duplicate, convergent mutation, control, or distinct intended construct with an indistinguishable sequence).

## 3. Intervention and WT-parent reconstruction

Intervention types are preserved exactly and additionally classified as WT, exact SNV, multi-base replacement, deletion, scramble, or other documented design. Exact-SNV status is established from sequence comparison, not solely from the workbook mutation label.

A candidate SNV must:

1. have mutation type `sgl`;
2. map to one intended WT parent using source gene ID, source gene name, and source tile ID;
3. have the same length as that WT;
4. differ at exactly one zero-based position;
5. have an A/C/G/T reference and alternate allele;
6. agree with the reported mutation position after the source coordinate convention is determined.

The parent sequence must carry the inferred reference allele. Ambiguous `Cflar_2` source/outcome identities remain quarantined; they cannot re-enter through occurrence-order assumptions. Raw sequence identity may recover a measurement for a sequence but cannot invent a missing design-to-parent identity.

WT-parent validity is decided only after raw measurement reconstruction. An unresolved WT makes all child deltas unresolved. `Map2|5` and `Cox5b|6+7` receive no special retention preference.

## 4. Read-count reconstruction

### 4.1 Primary source-faithful path

The primary count is the number of reads assigned to each canonical measurable sequence, because the publication describes a table of mapped-read counts, reports mapped reads, normalizes reads to total mapped reads, and states the coverage rule in reads. UMI evidence will also be extracted and retained when the read structure permits it, but UMI-deduplicated counts will not silently replace read counts.

Only the six untreated mutagenized WT-condition runs are in scope. The SDRF must establish three biological neurite/soma replicate pairs. Sample names are frozen by accession rather than inferred from file order.

The paper states that R1 reads containing `TTCGATATCCGCATGCTAGC` were considered, the UMI precedes that adapter, and reads were matched to library sequences without insertions or deletions. The public MPRNA default adapter is longer (`TTGATTCGATATCCGCATGCTAGC`). Both motifs and read orientation will be audited on a small deterministic read sample before full counting. The chosen source-faithful extraction rule must be justified by observed read structure and finite-value reproduction; adapter alternatives are reported, not silently pooled.

Matching is substitution-tolerant and indel-free, as established by decompilation of the pinned author bytecode in Amendment 1 below. The implementation will build a deterministic sequence index over canonical `sequence_id` values. A read with one uniquely best canonical sequence under the author mismatch rule is assigned once. A sequence shared by multiple design IDs is still one canonical match. Reads matching zero sequences are unmapped. Reads tied at the best mismatch distance across distinct canonical sequences are `ambiguous` and are not fractionally or multiply assigned. Reverse-complement and offset alternatives are diagnostic candidates; exactly one preregistered primary orientation is selected from adapter/read-structure evidence before outcome comparisons.

The pinned authors' Java counter will be run where its packaged dependencies and invocation are compatible. An independent parser will reproduce the selected exact-match rule. Aggregate and per-sequence disagreements are audited. If the JAR is opaque or incompatible, the independent source-faithful implementation is primary and the limitation is documented.

Counting is deterministic, stream-based, and chunk-order invariant. The raw matrix will contain read counts, genuinely recoverable distinct-UMI counts, mapping state, and per-sample totals. It will be written to `data/processed/nzip_mutagenesis_raw_counts_v1.csv.gz`; run-level QC and unmatched/ambiguous totals go under `results/v3_5r/`.

### 4.2 UMI handling

UMIs are extracted only from the exact read segment established by adapter structure. A UMI is retained verbatim after validating its expected length/alphabet. Distinct UMI counts are calculated per sample and canonical sequence. No error-correction, adjacency collapse, or cross-sequence UMI sharing correction is applied unless an exact historical rule is found in source code/configuration; any such alternative is a labeled sensitivity. Read counts remain the primary publication-faithful quantity unless exact historical configuration proves `useUMIs=TRUE` for this experiment.

### 4.3 Mapping validation

For each sample the audit records total FASTQ reads, adapter-positive reads, uniquely mapped reads, ambiguous reads, unmapped reads, mismatch-distance distribution, and mapping percentage. Publication scale is approximately 1.9 million mapped reads per mutagenized sample. A major unexplained disagreement in scale, systematic failure of one sample, lack of a stable adapter/orientation, or irreconcilable disagreement between author and independent counters triggers STOP before outcome reconstruction.

### 4.4 Source-evidence Amendment 1: author mismatch policy

**Frozen:** 2026-08-29, after a read-structure sample from the first completed FASTQ and bytecode audit, but before full raw counting.

The initial protocol used “exact” to interpret the paper's statement that matching allowed no insertions/deletions. A deterministic 100,000-read inspection of `ERR7337822` showed the declared adapter and orientation but only 331 zero-mismatch insert matches, far below publication scale. Decompilation of `scripts.lincs.patch.AnalyzeConservedPatches` from pinned `compbio.jar` then established the actual rule:

1. `findMatch` locates the adapter with at most two substitutions and no gaps;
2. the post-adapter read suffix is seeded against 5-nt words from the first 15 nt of each library sequence;
3. `matchesStart` compares the read and library sequence positionally without indels;
4. at most two mismatches are allowed in the first 15 nt;
5. candidates with total mismatch count strictly below five (zero through four) are retained;
6. the unique lowest-mismatch canonical sequence is counted;
7. a best-distance tie across distinct exact sequences is ambiguous and not counted;
8. multiple design IDs carrying the same exact sequence all receive the same author-counter read, demonstrating why design-ID-level output can pseudoreplicate one physical sequence.

The independent primary counter will implement these frozen rules at canonical-sequence level. Zero-mismatch exact counts remain a diagnostic column. The author JAR is run on deterministic slices and, resources permitting, full runs. Any difference capable of changing coverage or outcomes triggers STOP. This amendment changes no outcome after inspection; it corrects the counting algorithm from direct source evidence.

## 5. Coverage rule

The primary coverage rule is frozen directly from the publication: a canonical sequence passes if **at least three of the six experimental samples each have at least 20 mapped reads**. This rule is not tuned to force 5,679 passes. Counts are assessed before CPM normalization.

Each canonical sequence receives `coverage_pass`, `coverage_fail`, or `coverage_ambiguous`. Ambiguity is reserved for an unresolved identity/counting conflict, not borderline numeric values. Each of the 6,266 design rows inherits the state of its canonical sequence, while duplicate collapse remains separately explicit.

The observed pass count is compared with the reported 5,679 design constructs. Because the publication count is construct-level but raw measurement is sequence-level, both design-row and unique-sequence totals are reported. Any difference must be exhaustively reconciled through duplicate sequences, mapping/configuration, or documented processing behavior; an unexplained nonzero difference blocks truth-layer freeze.

The public `processTwist.R` contains a statement that indexes low-total-count ratios but does not assign `NA`; therefore that statement does not operationally filter ratios in the pinned revision. This defect is preserved in the software audit. It does not supersede the publication's explicit three-sample/20-read rule.

## 6. Normalization and replicate ratios

For each sample, read counts are normalized to counts per million using the total uniquely mapped reads across the canonical measurable library. No outcome-dependent subset is used in the denominator. If exact historical configuration establishes a different denominator, the publication-faithful CPM is retained as primary and the historical configuration is a labeled comparison.

For each biological replicate, the preregistered simple ratio is:

`log2((neurite_CPM + 0.5) / (soma_CPM + 0.5))`.

The compartment/run pairing comes from SDRF metadata. All three ratios are saved separately. Ratios are quantitative only for coverage-valid, unambiguous sequences; diagnostic values for failed sequences may be calculated in a clearly marked column but can never become truth labels.

The supplementary `Mean_log2ratio_NeuriteSoma_WT` column will be compared against: arithmetic mean of the three simple log2 ratios, log2 ratio of mean normalized counts, and DESeq2 log2 fold change. No semantic candidate is chosen merely because it preserves RNAddress rows. Agreement metrics include exact/rounded equality, Pearson and Spearman correlation, median/95th/max absolute error, and stratified discrepancies by count depth.

## 7. DESeq2 reconstruction

The source-faithful DESeq2 model uses raw integer read counts from the six samples, condition plus biological replicate (`~ condition + replicate`), and the contrast neurite versus soma. It outputs `baseMean`, `log2FoldChange`, `pvalue`, and Benjamini-Hochberg-adjusted `padj`. Missing values remain actual `NA` in memory and blank/NA on export; they are never converted to zero.

The pinned public script and its documented dependencies are audited. Exact historical R/DESeq2 versions and experiment config are sought in the repository, deposition, paper, and output metadata. If the exact environment cannot be recreated, the closest compatible Bioconductor environment is explicitly labeled **source-faithful modern reconstruction**. Any second modern-environment run is a sensitivity and may not be merged with the primary output.

DESeq2 independent filtering is distinguished from the publication's pre-analysis coverage filter. The following are recorded separately: coverage eligibility, whether included in the DESeq2 dataset, estimability of fold change/P value, and independent-filtering status of `padj`.

## 8. Missing outcomes and workbook-zero semantics

Missing truth is represented only as `NA` plus an explicit state/reason. It is never imputed, copied from a parent, replaced by a group statistic, or represented as numerical zero.

All 6,266 rows are reconciled against workbook ratio/padj, raw counts, coverage, reconstructed simple ratios, and DESeq2. Permitted terminal states are:

- `measured_valid`;
- `coverage_filtered`;
- `deseq_unresolved`;
- `sequence_ambiguous`;
- `duplicate_sequence_collapsed` (with the underlying sequence outcome state also retained);
- `design_only_no_measurable_identity`;
- a narrowly named `other_source_documented_state` with evidence.

The 491 zero-plus-missing-padj rows and the remaining 96 implied by 6,266 minus 5,679 are cross-tabulated by every reconstructed state. Zero semantics are classified only after evidence supports one of: supplement export sentinel, RNAddress coercion, source-processing artifact, genuine zero with missing statistics, or mixed causes. The workbook file itself is inspected at the XLSX XML/cell-type level to distinguish stored numeric zero, blank, formula, and reader coercion. Historical RNAddress parsing behavior is audited separately.

## 9. Finite-value validation and stop thresholds

The primary validation cohort is unambiguous, coverage-valid canonical sequences with finite workbook outcomes and finite reconstruction results. Agreement is expected to be near exact apart from documented rounding or a demonstrated semantic difference.

Truth-layer construction stops if any of the following remains unexplained:

1. the 6,266 design total or source key multiset cannot be reproduced;
2. raw file checksum or gzip integrity fails;
3. a sample cannot be mapped at publication-consistent scale;
4. the declared coverage rule cannot reconcile the published 5,679 construct count;
5. no candidate definition of the workbook localization ratio reaches Pearson and Spearman correlation at least 0.999, median absolute discrepancy at most 0.01 log2 units, and 99th-percentile discrepancy at most 0.05, unless a deterministic rounding/export transformation exactly explains the difference;
6. high-confidence historically finite values show a systematic discrepancy beyond those tolerances;
7. author-counter and independent-counter differences can alter coverage or outcomes and cannot be resolved;
8. parent identity or sequence identity cannot be made deterministic;
9. additional source-state coercion affects fields outside the known sentinel pattern;
10. any protected-data boundary is breached.

A triggered stop produces a discrepancy report and no corrected benchmark is labeled valid.

## 10. Corrected exact-SNV cohort and versioning

The corrected benchmark is new and immutable; `data/processed/nzip_snv_intervention_pairs.csv.gz` and all historical artifacts are never overwritten. The planned output is `data/processed/nzip_snv_intervention_pairs_v4_truth_corrected.csv.gz`.

An SNV delta is quantitative only when mutant and correct WT parent each have an unambiguous canonical sequence, pass coverage, have a valid reconstructed localization outcome from the same assay, and do not rely on a sentinel or duplicated independent measurement. The delta is mutant minus WT using the prospectively identified publication outcome definition. Invalid mutant or parent state yields `NA` delta plus a reason.

The benchmark includes stable design/source IDs, canonical sequence IDs, all three mutant and parent replicate ratios, aggregate outcomes, DESeq2 fields, coverage evidence, duplicate linkage, and validity reason. One experimental sequence measurement may annotate multiple design intents but contributes only one independent outcome.

The corrected manifest will be `data/frozen/nzip_v4_truth_manifest.json` and include raw/accession checksums, source hashes, author-code hash, environment versions, processing-script hashes, table hashes, row/state counts, valid/excluded SNVs, retained/excluded/quarantined parents, replicate schema, and unresolved-state definitions.

## 11. Historical old-to-corrected mapping and impact classification

All 4,395 historical rows are left unchanged and mapped by stable source/design and sequence evidence to `results/v3_5r/historical_to_corrected_snv_map.csv.gz`. The map includes historical mutant, WT, and delta; corrected states and outcomes; corrected delta where valid; absolute change; validity; and exact reason.

No model is rerun. Major artifacts are classified as:

- **UNAFFECTED:** construction or procedural conclusions independent of N-zip outcome labels;
- **LABEL-EXPOSED / REQUIRES REANALYSIS:** trained, selected, evaluated, calibrated, or gated using historical N-zip labels;
- **INDIRECTLY EXPOSED:** independent-outcome results whose model training/selection inherited historical N-zip supervision;
- **UNRELATED:** fully independent data and training/selection.

Historical verdicts remain in force as historical records. Corrected reanalysis, if later authorized, must be separately labeled and begin only after this truth layer is frozen.

## 12. Required deterministic artifacts

The reconstruction must produce at minimum:

- `data/processed/nzip_mutagenesis_design_v1.csv.gz`;
- `data/processed/nzip_mutagenesis_raw_counts_v1.csv.gz`;
- `data/processed/nzip_snv_intervention_pairs_v4_truth_corrected.csv.gz`;
- `data/frozen/nzip_v4_truth_manifest.json`;
- `results/v3_5r/sequence_identity_groups.csv`;
- `results/v3_5r/nzip_6266_outcome_state_reconciliation.csv.gz`;
- `results/v3_5r/historical_to_corrected_snv_map.csv.gz`;
- acquisition, environment, count-QC, comparison, discrepancy, and state-summary machine-readable files under `results/v3_5r/`;
- the five remaining required v3.5R reports plus the final verdict report.

All tabular output order, gzip metadata where controlled, hashes, and mapping decisions must be deterministic.

## 13. Tests frozen before interpretation

Tests will verify that missing outcomes remain NA; unresolved values cannot cast to zero; invalid WT or mutant prevents delta generation; duplicate sequences cannot become independent outcome pseudoreplicates; normalization/mapping is deterministic; exact SNVs differ by one base and match the parent reference; ambiguous `Cflar_2` rows remain excluded; coverage and ratio calculations reproduce frozen fixtures; historical files remain byte-identical; and Astrocyte/Moffatt protections remain intact. Raw counting determinism is tested on fixed synthetic FASTQ fixtures and repeated real-data chunk configurations.

## 14. Completion decision and mandatory stop

The final truth-layer decision is:

- **GO — CORRECTED TRUTH LAYER VALID** only if source processing, zero semantics, coverage, finite values, duplicate handling, and the corrected cohort are reproducible and sufficient independent parents remain;
- **CONDITIONAL GO** for a narrow, explicitly quarantined residual mapping that does not contaminate the valid cohort;
- **NO-GO — N-ZIP CANNOT BE RECOVERED RELIABLY** if quantitative outcomes or identities cannot be reproduced or too few parent landscapes remain.

After reports, tests, corrected data, and manifest are committed, work stops. No corrected performance, oracle-identifiability, direction-asymmetry, Astrocyte, or Moffatt analysis is permitted in this phase.
