# Independent methods review, 7 October 2026

This is an additive review of `cross_assay_20260927`,
`probabilistic_ranking_20260928`, their exposed canonical inventories, and the
earlier Mechanism-v2 design. No historical file was modified, no biological model
was refitted for this audit, and no new, reserved, or quarantined outcome was
opened. Existing reports are evidence to inspect, not assumed correct by fiat.
This review has not independently reconstructed every public raw measurement or
replayed every old saved prediction; those remain separate integrity questions.

## What the inspected implementation gets right

- The rank loss uses within-parent/context candidate differences, with positive
  label meaning larger measured destination effect. Decrease recommendations
  reverse the same scores and outcomes. The primary utility score is not treated
  as an absolute effect probability. The regret formula is consistent with this
  definition (`cross_assay_20260927/models.py:13`, `metrics.py:20`).
- Both directions use the same roster and equal weight. Consequently the exact
  uniform-expectation regret is 0.5 after averaging directions, independent of the
  asymmetry of measured effects. The directions are paired questions about the
  same measurements, not independent experiments.
- The study/component/context/pair hierarchy in training matches the intended
  biological aggregation in evaluation. Large libraries do not simply receive
  weight proportional to their candidate count (`models.py:7`, `metrics.py:36`).
- Mean and standard deviation are fitted on training rows. A parent-constant
  feature cancels in a linear pair difference; subtracting the global training
  mean does not remove a transferable within-parent linear contrast. Scaling can
  nevertheless change that contrast's effective regularization (`models.py:37`).
- Whole-study holdout includes all study reporters/cells and explicitly purges
  held global gene/exact-allele components. There is a second exact-allele guard.
  Single-component SRLE is correctly ineligible for held-parent validation
  (`models.py:81`, `dataset.py:37`). This verifies the implemented guard's intent,
  not completeness of biological family annotations.
- Soft-label noise pools use only training pairs and training replicate slots.
  Missing Moffatt replicate contrasts explicitly fall back to aggregate labels.
  Cross-replicate diagnostics use training-slot means rather than the processed
  aggregate containing evaluation slots (`probabilistic_ranking_20260928/models.py:5,27`).
- The soft-loss gradient and probability construction are algebraically
  consistent on inspection. Calibration evaluates empirical replicate support,
  not its smoothed working target. Pairwise probabilities are distinguished from
  improvement-versus-WT probabilities. Same-parent cross-replicate results are
  correctly described as measurement robustness, not biological generalization.

No definite implementation error invalidating the principal historical regret
values was identified in this review. That finding is narrower than certifying
every input mapping, resource, or scientific interpretation.

## Concrete limitations and discriminating diagnostics

1. **Sparse pair supervision in saturated libraries.** The frozen admitted hard
   training-pair inventory directly includes only 2,382/3,984 Astrocyte candidates
   (59.79%) and 3,840/6,749 Moffatt candidates (56.90%). Mikl and SRLE include
   every candidate. These counts were independently computed from the saved
   `left`/`right` indices and `historical_train_eligible`, without fitting.
   Outcome-blind sampling is legitimate, but about 40–43% of candidates in the
   saturated sources never directly constrain the rank objective. Compare the
   original 256 pairs with a larger fixed, outcome-blind cap, holding features,
   weights, scaler and source-only model selection fixed. This tests approximation
   sensitivity; it does not establish the old sampling was erroneous.

2. **Regularization is coupled to the wrong possible geometry.** The old scaler
   uses candidate variance across contexts, while the loss uses within-context
   differences, at one fixed L2=0.05. Pair RMS can isolate the geometry that enters
   the loss. A read-only check found most active pair-RMS/candidate-SD ratios near
   1.18–1.41, so broad attenuation of sequence signal is not established. The
   lowest ratios, 0.22–0.58 depending on held study, mainly concern edit-size/span
   metadata. Compare candidate scaling with weighted pair RMS at the frozen
   L2 grid [0.005, 0.05, 0.5], selecting solely inside training-assay holdouts.
   This is a modeling diagnostic, not a discovered software bug.

3. **Pooled labels encode different destinations.** Neurite/soma, synaptoneurosome/
   cortex, and nuclear/cytoplasmic localization are not interchangeable molecular
   outcomes. Ranking avoids incompatible raw numerical scales but does not make
   their sequence effects identical. Core SRLE has no second nuclear source;
   nuclear-domain transfer is thus extrapolation across endpoints. Compare
   all-source versus prospectively endpoint-compatible training, using the same
   recipient candidate sets and documenting ineligible nuclear transfer. A
   successful projection model would support a narrower claim, not universality.

4. **The current representations have limited ordered context.** The original
   features stop at 1–3-mer changes and coarse parent-composition interactions.
   Most unchanged sequence order and long motif interactions are absent. Wider
   windows change those composition interactions, not the 1–3-mer allele delta.
   Exact feature-collision bounds do not establish adequate biological capacity.
   The already exposed frozen-BERT comparator improved matched two-study regret
   in both Mikl and Moffatt; it is a specific lead, with incomplete four-study
   coverage and inherited mixed-runtime provenance. Test longer ordered local
   words, admitted frozen mechanistic deltas, or trustworthy frozen embeddings
   under the same purged source-only selection. Matched dimension and simple
   sequence controls are needed before a mechanism claim.

5. **Full biological context is unavailable for some assays.** SRLE supplies a
   six-mer placed in one HBB reporter, not a fully reconstructed transcript or
   construct. Length, boundary status and local frequencies then encode assay
   design, and structure computed from that six-mer alone would not describe the
   reporter. Do not invent flanks. Keep a coverage ledger and compare context-
   complete cohorts on identical sets; report SRLE limits explicitly.

6. **The rank objective does not optimize extreme-selection loss directly.**
   Every sampled non-tied pair has a hard ordering preference, regardless of
   effect magnitude. Small, noisy differences can dominate pair statistics while
   a few extreme choices determine regret. Candidate count, near-tied effect
   range, and optimistic observed extrema also affect normalized regret. Preserve
   the primary metric, while reporting raw within-assay regret, pair ordering,
   extreme recovery, replicate evaluation and set size together. Any alternative
   objective needs a separate freeze and training-only selection; do not filter
   test candidates or weaken the gate after seeing outcomes.

7. **The uncertainty experiment changes both targets and effective shrinkage.**
   Raw replicate win fractions differ from processed author preferences, and P2
   draws probabilities toward 0.5 while retaining the same L2. The Hraw control
   helps separate estimator changes, but one failed representation/penalty cannot
   rule out uncertainty as a broader contributor. A training-only temperature
   calibration of H0 is a useful shrinkage reference: it preserves candidate
   order while potentially improving probability scores. P3 models sign of a
   latent mean; that is not identical to another-replicate win probability.
   Few potentially correlated technical slots and shared experimental processing
   further limit Beta/normal uncertainty claims. All-primary Brier/log-loss worse
   than constant 0.5 establishes failure of these probabilities on that empirical
   endpoint; it does not alone identify the biological cause of transfer failure.

8. **Biological breadth and repeated exposure remain the limiting evidence.**
   The four sources have 2, 187, 6 and 1 components. Exact allele and same-gene
   grouping protects specified overlaps but does not certify near-sequence,
   ortholog/paralog or unseen full-context independence. Bayesian component
   bootstrap is degenerate for SRLE and does not estimate a population of future
   assays. Source coefficient sign reversals are associations in correlated,
   regularized features; the meta-shrink working penalized-Hessian variances are
   not independently estimated biological uncertainties. Preserve historical
   failures and use reused data for diagnosis. A new positive development result
   still needs trustworthy independent confirmation and a precise endpoint claim.

## New implementation boundary

`src/generalization_20261007/route_scaling.py` supplies the unchanged 246-feature
matrix, six frozen scaling/penalty configurations, training-only scaling, and
explicit zero coefficients for columns unsupported by training pair contrasts.
The shared runner owns nested source selection, purging, outcome access and the
prefit freeze. This module does not execute a biological fit on import.
`test_scaling.py` checks analytic pair RMS, parent-offset invariance, synthetic
direction recovery, parameter replay and unsupported-column freezing, using no
biological outcomes. No newly implemented route is declared successful here.
