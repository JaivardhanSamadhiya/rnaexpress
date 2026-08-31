# RNAddress v4 Moffatt source-truth audit

## Verdict and chain of custody

Moffatt was successfully converted from a sealed candidate into **v4 development data**. The conversion followed the required outcome-blind sequence:

1. `reports/v4_moffatt_preunseal_protocol.md` was committed at `bdbd9f1fbf30ea0094ea7bf7f029c4f828ec82ed` before any archive listing, extraction, or count-file opening.
2. The sealed archive hash was verified as `abc6e571ed68833e3fb0c0028209303a0f468347ac5f6efbeffd788c35c7ade1`.
3. The irreversible status transition and timestamps were committed at `e5cec4985cdc841673b95f5e9b63b5662b5ffb9d` before opening the archive.
4. Only then were the 80 predeclared processed-count members extracted and read.

Moffatt can never again be represented as independent validation. Astrocyte remained sealed throughout.

## Primary source and acquired files

- Moffatt et al., *Robust mammalian RNA localization elements are large and multipartite*; DOI [`10.64898/2026.06.09.731215`](https://doi.org/10.64898/2026.06.09.731215), PMID `42327238`, PMCID `PMC13277945`.
- GEO [`GSE334718`](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE334718); BioProject `PRJNA1476227`.
- `GSE334718_RAW.tar`: 12,697,600 bytes; SHA-256 above.
- `supplementary_file_1.txt`: sequence dictionary; 20,971,564 bytes; SHA-256 `202c019bfbd91e0a5d4f94da2b2b340e4f76ceda10d7c73f75f08090d346195e`.
- `supplementary_table_1.csv` through `supplementary_table_5.csv`: sufficiency, necessity, mutation, shuffle, and SHAPE outcome tables; exact hashes are `3adabe4e…`, `419accb4…`, `a752bc9f…`, `8bcec57a…`, and `c504d638…`, with full values in the machine manifest.
- The 80 exact GSM-to-filename mappings are frozen in `results/v4_phaseA/moffatt_geo_sample_manifest.csv`.

Public analysis-code corroboration was recorded at `charliemoffatt/sufficiency-mpra-analysis` commit `cb05e45d608b9ef51f22a25df8b14ebcbfec9c22` and `charliemoffatt/LE_SHAPE_Summary` commit `329ad93801587ed8c29053c2c36500fb9dd9cbec`. The manuscript-declared `TaliaferroLab/peak-oligo` repository did not resolve publicly during the audit; this is explicit, not silently substituted.

## Experimental design and raw-count integrity

The GEO design is exactly:

`5 assay families × 2 reporters × 2 compartments × 4 biological replicates = 80 samples`.

Families are mutation, necessity, SHAPE, shuffle, and sufficiency; reporters are GFP and Firefly; compartments are soma and neurite. All 80 predeclared files exist. Each is a headerless tab-separated table of oligo key, read count, and UMI count.

- Duplicate oligo keys within a sample: 0.
- Rows per sample: minimum 14,570; maximum 24,164.
- Unexpected or missing sample design keys: 0.

## Sequence-dictionary integrity

The dictionary contains 64,697 unique identifiers and 64,697 unique sequences and ends with a newline. The final record `trp53_1|260_1+suff` is present with a 260-nt sequence, disproving a truncation concern.

Thirty-five dictionary records are malformed 297-nt shuffle constructs containing `N`; their IDs carry `_h-NA`. None is accepted as a certified 300-nt fixed-length oligo. They are not silently repaired.

Across the five author outcome tables there are 47,955 rows. Exact ID mapping lacks sequence entries for 1,658 rows: 7 sufficiency, 1,557 necessity, 47 mutation, 14 shuffle, and 33 SHAPE. Five additional rows fail deterministic operation validation. All 1,663 are excluded with reason and source row. The certified set is therefore **46,292 interventions**.

## Outcome-blind parent reconstruction

All standard library oligos have 20-nt flanks around a 260-nt biological insert. Parents were reconstructed without reading effects:

- Sufficiency IDs use 1-based inclusive coordinates. The retained parent window appears first, followed by a source-declared inactive endogenous background. Overlapping windows reconstruct complete parents for `cdc42`, `gdf11`, `net1`, `rab13`, `trak2`, and `trp53`.
- Necessity IDs use 1-based half-open deletion coordinates. The retained parent is followed by inactive padding. Overlapping retained bases reconstruct `cdc42bpg`, `cplx2`, `gdf11`, `malat1`, `net1`, `rab13`, `trak2`, and `trp53inp2`.
- Mutation windows independently reconstruct the same six parent sequences as sufficiency. The four overlapping names `gdf11`, `net1`, `rab13`, and `trak2` agree exactly between necessity and mutation.

There are **10 biological parent labels/contexts but eight unique parent sequences**: `cdc42` and `cdc42bpg` share an exact sequence, as do `trp53` and `trp53inp2`. They remain separate biological labels for primary grouping and are additionally auditable under sequence-hash grouping.

Every certified child is checked against the reconstructed parent and its declared operation. No outcome is used to select a parent.

## Intervention classes

| Class | Certified interventions | Design meaning |
| --- | ---: | --- |
| Sufficiency background replacement | 9,462 | preserve a parent window and replace the remainder with inactive sequence |
| Necessity deletion with inactive padding | 3,328 | remove a parent interval and pad back to fixed length |
| Random substitution | 14,235 | mutate bases within declared windows, generally three designs per window |
| Regional shuffle | 10,539 | reorder bases within declared windows |
| SHAPE structure perturbation | 8,728 | mutate stem sides, compensatory stems, loops, or other structure-defined regions |

The author methods describe 260-nt parents, fixed-length sufficiency/necessity padding, three unique random mutants per window, shuffle designs emphasizing Hamming distance, and structure-directed SHAPE perturbations. The source code further confirms 1-based inclusive sufficiency spans and 260-nt sequence operations.

## Outcomes, replicates, and uncertainty

Finite author-processed outcomes exist for 44,248 GFP interventions and 20,783 Firefly interventions. They are **WT-normalized author log2 neurite enrichment** and remain separate reporters.

For every intervention/reporter, Phase A also retains all available raw UMI log2(neurite/soma) replicate ratios with pseudocount 0.5. A diagnostic mean, range, and standard error are emitted only when at least two paired replicates exist:

- GFP: 46,186 interventions have at least two paired raw ratios.
- Firefly: 44,535 interventions have at least two paired raw ratios.

These raw diagnostics are not equivalent to uncertainty on the author WT-normalized effect and are labeled accordingly. Insufficient paired-replicate states remain explicit. The certified author effect is not discarded solely because a raw diagnostic is sparse.

The recovered sufficiency analysis code states that explicit WT oligos were accidentally omitted from that MPRA and that normalization used localization-element controls. This is a real assay-specific caveat and is a major reason not to pool outcomes numerically across families.

Direction counts among finite effects are:

| Reporter | Increase | Decrease |
| --- | ---: | ---: |
| GFP | 27,007 | 17,241 |
| Firefly | 13,226 | 7,557 |

## Edit scale

Moffatt exact sequence Hamming distance has mean 74.556, median 48, and range 1–249. Operation-aware edit cost has median 40 and range 1–510. For fixed-length deletion/replacement designs, cost is removed bases plus inserted padding bases; it can therefore exceed 260. Other classes use exact changed bases.

Only six certified Moffatt interventions are exact one-base changes, all from one parent context. Moffatt's central value is mechanism and budget diversity, not broad exact-SNV coverage.

## Leakage-safe use and limitations

Primary splitting must hold out the biological parent label. Every assay family, reporter, variant, and replicate from that parent stays together. A stricter sequence-equivalence sensitivity split must co-group the two duplicated parent-sequence pairs. Because 46,292 variants derive from only 10 labeled parent contexts, row-level random splitting would be catastrophic leakage.

Moffatt is strong evidence for within-element operation learning and cross-operation representation. It is weak evidence for transfer to unseen genes by itself. Its value becomes defensible only alongside Mikl's 5,830 and TDP's 4,566 parent contexts and with assay-specific heads.

## Machine artifacts

- `results/v4_phaseA/moffatt_interventions.csv.gz`
- `results/v4_phaseA/moffatt_geo_sample_manifest.csv`
- `results/v4_phaseA/moffatt_preunseal_metadata_audit.json`
- `results/v4_phaseA/moffatt_unseal_log.json`
- `results/v4_phaseA/common_intervention_outcomes.csv.gz`
- `results/v4_phaseA/exclusion_audit.csv`
- `results/v4_phaseA/edit_distribution.csv`
- `results/v4_phaseA/phaseA_summary.json`
- `results/v4_phaseA/source_manifest.json`
