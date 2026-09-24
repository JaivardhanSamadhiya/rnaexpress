# Measurement follow-up — 23 September 2026

AI-authored working notes. No historical verdict is changed. This file records
post-hoc diagnostics and a resource decision, not student-authored submission prose.

## HeLa: suspend this processed endpoint

A second agent independently re-extracted the 277 already-open Total1 values by
header name and reproduced all saved values. It independently recounted the
existing raw prefix, checked all 31 exact-read examples and their barcode
uniqueness, and verified sample identity. No defect was found in our orientation,
row alignment, column selection or prefix parsing. It reviewed, but did not
rerun, the completed 9.60-million-read full scan.

The author's unique-barcode mapping branch sums all reads bearing that barcode.
The supplied normalization code applies column scaling. Those operations alone
do not explain the 31 processed zeros supported by 157-22,579 exact high-quality
reads in the documented raw sample. The relationship of the repository's
four-replicate example to the final six-replicate table remains unknown.

Decision: stop biological model testing on this processed endpoint unless a
documented raw-to-processed mapping becomes available. The failed pilot remains
failed; the mismatch is not proof of an error in the published study.
Sources are the author's [mapping code](https://github.com/cshukla/oligoGames/blob/c5b4966f0fc367af49f887e008aaaa19a1199972/exec/mapToBarcodes.py),
[normalization code](https://github.com/cshukla/oligoGames/blob/c5b4966f0fc367af49f887e008aaaa19a1199972/R/normCounts.R)
and [sample metadata](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM2615964).

## SEERS: quality sensitivity does not rescue transfer

The separate specification fixed minimum insert-base Phred thresholds 0, 20,
25 and 30, exact anchors and paired sequence agreement. Only the previously
opened RNA prefixes and 241 frozen predictions were used. No data were enlarged,
no model fitted and no threshold selected as a replacement primary analysis.

| Minimum Phred, both mates | Eligible groups | Candidates | Primary kmer regret | CCC regret | Random regret |
|---|---:|---:|---:|---:|---:|
| 0 | 24 | 126 | 0.55847 | 0.44568 | 0.50000 |
| 20 | 20 | 104 | 0.59179 | 0.47267 | 0.50000 |
| 25 | 20 | 104 | 0.59179 | 0.47267 | 0.50000 |
| 30 | 5 | 25 | 0.44949 | 0.55810 | 0.50000 |

Lower regret is better. The cohorts differ across rows, so these differences
cannot be attributed solely to measurement quality. Q20 improvement over random
was -0.09179, descriptive group CI [-0.22662, 0.04781]. Q20 and Q25 counts happened
to coincide; all Q30 counts and metrics exactly reproduced the frozen screen.

On the fixed original 25-candidate cohort, primary regrets were 0.31724 at Q0,
0.46608 at Q20/Q25 and 0.44949 at Q30. Every descriptive primary improvement
interval over random crossed zero. No favorable subset is promoted. Across all
241 candidates, Q20/Q30 endpoint Spearman was 0.73860. Retention fractions varied
across sequences and fractions; these read-level observations do not establish
biological replication or identify the cause of quality dependence.

The original screen remains inconclusive. This diagnostic provides no convincing
transfer benefit, even when read coverage reaches twenty composition groups.
Stop further threshold/model searches on this small older archive.

The independent provenance search found no download for the updated CSVs in the
checked official repository, notebooks, project archives or OMIX records. The
available archive predates Method 2 and L6 represents one biological sample with
technical replication. See seers_updated_data_provenance_20260923.md for sources
and the limits of that bounded search.

## Productive continuation

A newly located independent resource is Faraway et al., Nature 2025,
[Collective homeostasis of condensation-prone proteins via their mRNAs](https://doi.org/10.1038/s41586-025-09568-w).
Its public reporter library combines synonymous sequence variants and intron
placement while preserving the protein product. This makes a combinatorial
selection question potentially feasible. Aggregate mechanisms in that paper
are already known and cannot be claimed as new. Construct identity, processed
endpoint semantics and replication must qualify before numerical outcomes open.

A fallback requiring no new resource is a source-only benchmark for selecting
one fragment robust across all four Ron/Ulitsky reporter contexts. Existing
analyses average separate context-specific selections and do not answer this
question. A maximin rule would need comparison to mean-context selection, all
four single-context rules, composition and random, on identical complete-case
candidate sets and component-held-out folds. Maximin optimization itself is
prior art; no experiment or novelty claim has yet been made for this proposal.
