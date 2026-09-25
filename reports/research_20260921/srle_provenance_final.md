# SRLE measurement provenance — final bounded audit, 25 September 2026

**Determination: PARTIAL.** The benchmark's use of published Table 5 and the
local four-library count arithmetic pass. The complete author raw-to-Table-5
production chain remains unresolved. This supports reporting a benchmark on
the published score landscape, with explicit provenance qualifications; it does
not support calling that landscape independently reconstructed or biologically validated.

This additive AI-authored audit preserves all earlier reports and gates. Its
scope was recorded in `provenance_work_scope_20260925.md` before the new
calculations; it fits no model and searches no normalization, sign or pseudocount.

| Measurement link | Status | Verified evidence / missing information |
|---|---|---|
| Source supplement identity | VERIFIED | Pinned Europe PMC supplement SHA-256 and nested Table5 workbook; only Table5 opened. Workbook SHA-256 `4a128c2542914d948866ba6500a043b11f10585726500d5e1ecfa389e2e73cc4`. |
| Table5 to benchmark rows | VERIFIED | All 4,096 unique six-mers, worksheet `Table S5`, Excel rows 3–4098, mapped after original U-to-T normalization and lexical ordering. Every score exactly matches both prediction tables and the published-forward field in archived raw scores. |
| Original train/test assignment | VERIFIED | Original deterministic hash partition reproduced: 3,234 train / 862 test. Prediction-analysis eligibility remains 855 test rows / 70 composition classes. |
| Archive sample labels and files | VERIFIED | Official run metadata maps HRR3059160/61/62 to Cyto1/2/3 and HRR3059163/64/65 to Nuc1/2/3. Sample/experiment/biosample IDs and filenames exported, not inferred. |
| Biological identity, replicates 1/2 | STRONGLY_SUPPORTED | Labels, archived read QC and receipts agree. File identity cannot independently verify the laboratory sample assignment or biological independence. |
| Biological identity, replicate 3 | AMBIGUOUS | Previously inspected first 1,000 IDs and sequences match differently labeled MALAT1 runs in both mates. Full-file identity and pooling/demultiplexing remain unresolved. No new counts or outcomes admitted. |
| Raw files to local saved count matrix | STRONGLY_SUPPORTED | Eight complete raw-file SHA-256 values rechecked against receipts; prior extraction/QC recorded 33,010,339 pairs and 30,267,389 accepted fragments. Raw counting was not repeated in this audit. |
| Local count matrix to saved replicate NRS | VERIFIED | Four count columns match archived copies; all depth sums equal accepted-fragment QC; original half-count depth normalization exactly reproduces both 4,096-value NRS vectors. Maximum error 0. |
| Local eligibility | VERIFIED | Original >=20 counts in each of four libraries gives 4,069 sequences. This is our diagnostic rule, not a recovered author Table5 filter. |
| Author three-replicate count matrix / statistic / export | UNRESOLVED | Missing authoritative matrix, filter, zero policy, replicate pooling or DESeq2 coefficient definition, and exact Table5 export. |
| Physical construct identifier | UNRESOLVED | Six-mer identity is exact, but no per-row physical clone identifier is established. HBB reporter context is a study-level description, not 4,096 independent biological contexts. |
| Public code versus documentation | CONTRADICTORY in specific fields | Current `nes` uses cytoplasmic abundance in both terms; shared-denominator CPM and field/sign descriptions differ from methods. This contradiction is in the inspected code/documentation, not proof that Table5 was produced by that code or is incorrect. |

The [lineage CSV](D:/rnaexpress/artifacts/research_20260925/srle_measurement_lineage.csv)
contains 24,576 rows: 4,096 sequences times six labeled libraries. The two
unquantified libraries have empty count and reconstructed-value fields with
explicit unresolved status. Nuclear and cytoplasmic rows repeat their paired
replicate NRS; those repetitions are provenance links, not extra observations.
The [sample manifest](D:/rnaexpress/artifacts/research_20260925/srle_samples.csv)
and [calculation receipt](D:/rnaexpress/artifacts/research_20260925/srle_lineage_result.json)
record accession IDs, hashes, denominators, exact comparisons and scope.

The fixed local score is
`log2((Nuc+0.5)/(sumNuc+2048)) - log2((Cyto+0.5)/(sumCyto+2048))`.
Its mean absolute difference from the published aggregate is 0.18234 / 0.18071
for replicates 1/2, with maxima 3.40812 / 2.35289. **These compare different
quantities.** They are not a fitted reconstruction error, evidence of a bad paper,
or grounds to choose a different normalization. The earlier eligible-row raw-to-
published correlations of 0.720/0.730 are association checks, not equivalence.

## Bounded public-source history inspection

The official [SRLE repository](https://github.com/lysovosyl/SRLE-seq) supplied
public free source text and metadata. Six code blobs, one 40-entry commit listing,
and two historical recursive tree responses were archived with URLs, timestamps,
SHA-256, and Git blob verification. No downloaded code, CSV or model was executed
or scored. Existing pinned current scripts/README/configuration were also reviewed.

The current prediction files consume precomputed numeric examples and train/infer
a classifier; they do not define raw-count production or Table5 export.
Two history snapshots were selected because commit metadata named deleted count
and processing helpers: `620411cae4a236cef8a333a3b117a69fdce97bbd` and
`ebef7a015d87e93c54b1223a0323c073e74f0cb7`.

- Historical `kmer_count.py` counts at most one matched insert per read pair,
  normalizes orientations, optionally filters length, and exports diversity CPM.
  It has no nuclear/cytoplasmic replicate fit or Table5 export.
- Historical `makeshell.py` emits commands for time-labeled diversity processing
  using local paths and primer metadata. It does not supply a six-mer nuclear/
  cytoplasmic accession manifest, DESeq2 analysis or workbook export.
- Historical `library_location_analysis.py` accepts one nuclear/cytoplasmic pair,
  counts mates separately and later computes compartment-specific CPM. Its
  `log2fc` uses cyto/nuc whereas `nes` uses nuc/cyto with 0.5. It contains no
  three-replicate analysis or Table5 export. These definitions differ from the
  current file; their existence does not identify the publication workflow.

New commit metadata clarifies an earlier conservative description:
`a65b8d3d26258647d41611cf1656c08ea34e9196` is the latest inspected **commit**;
its actual tree is `ff6a7dd10825858c006b274528f3d748ab329f15`. The previous report
recorded the API tree-response SHA without assuming a commit. This is an additive
identity clarification, not a modification of that historical report.

No complete route was found **within this scope**. Other history versions,
unpublished scripts and author intermediates are not ruled out. Inspection stops
here because missing authoritative production records cannot be recovered by
trying alternative formulas against published outcomes.

## Reproduction and next evidence needed

Use bundled Codex Python from the repository root, with bytecode writing disabled:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
& 'C:\Users\jaisa\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m src.research_20260921.srle_measurement_lineage_20260925
```

The shipped `lineage_config.json` pins inputs and code; keep it when replaying.
`--freeze` is only for an empty new audit directory, never for replacing the
delivered configuration. `srle_public_history_20260925` reuses hash-checked cached
sources; if absent it retrieves only the documented public SRLE source scope.
Historical `raw_counts.py` documents the original extraction but is not rerun by
the lineage audit. The new audit's initial freeze attempt caught a transcribed
hash typo before any output; correction used the existing checkpoint manifest,
and no historical input was changed.

The remaining author questions are in
[srle_provenance_questions_20260925.md](D:/rnaexpress/reports/research_20260921/srle_provenance_questions_20260925.md).
Authoritative records could upgrade PARTIAL; additional predictor experiments cannot.
