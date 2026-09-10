# Mechanism-v2 model selection

Status: prospective inner-development specification, 10 September 2026. No new
localization outer predictions or scores exist at this checkpoint. This document
does not authorize Astrocyte access or claim a completed final evaluation freeze.

## Compact candidate grid

The controlling machine-readable design is
`configs/mechanism_v2/localization_design.json`. Eight families each receive six
recipes: A, shared linear paired ranking with ridge 0.01; B, A plus source linear
nuisance penalty; C, A plus edit-band penalty; D, both penalties; E, ridge 0.1 with
no penalty; F, ridge 0.01 with shrinkage-regularized source ranking temperatures.
There are **48 recipes**, not a neural architecture search. Repeated fitting of
these same recipes across nested folds is validation, not additional tuning.
The previously synthetic-tested implementation is reused without changes.

| Family | Inputs | Columns |
| --- | --- | ---: |
| M0 | Archived geometry/edit descriptors, same definitions | 28 |
| M1 | Signed RBPNet delta + pooled 3UTRBERT allele delta | 540 |
| M2 | Local structure delta at all three preset radii | 18 |
| M3 | Processing motif nuisance delta; no stability model admitted | 8 |
| M4 | M1 + M2 | 558 |
| M5 | M1 + M3 | 548 |
| M6 | M1 + M2 + M3 + motif/exposure deltas | 574 |
| M7 | M6 + four aligned external RBP-availability interactions | 578 |

M6 means all *available* mechanistic/nuisance blocks, not that each has been
validated as a localization mechanism. Processing is not a splice probability.
The independent stability predictors failed before this design, so the stability
block is absent, not represented by zero. No family receives absolute parent
features or source/reporter/gene identity in its biological score.

The BERT choice is prospective and arithmetic: the same fixed-projection pooled
allele function is evaluated on reference and mutant. This makes the primary
128-dimensional delta exactly mutant minus reference and permits a clearly
defined broken-reference comparator. The older contextual delta is preserved as
a separately named diagnostic, not an interchangeable block. This choice was
made without new localization model performance. All three structure windows
remain in the compact model with regularization; no outer-based radius selection.

## Nested selection and weighting

Use the completed all-allele 95% connected grouping: 211 independent components
from 213 historical units. Exact gene, parent, mutant, and cross-source links
are preserved. Five outer folds and their three inner component assignments are
read from the hash-pinned inventory, not regenerated after results. The prior
90% parent-only sensitivity is retained but is not a gene-family test.

For each outer fold, all 48 recipes fit separately to each inner training split.
Preprocessing, nuisance matrices and source temperatures use training rows only.
Pair sampling is uniform within decision sets without outcomes, capped at 128
unordered pairs per set. Exact outcome ties are subsequently omitted. Weights
balance source, connected component, decision set and candidate. The biological
prediction API accepts feature matrices only; decrease uses its negative.

Concatenate the three inner out-of-fold predictions for each recipe. Average
decision metrics within component/source/direction, then average source/direction
contexts equally. Select the smallest regret, retaining a 0.002 regret tolerance
window; within that window use highest rank, fewer columns plus nuisance/head
parameters, then lexical recipe ID. Select one recipe within each M0–M7 family
and one primary candidate across M1–M7. M0 is never a selected mechanism.
No separate directional model or outer-selected ensemble is allowed.

Per-recipe inner predictions, model parameters, exact train/validation row IDs,
hashes, convergence and exclusion records are immutable. A completed shard is
reused only after hash and identity checks. An exclusive process lock prevents
duplicate training. A stale lock requires process/log inspection; the runner
does not infer that an old PID is dead and delete it automatically.

The `train` stage currently implements **inner development only**. There are 720
inner fits (48 × 3 × 5). `evaluate`, `controls`, `freeze` and `holdout` must not be
represented as completed. A separate complete outer-evaluation protocol/code
freeze is required before producing outer results.

## Heads, nuisance flags and uncertainty

Source temperatures change ranking-loss weighting during training, not the order
of scores within an assay at inference. They are not calibrated assay-value
regression heads. Head necessity must compare retrained F with A and retrained
source-reassigned F, especially in leave-source transfer. An inference-only
positive-affine shuffle cannot establish necessity. Reporter affine heads and
flexible neural heads are excluded prospectively.

Processing covariates versus a flag/abstention policy will be compared on inner
predictions: a flagged top edit changes at least one strict donor/acceptor or
canonical/common PAS motif. Flagging never deletes outcomes or changes the
full-cohort primary metric. Report coverage and the full-versus-abstaining policy
on identical covered decisions. No favorable outer subgroup becomes an exclusion.

Uncertainty uses three connected-group bootstrap refits of the selected inner
recipe and within-decision percentile-rank standard deviation. Coverage choices
are 100%, 90%, 75%, selected inside training only by covered regret with the same
0.002 tolerance, then greater coverage. Full coverage remains the gate. These
policy/uncertainty stages are specified here but not yet executed by the inner
runner. Their executable tests are prerequisites for final outer evaluation.

The data have already been reused through multiple historical redesigns. Even
properly nested results remain development evidence, not independent confirmation.
