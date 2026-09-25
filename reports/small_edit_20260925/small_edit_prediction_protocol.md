# Frozen small-edit prediction protocol

User-directed reframing, 25 September 2026. Written after sequence/measurement
inventory, before new model fitting or performance calculation. Outcomes and
earlier broad results are already known; this is exploratory grouped development
estimation, never pristine confirmation or a replacement for an old NO-GO gate.
No universal-mechanism v6 claim is tested. New artifacts use a separate namespace.

## Primary cohort and estimand

Mikl only, separately CAD and Neuro-2a, using the exact existing certified
Phase-B candidate cohort and biological folds. Keep every finite measured effect
with 1–6 corresponding-coordinate substitutions. No significance, effect-size,
reliability or favorable-gene filtering. Each cell has 13/147/663/8896 rows for
1/2/3/4–6 bases respectively. Parent RNA is the certified 150-nt test insert;
target is author-processed mutant-minus-matched-WT log2(neurite/soma).
Missing absolute parent measurements remain missing; zero is not an imputed WT.
Coordinate edit span and minimum Levenshtein distance are reported separately.
No >6-base training examples enter the new fits. Tiers are never pooled into a
central performance claim. Training uses all eligible <=6 sizes; test reporting
always separates 1,2,3,4–6. This distinction is explicit in final claims.

All variants, both cell outcomes and identical parent/mutant alleles from a gene
remain in the original biological fold. Verify no parent, gene or exact allele
crosses folds; preserve the earlier all-allele grouping audit. Each cell is fit
separately, so test genes are unseen but assay/cell context is represented.

## Fixed models and controls

Task A predicts quantitative delta with Ridge, standardized on training only.
Every nonconstant comparator receives the same inner alpha grid {10,100} and
leave-one-of-the-four-training-folds-out selection by gene-macro mean squared
error. Ties go to lower grid order. Sample weights make training genes equal.
No-change is zero with direction probability 0.5.

Controls: training-mean effect/training-prevalence probability; changed-base count;
edit position/span; parent/mutant mononucleotide
composition; delta AU; delta 1-mer; delta 2-mer; delta 3-mer; delta 1–3-mer;
local aligned +/-5-base windows (mean pre-edit one-hot and change, zero padding);
historical motif-count deltas (CCC, CCTCCC, ATAT, TATA, TGCA, TGTA);
and a seeded 16-dimensional Gaussian projection of delta 1–3-mer features.
Motifs are predictive controls across prior hypotheses, not proven causal
determinants in this assay. Random projection retains sequence information;
it is a representation control, not a label-null or proof of nonspecificity.

The paired representation combines delta 1–3-mer frequencies, edit count and
geometry, local pre-edit/change windows, and parent-mononucleotide by delta-
mononucleotide products. These interactions and edit-local context allow the
same substitution to have different effects depending on its parent. The primary
model is selected inside each training fold from delta123 and paired, each with
the same alpha grid. It is a fixed nested selection procedure, not a test-set
winner. Save every inner score, selected recipe and fitted coefficient/scaler.

Task B fits L2 logistic C=1 on the corresponding training features, using the same
gene weights, excluding exactly zero effects from binary training/scoring.
The primary feature family is the Task-A inner-selected family, with no further
direction-optimized search. Threshold 0.5 is fixed. Probabilities predict observed
effect sign, not statistical significance. Seed 20260925 only; no seed retries.

Task C uses quantitative effect predictions, not outcome-selected alternative
scores. Within each exact parent x cell x edit band with >=2 distinct candidates
and nonzero measured range, rank all measured candidates for both increase and
decrease. Fixed lexical mutant-sequence/ID tie order. Retain all controls on
identical sets. Compute exact uniform expected regret; do not mistake a lexical
tie policy for uniform selection. No unchanged-parent option is added after
seeing outcomes. Interpret wrong-direction changes relative to the measured WT,
separately from regret relative to the best measured candidate.

## Reporting and uncertainty

Tasks A/B: gene-balanced MAE/RMSE, sign accuracy, balanced accuracy, Brier score,
global Pearson/Spearman and auROC; gene-macro auROC where both signs are present
with eligible-gene counts; observed calibration slope/intercept and fixed
probability bins. No calibration fitted to outer outcomes is used for prediction.
Task C: regret, parent rank correlation, correct/wrong-direction rate, best/top-k
recovery, and fraction of genes improved versus each control. Average parents
and directions inside gene, then genes equally, separately for every cell/band.
No averaging across assays, cells or size bands to produce a success claim.

Use 2,000 deterministic paired gene-bootstrap draws for gene-macro loss,
classification and decision metrics and differences. CIs condition on fitted
models/splits and omit refitting uncertainty. Correlations/global auROC are
descriptive points; gene-macro auROC supplies clustered descriptive uncertainty.
Report per-gene/fold performance and all failures. Tier1 and two-base Task C
have too few units for a robust population claim. A formal breadth claim needs
at least20 eligible genes, but meeting that minimum alone is not a pass.

A candidate small-edit advantage requires positive paired 95% lower bounds
against every required applicable simple comparator, plus at least .02 mean
normalized regret improvement for Task C, >50% genes improved, and no increase
in wrong-direction selection. Otherwise describe the actual weaker evidence.
These are conservative descriptive flags for this exposed-data analysis, not
new confirmatory gates. No p-value or multiple-look discovery claim is made.
Above-chance signal alone cannot establish superiority over composition/motifs.

## Secondary existing evidence and stopping

Reproduce SRLE's frozen aggregate outputs first. Export fixed model differences
f(mutant)-f(parent) and evaluate A/B/C descriptively on the original1744 measured
candidate links among592 parents/60 composition classes. No refitting, new
split/neighborhood/quality threshold or independent-parent claim. A score is not
a calibrated direction probability; leave that probability undefined.

SIRLOIN: only original227 SNV metadata and finite Rep1/2 outcomes, fixed existing
source-model and motif scores; subtract each WT score using the same saved source
lookup. No target fit or recalibration; retain original substitution-class
candidate sets and failed gate. Two biological parents preclude population CIs.

Other resources remain inventory/previous-result evidence. Do not invent small
edits between unrelated tiled fragments or use intron/barcode constructs as pure
small-RNA edits. Reserved/quarantined outcomes stay closed. New-dataset discovery
remains blocked and is not retried. Stop after this one specified analysis,
regardless of result. Any implementation failure is documented and corrected
without changing scientific choices; partial outputs are preserved/versioned.
