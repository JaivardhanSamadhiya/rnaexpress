# RNAddress FinalShot frozen zero-shot protocol

Freeze date: 2026-09-02

Starting commit required by the controlling prompt: `f5bf28e`

Committed resource-audit checkpoint: `f2b2c01`

Historical verdicts: Phase B `NO-GO`; Phase B2 `NO-GO`; historical N-zip
outcome analyses invalidated. This protocol is the last authorized test of the
original zero-shot RNAddress hypothesis.

## 1. Scope, question, and nonnegotiable boundaries

The estimand is ranking quality for interventions on a previously unseen RNA
biological parent, using no intervention outcome from that parent. Given parent
sequence, cellular context, requested increase/decrease direction, and a fixed
candidate set, the model must rank measured candidates through a shared score.
This is not few-shot calibration and does not generate arbitrary edits.

Only certified v4 Mikl/GSE173098, TDP-43/GSE288185, and
Moffatt/GSE334718 localization outcomes are eligible. The exact v4 decision
cohort, exclusions, decision sets, biological-unit identities, and five
deterministic folds are reused. N-zip outcomes are prohibited for every purpose.
Astrocyte outcomes, expression, translation, ribosome occupancy, and sequences
remain sealed; no Astrocyte prediction or preregistration is authorized here.

Outcome-independent resource download, hash verification, runtime loading,
synthetic inference timing, public transcriptome processing, and exact sequence
deduplication are allowed before this freeze. No FinalShot localization model,
representation score, or definitive transfer result was calculated before this
protocol's first commit.

## 2. Resource decision frozen before outcomes

The official published Parnet/PanRBPNet preprint architecture has no released
matching checkpoint. The development checkpoint that loads does not match the
paper architecture. Parnet is therefore excluded under section 6 of the
controlling prompt; it will have no output-space or hidden-embedding result.
No retraining is allowed.

The sole mechanistic fallback is RBPNet 0.10.0 at repository commit
`8ee000dcdb897e0eeed6a46a855604299e914ca7`. Its official 103-model Zenodo
archive has MD5 `e88fb57483ba9a3d81b842cc5aa140fb` and SHA-256
`dc182e51d7b3ffe046ec7de56ab7e98a9ec0bd2f789d8e6bd61168b3718c355d`.
Every model hash is frozen in `results/finalshot/rbpnet_checkpoint_manifest.csv`.
Only frozen target-profile output and mixing-coefficient output are eligible.
Control/total tracks and hidden representations are excluded.

DeepLocRNA, BRIDGE, RNALocate v3, generic ViennaRNA structure, and GSE249405
are excluded as input features for the reasons committed in the resource audit.
No alternative model zoo may be introduced after this freeze.

## 3. Cohort and decision tasks

The canonical row source is the v4 Phase A common intervention table filtered
through the exact Phase B eligible decision-set membership. The expected frozen
cohort is 93,208 assay rows, 445 base decision sets, 890 directional tasks, and
213 biological units; reconstruction must fail closed if these counts or the
source manifest differ.

- Mikl decision set: gene × cell line; biological unit is held gene.
- TDP decision set: gene; biological unit is held gene.
- Moffatt decision set: exact-sequence-equivalent parent × assay family ×
  reporter; biological unit is the co-held biological parent.

Each base set must contain at least five finite candidates and positive measured
effect range. A candidate is good when normalized regret is at most 0.10.
Increase chooses high score; decrease chooses low score. No direction flag is
an input to the shared effect score.

## 4. Exact biological splitting and weighting

The five existing deterministic Phase B/B2 outer folds are reused without
regeneration. Mikl and TDP hold complete genes; Moffatt holds complete
exact-sequence-equivalent parents. All rows, reporters, contexts, assays, and
variants of an outer biological unit remain outside training, scaling,
regularization selection, latent-head fitting, and calibration.

Inner selection cycles over the remaining biological folds. Leave-source-out
holds all outcomes from the target source. CAD→N2A and N2A→CAD hold all outcomes
from the target cell state. Firefly→GFP and GFP→Firefly hold all outcomes from
the target reporter. No target measurement head is fit in these transfers.

Training and evaluation weights are hierarchical: equal total source weight;
within source equal biological-unit weight; within unit equal decision-set
weight; within set equal candidate weight. Weights are normalized to mean one
for fitting. Metrics are averaged in the corresponding set→unit→source order.
Moffatt row count never constitutes independent replication.

## 5. Outcome orientation and shared latent target

The shared biological score `phi` is oriented so larger means greater neurite/
distal localization on the source's declared effect scale. For M0-M2, training
uses the within-decision-set empirical midrank of `localization_effect`, mapped
to `[0,1]`. This monotone rank target is created only for training decision
sets and removes arbitrary affine source scale while retaining ordering.

M3 instead fits raw training effects through low-capacity monotone measurement
heads. At test time every model ranks candidates only with `phi`; source heads
are never required for zero-shot selection.

## 6. Frozen primary representations

There are exactly three primary families.

### R0 — geometry

The Phase B/B2 metadata block is reused: edit cost and fraction; substitution,
insertion, deletion, replacement, and operation sizes; changed-block count;
first/last/mean position and span; A/C/G/T/GC composition deltas; operation
signature/class; edit-cost tier. Source, gene, parent identity, and outcome
statistics are absent.

### R1 — 3UTRBERT contextual state

The frozen `yangheng/3utrbert` revision is
`220d80829deb077d1d640463a4267a96e9e70b1d`; checkpoint SHA-256 is
`7aca71823ab74771006be1030d9e7239220bba40a16858575929a02e6d2a7471`;
the previously rebuilt certified-v4 cache SHA-256 is
`51912767e74dc19a06dadf6bab9f3022f11939f1cc537f024af148cc18f948d9`.
R1 uses the fixed 128-dimensional parent absolute block and 128-dimensional
contextual mutant-minus-parent block plus R0. No encoder selection or tuning is
allowed.

### R2 — RBPNet output-space intervention signature

All 103 frozen checkpoints are evaluated at native sequence length: 150 nt for
Mikl and 260 nt for TDP/Moffatt. Parent and mutant lengths must match; no
sequence is cropped or padded. DNA `T` is used; any character outside A/C/G/T
is encoded by the official all-zero unknown convention and counted. Outputs
are cached by exact sequence SHA-256, checkpoint SHA-256, native length,
RBPNet commit, TensorFlow version, and output definition.

For each checkpoint, target-profile logits are softmax-normalized over sequence
positions. Let `p_r(P)` and `p_r(M)` be parent/mutant target distributions,
`d_r = p_r(M)-p_r(P)`, and `a_r` the mixing coefficient. Changed positions are
the direct Hamming mismatch set. The edit span is first through last mismatch.
Radius `q` means the edit span expanded by `q` positions on both sides and
clipped to sequence boundaries.

Technical clarification recorded before any successful checkpoint cache or
localization evaluation: the serialized mixing head emits an unconstrained
logit. Consistent with the official `rbpnet.prediction._to_probs` implementation,
`a_r` is the sigmoid-transformed value, not the raw head logit. A full-scale QKI
pilot detected the ambiguity by correctly rejecting raw values outside `[0,1]`;
the failed pilot wrote no profile or feature shard. This clarification changes
no representation family, summary, radius, model, fold, metric, or gate.

Exactly nine modeled summaries are frozen per RBP:

1. signed `sum(d_r)` in radius 10;
2. signed `sum(d_r)` in radius 25;
3. signed `sum(d_r)` in radius 50;
4. maximum `abs(d_r)` in radius 25;
5. global binding gained, `sum(max(d_r,0))`;
6. global binding lost, `sum(max(-d_r,0))`;
7. parent target-profile mass in radius 25;
8. parent mixing coefficient;
9. mutant-minus-parent mixing coefficient.

Global signed target-profile delta is a diagnostic invariant, not a feature,
because softmax normalization makes it zero. Gain/loss equality is checked
within numerical tolerance and preserved as separately named mechanistic
summaries, not expanded into additional pooling variants. No site caller,
arbitrary threshold, control profile, total profile, attribution map, or hidden
embedding is introduced.

R2 contains R0 plus the 927 channel summaries. Parent features are items 7-8;
delta features are items 1-6 and 9. Every cache must pass finite-value, profile-
sum, input-length, sequence-hash, checkpoint-hash, and parent-reuse tests.

## 7. Outcome-independent trans context

The exact construction is frozen in `reports/finalshot_trans_context.md` and
`results/finalshot/context_source_manifest.json`. For 98 canonically mappable
channels, `E[r,c]` is the equal-compartment mean of the soma and neurite
medians of `log1p(FPKM)` across three GSE67828 replicates. Five unresolved
human→mouse mappings receive no trans feature; no value is imputed.

M2/M3 add only elementwise, same-RBP terms:

- `E[r,c]` times each of the seven delta summaries;
- `E[r,c]` times each of the two parent summaries.

Raw context alone is not an identity shortcut input. There are no cross-RBP
products. Standardization is fit inside training folds.

## 8. Stability and structure

No reproducible external mutant stability predictor passed audit. No stability
or structure feature is authorized. GSE249405 contributes no data-derived
feature, coefficient, or target. Historical TDP EV5 stability is prohibited.
Gate I and stability permutation are not applicable rather than imputed as
successes. The exact decision is in `reports/finalshot_stability_prior.md`.

## 9. Matched representation comparison

R0, R1, and R2 are compared with the identical downstream learner:
training-fold `StandardScaler` followed by weighted Ridge with `alpha=100`,
fitted to the shared `[0,1]` rank target. R1 and R2 each include R0. Each
representation receives identical outer folds, decision tasks, weights, and
metrics. The comparison reports incremental value over R0; it does not choose
features by pooled row-level MSE.

The representation comparison is descriptive and mechanistic. It cannot add a
fourth representation or alter M1-M3 after results.

## 10. Frozen model family

There are exactly four main candidates.

### M0 — strong geometry baseline

R0, training-fold standardization, and weighted Ridge `alpha=100` on shared
rank target. This is the nuisance/shortcut comparator.

### M1 — RBP-delta model

R2 without trans interactions, fit to the shared rank target by sparse group
linear regression. Geometry is one unpenalized/light-ridge group. Each RBP's
nine summaries form one group. The weighted objective is squared error plus a
sparse-group penalty. Within-RBP group identity is preserved.

The fully nested grid is:

- group penalty `lambda ∈ {0.001, 0.01, 0.1}`;
- group fraction `eta ∈ {0.25, 0.75}`;
- fixed coefficient ridge floor `1e-5`.

FISTA/proximal optimization uses maximum 500 iterations, relative objective
tolerance `1e-6`, and deterministic zero initialization. Failed convergence is
reported and the candidate is ineligible in that fold; no grid expansion is
allowed.

### M2 — trans-conditioned RBP model

M1 plus the 882 allowed expression interactions for the 98 mapped channels.
Each interaction remains in its RBP group. The same fixed grid and optimizer
are used. There is no low-rank context embedding because only two cell states
exist and the elementwise biological interaction is lower-capacity and more
interpretable.

### M3 — mechanistic latent phenotype + measurement process

M3 uses M2 inputs, a sparse-group linear latent score `phi`, and one monotone
measurement head for each of five observed assay contexts: Mikl-CAD,
Mikl-N2A, TDP-CAD, Moffatt-GFP-CAD, and Moffatt-Firefly-CAD. Heads are either
positive affine functions or positive piecewise-linear functions with two
fixed training-score quantile knots. Softplus-constrained slopes guarantee
monotonicity. Heads cannot see sequence, parent, edit geometry, or identity.

The head form `{affine, two-knot}` and the same `lambda/eta` grid are selected
only by inner biological folds. Ties within 0.002 normalized regret choose the
affine head, larger `lambda`, and then larger `eta`. Joint weighted raw-effect
MSE uses Adam learning rate `1e-3`, batch size 2048, maximum 100 epochs,
gradient norm 5, and training-objective patience 10. Seeds are exactly
`[17, 41, 89]`; all are reported and averaged, never selected.

Scale nonidentifiability is controlled by centering and unit-scaling `phi` on
training rows during optimization. At transfer and evaluation, ranking uses
pre-head `phi`. No target head is estimated from target outcomes.

## 11. Nested model selection

Every M0-M3 receives outer-held predictions. For the primary nested FinalShot
prediction, M1-M3 and their hyperparameters are selected within each outer fold
by equal-source normalized regret, then rank percentile, then GoodSelection@3.
Ties within 0.002 regret ContextValue choose the simpler family M1, M2, M3 in
that order, stronger regularization, and the affine M3 head. M0 is always the
fixed baseline and cannot be displaced as the comparator.

Outer outcomes determine the scientific verdict but never trigger a new model,
threshold, radius, feature, or fold. A final full-development refit may archive
the selected recipe only after evaluation; it is not another performance test.

## 12. Mandatory mechanistic tests

### Mikl matched mechanism

Candidate matching uses cell line × motif family × intervention class ×
operation signature × edit-size band. Bands are the section 15 bands. A stratum
requires at least 20 candidates and five genes. At most two rows per gene are
retained by candidate SHA-256, without outcomes. Within each held gene's
existing decision set, matched subsets require at least four candidates.
Rank/regret ContextValue is computed on those subsets and macro-averaged by
gene and motif family. This asks whether RBP outputs distinguish outcomes after
generic motif/edit class is controlled.

### TDP mechanism

RBPNet has no TARDBP checkpoint. This limitation is frozen, not patched.
FinalShot reports available-channel group selection and the performance of
UG-rich/TDP-labeled motif perturbations after geometry matching. It may show
co-regulatory predictive value but cannot claim direct identification of
TDP-43 binding. Success driven only by edit size fails the mechanistic reading.

### Moffatt dense landscapes

All evaluation holds complete biological parents. Sensitive-subsequence value
is reported within intervention class and edit-size band. Eight eligible
parents remain eight units regardless of candidate count.

Selected RBP group stability is the fraction of outer folds in which each group
has nonzero norm, with coefficient direction and median norm. A claim centered
on an RBP requires selection in at least three of five folds or must be labeled
unstable/exploratory.

## 13. Mandatory transfer evaluations

All transfers fit scalers, penalties, latent functions, and available source
heads only on training outcomes:

- CAD→N2A and N2A→CAD, each direction separately;
- Firefly→GFP and GFP→Firefly, each direction separately;
- leave Mikl out, leave TDP out, and leave Moffatt out, each direction;
- standard held-gene/held-parent outer folds within source.

The held source has no head. Transfer uses the shared `phi`. Results compare M0,
R1 matched Ridge, M1, M2, and M3 on identical tasks.

## 14. Mandatory mechanism-breaking controls

Controls use seed `42017` unless M3's three optimization seeds apply. Each is
retrained through the same nested procedure where retraining is meaningful.

1. **RBP identity permutation:** for each intervention, a deterministic
   sequence-pair-hash-seeded permutation reassigns complete nine-feature RBP
   blocks. Parent and delta summaries move together. Geometry and the within-row
   multiset of RBP values are preserved, but channel identity is inconsistent
   across interventions; expression remains attached to biological RBP names.
2. **Delta-RBP intervention permutation:** the complete delta block is shuffled
   across biological units within dataset × cell line × operation signature ×
   edit band × motif family. Only strata with at least two biological units and
   five rows are eligible; sparse rows are excluded from this control rather
   than rematched more loosely. Parent and geometry remain fixed.
3. **Cell-context permutation:** CAD and N2A expression vectors are swapped for
   compatible Mikl rows. Sequence, geometry, and outcome assignment remain
   fixed. CAD-only sources are not relabeled as a nonexistent N2A assay.
4. **Parent-binding knockout:** items 7-8 and their expression interactions are
   removed.
5. **Trans-interaction knockout:** M2/M3 are refit without every `E × binding`
   term, reducing to the corresponding M1 feature space.
6. **Stability permutation:** not applicable because no stability block exists.
7. **Geometry-only:** M0.
8. **Measurement-head randomization:** M3's fitted head parameter blocks are
   deterministically permuted across the five assay contexts at calibration
   evaluation. Calibration MSE/Spearman must degrade; pre-head latent ranking
   must remain bitwise unchanged.

## 15. Shortcut tests and edit-size bands

A weighted Ridge predicts `log1p(edit_cost)` from delta-RBP summaries and a
class-balanced multinomial logistic regression (`C=0.1`) predicts intervention
class. Both use held biological folds and report R-squared and macro-F1 against
geometry comparators. Predictability is not itself disqualifying; the decisive
test is incremental value within the frozen matched strata.

Edit-size bands are exactly:

- exact 1 nt, descriptive only;
- 2-5 nt;
- 6-10 nt;
- combined 2-10 nt;
- 11-25 nt;
- 26-50 nt;
- greater than 50 nt.

No band may be merged or rethresholded after results. Directional increase and
decrease are always separate.

## 16. Metrics and uncertainty

Primary metrics per directional decision task are normalized regret, selected
measured utility, selected normalized utility, GoodSelection@3,
GoodSelection@5, directional rank percentile, and within-set Spearman. Exact
oracle recovery is descriptive. ContextValue is full minus M0 for larger-is-
better metrics and M0 minus full normalized regret.

Biological-unit ContextValue, fraction improved, median, leave-best-one-out
mean, and a paired 10,000-resample biological-unit bootstrap with seed `42017`
are reported. Bootstrap resamples units within source and preserves both
directions of a unit. Favorable row-level confidence intervals are forbidden.

## 17. Frozen gates

All gains are paired on identical held-out tasks against M0.

- **A — overall mechanism value:** equal-source/direction rank ContextValue at
  least `+0.020` **and** normalized-regret ContextValue at least `+0.010`.
- **B — distributed units:** positive median unit regret ContextValue; at least
  55% of units improve; leave-best-one-out mean above zero; paired-bootstrap
  95% lower bound no worse than `-0.005`.
- **C — Mikl matched mechanism:** matched held-gene rank ContextValue at least
  `+0.010` and regret ContextValue at least `+0.005`, both positive by motif-
  family macro-average.
- **D — leave-source-out:** at least four of six source×direction tasks have
  positive regret ContextValue; mean rank ContextValue is positive; mean regret
  ContextValue is at least `+0.010`; no single source contributes more than 75%
  of the sum of positive regret gains.
- **E — cell/reporter transfer:** at least three of four directional cell tasks
  and three of four directional reporter tasks have positive rank and regret
  ContextValue; each four-task mean regret ContextValue is at least `+0.005`.
- **F — small-edit bridge:** combined 2-10 nt has rank ContextValue at least
  `+0.020` or regret ContextValue at least `+0.010`; the companion metric is no
  worse than `-0.002`; neither 2-5 nor 6-10 regret ContextValue is below
  `-0.005`. Exact 1 nt cannot pass this gate.
- **G — RBP necessity:** both RBP identity permutation and delta-RBP shuffle
  eliminate at least 50% of the observed gain in at least one Gate A metric;
  their mean retained gain across rank/regret is at most 50%; neither control
  independently meets both Gate A thresholds.
- **H — trans context:** M2/M3 must beat its trans-interaction knockout on the
  crossed cell-transfer mean by regret `+0.005` or rank `+0.010`, with the other
  metric no worse than `-0.002`; otherwise trans context is dropped.
- **I — stability:** not applicable; stability is excluded prospectively.
- **J — measurement process:** M3 must beat direct M2 on leave-source-out mean
  by regret `+0.005` or rank `+0.010`, with no more than one source×direction
  task worsening in regret by more than 0.020; otherwise M3 is dropped.
- **K — optimization stability:** across M3 seeds, equal-source rank and regret
  standard deviations are each at most 0.010 and the categorical M3-vs-M2
  conclusion agrees for all seeds. Deterministic M0-M2 must reproduce within
  `1e-8` on a repeated smoke fold.
- **L — integrity:** all leakage, grouping, hash, permutation, cache, source-
  holdout, and protected-data tests pass; no target-parent outcome is used.

## 18. Directional and final verdict rules

A direction has meaningful evidence only if its within-source, leave-source-
out, and 2-10-nt regret ContextValues are positive; its overall rank
ContextValue is positive; and at least 55% of its biological units improve.

`FULL GO — ORIGINAL RNADDRESS SURVIVES` requires Gates A-H and J-L, both
directions meaningful, no source/edit-size shortcut explanation, and all eight
substantive requirements in section 40 of the controlling prompt. Inapplicable
Gate I does not count as failure or success.

`PARTIAL GO — BIOLOGICALLY REAL BUT NARROW` is allowed only for a real,
distributed, mechanism-control-supported effect that is restricted to one
direction, assay family, or larger edit regime. It does not establish the
original universal compiler and does not authorize Astrocyte use.

Otherwise the verdict is `NO-GO — END ZERO-SHOT RNADDRESS`. No B4/B5, new
representation search, revised threshold set, or another zero-shot cycle is
authorized after NO-GO. The next eligible hypothesis is RNAddress-Adapt, under
a separately defined few-shot active-design protocol.

Even FULL GO only justifies considering a separate prospective Phase C
protocol. Astrocyte remains sealed in every FinalShot verdict.

## 19. Reproducibility and fail-closed conditions

The run records source-table hashes, exact eligible sequence hashes, checkpoint
hashes, cache keys, runtime versions, fold membership, weights, hyperparameters,
seeds, exclusions, group norms, predictions, and every metric under
`results/finalshot/`. Scripts must never import a protected Astrocyte or N-zip
outcome path. Tests scan code and manifests for those boundaries.

Stop without definitive modeling if checkpoint hashes change, target profiles
cannot be reproduced, sequence lengths/mappings are inconsistent, the v4 cohort
or folds do not match frozen counts, a provenance error appears, protected data
are accessed, or any model requires target intervention outcomes. A technical
failure is reported; it is not patched by changing the scientific question.

## 20. Final interpretation

Before verdict writing, perform the nine-query novelty refresh required by the
controlling prompt and prioritize primary papers/repositories. Any novelty
claim must be narrow and qualified. The final report must answer all 60 required
return items, including explicit not-evaluated/not-applicable entries, exact
tests and commits, Astrocyte status, and whether a PV-CARE-level path remains.
