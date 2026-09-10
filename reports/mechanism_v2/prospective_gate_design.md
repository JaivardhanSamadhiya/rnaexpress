# Mechanism-v2 prospective acceptance and control design

Written before new localization fitting or outer results, 10 September 2026.
These rules are input to the eventual `frozen_protocol.md`, not a claim that all
evaluation code, controls, reports or final models have already been frozen.
They cannot be weakened in response to new results. Unavailable or underpowered
required evidence is **ineligible**, never an automatic pass.

## Estimand and eligibility

The primary estimand is equal-source/equal-direction improvement of the inner-
selected M1–M7 intervention selector over inner-selected M0 on identical candidate
sets. Within each source/direction, average decisions within connected biological
component and components equally. Full candidate coverage is primary. Positive
rank gain and positive normalized regret reduction both favor the selector.
Compute paired component bootstrap with 10,000 replicates and seed 20260909.
Resample each connected component once, retaining both directions and its
cross-source remeasurements together. If over 1% of replicates lack a required
context, do not present the interval as eligible confirmation.

Decision sets need at least two distinct candidate IDs and nonzero outcome range.
Candidate and outcome hashes must match across compared models. A restricted
subanalysis needs at least 20 independent components overall to support a formal
claim. Source/direction transfer tasks need at least three independent components
and three eligible decision sets; otherwise report point estimates descriptively.
The special Mikl motif-mechanism subanalysis retains its four-candidate minimum.
These eligibility minima reflect the small experimental units, not the many
candidate rows. They do not make narrow intervals with very few units trustworthy.

## Universal development gates (all required)

1. **Useful selection:** overall rank gain ≥0.020 AND regret reduction ≥0.010.
   Both correspond to useful movement on normalized intervention-selection scales
   and retain the old scientific expectations. The absolute selected performance,
   random expected regret, Good@3 and Good@5 are also reported.
2. **Distributed benefit:** median component regret gain >0, ≥55% of components
   improve, leave-best-component-out mean >0, and the paired 95% lower bound for
   both primary gains ≥−0.005. Retain the 55% threshold despite the old near miss.
   Report quartiles and worst-decile mean, not just these acceptance statistics.
3. **Matched edits:** within original decision set × fixed edit band × mutation
   class, rank gain ≥0.010 and regret gain ≥0.005, with ≥20 components. Report
   source/parent-matched versions and Mikl motif-family macrovalues separately.
   Both uncapped and literal two-per-gene cap sensitivities are required. An
   impossible cap-plus-four-minimum sensitivity is reported as unevaluable.
4. **Leave-source:** all three sources withheld separately with connected-group
   purging. At least 4/6 source-direction tasks improve both rank and regret;
   macro regret gain ≥0.010, macro rank gain >0; no source provides >75% of total
   positive source-level regret gain. No task may trigger the hard harm rule.
5. **Cross-cell and cross-reporter:** use the existing paired Mikl CAD↔Neuro-2a
   and Moffatt GFP↔Firefly frameworks, but hold connected groups out across
   contexts rather than allowing a measured mutant to serve as its own transfer.
   At least 3/4 cell-direction tasks and 3/4 reporter-direction tasks improve both
   metrics, and each macro regret gain ≥0.005. Context training/selection uses
   only the allowed source side. Paired-context transfer with the same parent
   in training can be a clearly labeled diagnostic, never the zero-shot gate.
6. **Small edits:** for 2–10 nt, rank gain ≥0.020 OR regret gain ≥0.010, with
   companion gain ≥−0.002; BOTH 2–5 and 6–10 bands have regret gain ≥−0.005.
   Report 0, exact 1-nt SNVs, 2–5, 6–10, 11–25, 26–50, >50 separately without
   moving edit definitions. Exact SNVs require independent adequate evidence,
   potentially supplied by the one-time holdout; absence is not generalization.
7. **Mechanistic necessity:** full mechanistic deltas must beat the prospectively
   specified nulls, including matched-dimensional frozen random sequence features,
   absolute features and broken reference pairing. Global and joint source ×
   edit-band bijections must each destroy ≥50% of at least one useful-selection
   gain; mean retained gain across the two primary metrics ≤50%; neither null
   may meet both useful-selection thresholds. Retention is undefined when the
   full gain is nonpositive; it is not clipped into a pass. At least one biologically
   interpretable block must show paired removal harm ≥0.005 regret OR ≥0.010 rank,
   companion gain ≥−0.002, with Holm-adjusted one-sided p<0.05. These are predictive
   necessity tests, not experimental proof that an RBP mediates localization.
8. **Shortcut resistance:** no source label or absolute parent channel enters
   the primary latent score. Matched-stratum and true partition-local permutations
   must preserve the conclusions above. Report source, reporter, edit-size/class,
   parent/gene and direction probe performance with legal grouping; strong
   decodability alone neither proves nor disproves a shortcut. Unseen parent/gene
   label classification is ineligible, not a zero-accuracy success. No biological
   mechanism may be claimed if a simpler null reproduces its utility.
9. **Stability and integrity:** repeat selected-recipe fitting at seeds 20260910
   and 20260911, without reselection against outer outcomes. Primary-gain SD ≤0.010
   and gate-category agreement across seeds. Same-seed replay prediction tolerance
   1e-8. All split, feature, model, cohort, cache and sealed-data tests must pass.
10. **Hard harm:** no eligible source-direction, cell-direction, reporter-direction
    or small-band task has regret gain <−0.020. Overall worst-decile component
    mean regret gain must be ≥−0.200. These explicit harms are in addition to,
    not substitutes for, positive mean and small-edit requirements.

If selected M7 relies on trans context, it must improve genuine cross-cell
transfer versus M6 by ≥0.005 regret OR ≥0.010 rank, companion gain ≥−0.002,
and survive a paired context-identity necessity test. Otherwise no trans claim.
Its presence does not excuse a failing selector. Optional head usefulness uses
the same gain thresholds on leave-source transfer and permits at most one
source-direction regret harm >0.020; universal hard-harm limits still apply.

## Exact control estimands

All transformations operate separately inside each inner training, validation
and outer test partition. Use unique intervention IDs, then replicate features
to repeated candidate rows. No direction-specific donor shuffling: both directions
share the same biological score. A true bijection may have fixed points; record
them. Singletons are ineligible for matched null comparisons. No cycling smaller
groups. Use seeds 20260909–20260911 for permutation robustness.

- N0: selected geometry baseline; N1: fixed edit-size/class descriptors.
- N2: geometry with source-specific learned slopes, diagnostic only; unseen
  sources use a pooled training-only fallback, with coverage explicitly stated.
- N3: parent identity diagnostic only where labels are legal. Shared constant
  parent intercepts cannot change within-parent rankings. Do not train/test
  identical parents and call this zero-shot evidence.
- N4: 540-dimensional fixed random projection of reference/mutant 1–4mer sequence
  counts, same seed and same function on both alleles. Compare with M1 using
  the same six downstream recipes and nested selection. A higher-dimensional
  random vector does not increase the underlying kmer information rank.
- N5/N8: whole-delta intervention bijections: global, source, edit band,
  biological parent, and joint source × edit band. All use every eligible donor
  exactly once per partition; primary necessity uses global and joint controls.
- N6: absolute mutant RBP and pooled BERT, matched to M1's 540 columns. Also
  report reference-only and separately parent-aware M1 comparators.
- N7: mutant minus an independently assigned reference, within source × native
  sequence length × edit band. BERT uses the same absolute allele encoder. RBP
  donor-reference profiles must be pooled at the RECIPIENT's edit window, not at
  the donor intervention's unrelated window. Require a cross-component bijection
  where possible; ineligible strata are explicit. Full/geometry comparisons use
  the same eligible rows. This is a pairing perturbation, not plausible biology.
- N9: structure block bijection within source × edit band; other blocks preserved.
- N10: inapplicable because independent stability admission failed, never filled
  with a fake stability score or called a passed stability necessity control.

RBP identity is permuted per intervention over whole four-summary channels so
the summary roles stay aligned. A single global column renaming of a freely
learned linear model is mathematically invariant and is NOT a valid necessity
test. Trans identity controls mismatch the externally named RBP availability
weights, not merely relabel a free coefficient vector. Report both limitations.

Retrain each applicable null with the same six downstream recipes and inner-only
selection. Block-removal controls use the selected recipe with only the named
block removed, refit entirely on training data. Enumerate the formal block
removal family (RBP, BERT, structure, processing, motifs, trans, heads) before
evaluation and apply Holm to all seven hypotheses; absent components get no claim
and p=1 for family accounting. Report paired effects/intervals alongside p-values.

## Transfer, sensitivity and decision boundaries

Within-source held-group estimates, leave-source, purged cross-cell/reporter,
large-to-small (>10 to 2–10, held components), 90% sequence-cluster sensitivity
and externally justified gene-family sensitivity are required. A parent-only
90% sequence audit or shared gene symbol is not an external family ontology.
Pending family-resource/sensitivity implementation is an explicit outstanding
prerequisite, not a passed analysis. Missing-context transfer is never zero-filled.

No post-hoc restricted domain can obtain PARTIAL GO. The one prospective narrower
domain is **2–10-nt interventions in the covered neuronal/neuron-like reporter
contexts**, retaining the same useful-selection, distributed-benefit, matched,
transfer, necessity and harm criteria on that domain. It still requires adequate
independent confirmation; a favorable subgroup from outer results is insufficient.

STRONG GO additionally requires the completely frozen one-time Astrocyte test to
meet rank ≥0.020, regret ≥0.010, ≥55% improved units, median >0, both 95% lower
bounds ≥−0.005 and the same hard-harm limits, with eligible small-edit evidence.
PARTIAL GO needs the corresponding prospectively restricted evidence; neither
verdict follows from development metrics alone. Preserve historical FinalShot
NO-GO in all outcomes. No Astrocyte file is opened by this specification.
