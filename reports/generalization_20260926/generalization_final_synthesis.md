# Generalization synthesis

**The strongest fully supported claim remains Level 1: strict within-SRLE small-edit prediction.** The newly frozen external study produced a useful candidate-regret signal, but neither zero-shot transfer nor the primary incremental sequence-order replication criterion passed. We should preserve the candidate result as positive secondary evidence and avoid upgrading the overall claim.

| Question | Result | Interpretation |
| --- | --- | --- |
| Existing SRLE result preserved? | 10.19% edit-effect MSE gain, descriptive interval 1.00–19.99%; regret 0.320 vs 0.500 | Yes, one reporter context; frozen result unchanged |
| Exact SRLE coefficients transfer? | Mean parent rho 0.051 [−0.003, 0.139]; composition baseline 0.067 | No strong zero-shot transfer demonstrated |
| Same order representation adds beyond simple controls? | B rho 0.102; paired increment 0.013 [−0.022, 0.068], exact p=0.3125 | Weak/heterogeneous incremental evidence; criterion failed |
| Held-parent candidate choice useful? | Regret 0.372 vs simple 0.489 and uniform 0.500; 5/14 wrong direction | Positive predeclared secondary signal; not a reliable general design tool |
| Third untouched dataset available here? | GSE334718 explicitly unsealed in August for development | No; independent-test branch stopped |

All external results use 3,984 verified SNPs, seven 190-nt parents, five nonoverlap components and two genes (Slc1a2 and Sparc). The author-retained design has 14 matched biological replicate labels (three-cortex pools), with 11–14 positive matched pairs per admitted variant. Technical sequencing lanes are not biological replicates. Intervals below are descriptive 95% component-bootstrap intervals, not evidence of thousands of independent biological contexts. Historical exposure is PARTIALLY EXPOSED.

## What was completed

Verified original frozen SRLE bundles; audited official metadata and historical exposure; reconstructed the 190-nt SNV design and author endpoint; committed protocols, source coefficients and every source-only prediction before reveal; mapped all 3,984 eligible outcomes; ran A once; preserved its failed primary result; executed the previously fixed nested overlap-purged B study; ranked every candidate in both directions; performed the fixed two-gene and coefficient checks; audited GSE334718 without reopening its outcomes; independently replayed predictions and metrics; produced reproducible reports, figures and the evidence ledger.

Protocols, implementation and source-only predictions were frozen in `0b100d3`; access marker `5ae6d4a` preceded reveal. Once-run A outcomes were preserved at `1ff9bc2` before conditional B. The UTC/local-time typographical error in the marker is disclosed in `execution_notes.md`; the timestamped JSON and git ancestry establish the order.

All 37 prefit hashes remain unchanged. Fresh reconstruction of **84 outer model fits exactly reproduced their predictions** (maximum numerical error 0.0); 4,553 source-only predictions, 154 parent/model metrics, 308 selected-candidate decisions and two primary uncertainty calculations were checked independently. Twelve scoped tests passed. Original bundles with 119, 70 and 41 manifest members and their ZIP hashes are unchanged. No spending, new scheduled task, protected dataset opening, broad model search or unfiltered pytest occurred.

## Why each generalization approach fell short

**A, direct source parameter transfer:** the primary had a small uncertain rank correlation and underperformed composition/substitution ranking. Its 2-mer-only component was weaker still. The difference in compartment endpoint, species/cell type, parent length, and substitution versus composition-preserving exchange could explain the mismatch, but the experiment does not isolate these explanations. Candidate regret improved but wrong-direction frequency did not.

**B, local representation replication:** fitting in astrocytes produced positive held-parent ranks and useful extreme-candidate ordering, yet simple position/substitution controls captured most whole-list rank signal. Adding 2-mers helped four parents and hurt three; the paired increment is uncertain. The stronger candidate result is concentrated at the ranked extremes and does not prove a robust improvement throughout the candidate list. Its exact simple-baseline regret p=0.0625 also reflects the tiny block count. The isolated Δ2-mer model's regret was 0.510, so adjacency alone was not a successful candidate recommender.

**More complex frozen controls:** 3-mer and 1–3-mer variants did not supply a coherent strong-transfer result, and were not promoted after reveal. This study does not justify more architecture/hyperparameter search against these same outcomes.

**GSE334718 as untouched third system:** historical outcome-driven development disqualifies it. Its exact-SNP breadth is also sparse. Relabeling exposed data would not add independent evidence.

## Representation, parameters and mechanism are different claims

| gauge | pearson | cosine | sign_concordance | permutation_p_positive |
| --- | --- | --- | --- | --- |
| grand_mean | -0.470618 | -0.470618 | 0.500000 | 0.966073 |
| row_column_interaction | 0.457356 | 0.457356 | 0.625000 | 0.091286 |

The mean held-parent isolated-2mer coefficient vector is negatively correlated with SRLE after grand-mean removal (r=−0.471). Removing row/column additive composition terms yields positive interaction concordance (r=0.457), but the fixed descriptive feature-label permutation p=0.0913 is uncertain. Correlated features, overlapping training fits and only two genes make these conditional coefficient diagnostics, not independent mechanism tests. Neither flipping the transferred sign nor extracting a favorable coefficient subset is permitted. Exact parameter transfer is not established; representation reuse shows partial evidence; a shared molecular mechanism is not demonstrated.

## Claim hierarchy

1. **Level 1 — supported:** strict within-SRLE small-edit prediction, with the original composition/similarity controls and limitations.
2. **Level 2 — incomplete:** independently collected astrocyte data show weak held-parent ranks and a positive candidate-regret secondary result, but the frozen primary incremental-order criterion failed. State this as partial evidence, not completed method validation.
3. **Level 3 — not established:** exact source coefficients did not pass the frozen zero-shot test.
4. **Level 4 — not established:** no independent three-system candidate-edit validation exists.

## What remains missing and the next three tasks

1. Finish a reproducible paper/presentation around the existing SRLE result, the protected external test, its limits, and the positive secondary candidate result. Keep the failed primary results prominent; neither novelty nor competition success is established by a score.
2. Resolve measurement provenance before stronger direction claims: exact raw-count/author-REML reproduction, WT measurement uncertainty, complete sample pedigree and transcript versions. A separate diagnostic protocol may address these, but must preserve the present endpoint and verdicts. The paired-CPM corroboration here is not full pipeline certification.
3. Seek a genuinely new, unexposed computational validation resource with more independent parent genes and measured small-edit alternatives, only under a distinct admission/prefit protocol. More searches or fits on these already opened datasets cannot convert the failed test into independent confirmation. This task deliberately stopped at its prescribed boundary.

## Do not touch and confidence gaps

Do not alter the SRLE source fits/results/bundles; the 37-file GSE330741 prefit manifest; A/B outcomes, predictions, metrics or failures; the exposure classifications; historical failed RNAddress gates; N-zip/TDP EV5 and other reserved data; or unrelated user modifications. Do not flip A signs, select another primary after reveal, discard weak parents, retune candidate rules, spend money or create scheduled tasks.

Confidence is high in exact sequence mapping, preservation and numerical replay. It is limited by historical partial exposure (the three original printed rows are unidentified), five nonoverlap components nested within two genes, partially shared samples/WT references, endpoint mismatch, lack of full author-pipeline replay, and no wet-lab validation. Bootstrap/sign-flip assumptions across components remain approximate because common genes and experimental pools create additional dependence. Public availability and primary-source provenance do not by themselves prove biological validity or novelty.

## Deliverables

The eight requested reports are in `reports/generalization_20260926/`. Predictions, all candidate ranks and `generalization_evidence_ledger.csv` are in `artifacts/generalization_20260926/`. Protocol/configuration, complete baseline/parent tables, fitted parameters, provenance and verification receipts are in `results/generalization_20260926/`. `src/generalization_20260926/figures.py` renders the figures from saved results; `verify.py` replays the frozen outputs without scientific model selection. See `reproducibility.md` for safe reproduction and the archive receipt for hashes.
