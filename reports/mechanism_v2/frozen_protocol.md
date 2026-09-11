# Mechanism-v2 frozen outer-evaluation protocol

Status: **frozen before any outer-fold outcome has been scored.** This document
and `configs/mechanism_v2/frozen_gates.json` together are the controlling
specification for the single outer evaluation. They retain, without weakening,
every numeric requirement already written in
`reports/mechanism_v2/prospective_gate_design.md` on 10 September 2026.

Nothing in this protocol authorizes Astrocyte access. The holdout loader does
not exist; `src/mechanism_v2/io.py::open_holdout` refuses unconditionally.

## What is already fixed and may not change

* Candidate inventory: the two hash-pinned certified development tables,
  93,208 candidate rows over 445 decision sets and 213 biological units.
* Grouping and splits: the all-allele 95% connected components (211 groups),
  five outer folds and their three inner component assignments, read from
  `results/mechanism_v2/manifests/splits_all_alleles95.json`.
* Feature blocks: the six hash-pinned mutation-induced blocks plus archived
  geometry, exactly as recorded in `results/mechanism_v2/features/`.
* Model grid: 48 recipes (eight families x six variants) with the constants in
  `configs/mechanism_v2/localization_design.json`.
* Inner selections: the 720 completed inner-only fits and the five committed
  `selection.json` records, verified in
  `results/mechanism_v2/training/status/verified_0720_fits.json`.
* Tie order: minimum regret inside a 0.002 window, then highest rank, then fewer
  columns plus nuisance/head parameters, then lexical recipe ID. One rule, tested.
* Gate thresholds, eligibility minima, bootstrap design and the three allowed
  verdicts: `configs/mechanism_v2/frozen_gates.json`.

## The outer evaluation contract

For each outer fold `k` in 0..4:

1. The training partition is every candidate row with `outer_fold != k`; the
   evaluation partition is every candidate row with `outer_fold == k`.
   `fitting.assert_outer_boundary` refuses anything else, including a partial
   fold, a repeated fold or a training set that contains a single evaluation row.
2. The recipe is the one the committed inner-only selection already chose from
   fold `k`'s development rows. `outer_evaluation.selected_recipes` reads it and
   fails if the record claims outer outcomes were used or if its freeze hash
   differs. No recipe is chosen, re-chosen, ensembled or averaged here.
3. Preprocessing (weighted centering and scaling), the nuisance matrix and any
   source ranking temperature are estimated from training rows only, inside
   `PairedRanker.fit`.
4. The fitted model scores the evaluation fold exactly once. Predictions, the
   serialized model, the training/evaluation row-identity digests, the component
   and intervention purge audit, the convergence audit and the feature
   provenance digest are all recorded before any metric is computed.
5. Because connected components never cross folds and a decision set never
   crosses a component, every decision set is scored by exactly one model whose
   training partition excluded it. Concatenating the five folds therefore gives
   complete, non-overlapping candidate coverage, which is the primary estimand.

Replay is content-addressed: re-running a completed fit re-verifies the identity
record and the artifact hashes and refuses to overwrite a differing result.

## Metrics and weighting

`evaluation.decision_metrics` is unchanged from the inner stage. Within each
decision set it computes both directions from the same shared latent score
(decrease uses its negation), normalized regret and normalized rank of the
selected candidate, Good@3, Good@5 and the random expected regret, plus a
candidate/outcome cohort SHA-256. `evaluation.pair_comparison` refuses to
compare two models whose eligible decision sets, candidate counts or cohort
hashes differ. Gains are averaged within source/component/direction and then
over source x direction contexts equally.

Uncertainty is the paired connected-component bootstrap with 10,000 replicates
at seed 20260909; a component travels with both of its directions and all of its
cross-source remeasurements. More than 1% of replicates missing a required
context makes the interval ineligible rather than silently redefined.

## Controls, necessity and transfer

* Every applicable null (N1, N2, N4, N5 global/source/edit-band/parent, N6, N7,
  N8 joint, N9) is refit with the same six recipes and the same inner-only
  nested selection, then scored once per outer fold. N0 is the geometry baseline
  itself. N3 is ineligible and says why. N10 does not exist because independent
  stability admission failed; it is never zero-filled.
* Permutations act on unique interventions and are constructed separately inside
  the training rows and inside the evaluation rows of each partition. Donors are
  used once per stratum, fixed points are recorded, singleton strata are
  ineligible and donors are never cycled to repair an impossible derangement.
* A null comparison is restricted to decision sets in which every candidate is
  eligible, applied identically to the null and to the full model, so the cohort
  hashes still match.
* The N7 donor reference profile is pooled at the **recipient's** edit window.
  Strata are source x native sequence length x edit band, which is what makes
  that pooling well defined, with a cross-component derangement requested.
* Block removals use the already-selected recipe with one named block removed and
  refit entirely on training rows. Holm correction is applied across all seven
  enumerated hypotheses; an absent component receives p = 1 and no claim.
* Transfer tasks come from the committed outcome-blind purged inventory. Recipes
  are re-selected inside each task's own training domain using that task's
  committed inner component folds. The one GFP-to-Firefly fold with no eligible
  held group is reported ineligible, not passed.

## Integrity requirements

* Only `tests/mechanism_v2` is ever run. Legacy tests can load protected N-zip
  or Astrocyte inputs and are excluded by construction.
* `prepare-outer` verifies that every code file, design document, configuration,
  split inventory, feature manifest and inner selection record is committed at
  HEAD with a matching content hash before outer evaluation is authorized.
* Any write outside the Mechanism-v2 namespaces is refused. Evidence records are
  write-once: an identical replay is allowed, a differing record is an error.
* The selected recipes are refit at seeds 20260910 and 20260911 without any
  reselection against outer outcomes. A same-seed refit in a separate namespace
  must reproduce the frozen score to 1e-8.

## Amendment rule

If a genuine pre-result software or integrity defect makes a specified analysis
impossible, the defect is preserved and documented in
`reports/mechanism_v2/implementation_incidents.md` and the analysis is reported
ineligible. Thresholds are not moved, analyses are not swapped for easier ones,
and a favorable subgroup discovered in outer results can never become a
restricted domain. The only prospective restricted domain is 2-10-nt
interventions in the covered neuronal/neuron-like reporter contexts.

## Verdict rule

Exactly one of the three allowed verdicts is reported. A development-only
result, however favorable, cannot be a GO: STRONG GO additionally requires the
completely frozen one-time Astrocyte test, and PARTIAL GO requires the
prospectively named restricted domain to pass every criterion with adequate
independent confirmation. The historical FinalShot conclusion
`NO-GO — END ZERO-SHOT RNADDRESS` is preserved unchanged in every outcome.
