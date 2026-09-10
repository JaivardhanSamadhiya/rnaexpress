# RNAddress-Mechanism-v2 — prospective design ledger

Status: development design, **not a final evaluation freeze**. Created 9 September
2026 before any Mechanism-v2 localization model or probe has been fit.

## Boundaries

FinalShot at `98ffc02` is an immutable negative experiment, not a model to patch.
All new evidence is namespaced. Certified Mikl GSE173098, TDP43 GSE288185 and
Moffatt GSE334718 are the only localization development outcomes. N-zip outcomes
and quarantined TDP stability data are excluded. Astrocyte data are unopened;
this development implementation intentionally has no usable holdout loader.
Holdout access requires a later complete, committed system/protocol/hash freeze,
reviewed authorization and one-shot opening ledger. A CLI flag is not consent.

These development datasets have already been examined repeatedly in earlier
RNAddress experiments. New nested evaluations are leakage-controlled estimates
on a **reused benchmark**, not fresh independent confirmation. Resource choice
and redesign are informed by the known failures and must be described as such.

## Audit choices committed before new forensic probes

Recompute archived predictions using the old metric implementation, without
retraining or overwriting anything. Report geometry comparisons by source,
biological unit, parent, direction, size and mutation class; retain archived
transfer/control results with provenance. Distinguish recomputation from merely
checking a summary. Historical Git audit covers the Mikl cap, tie order and
measurement-head criterion. Both uncapped and literal-cap interpretations must
be reported; if the literal cap leaves no evaluable subsets, say so.

Diagnostic prediction reconstruction uses grouped out-of-fold Ridge (alpha 100)
and a shallow random forest (100 trees, max_depth 4, min_samples_leaf 20, seed
20260909). Inputs: geometry, size/class, GC/length/location, parent/source/reporter
identity when legally evaluable, RBP absolute summaries, RBP deltas, and geometry
plus deltas. Targets are archived frozen model scores, not new outcomes. Report
weighted out-of-fold R-squared and incremental R-squared as predictive diagnostics,
not causal mediation. Parent-label decoding with unseen held-out labels is not a
valid classification task. The two directional tasks often share identical
covariates; direction decodability must state this identifiability limitation.
Additional representation probes, if run, are exploratory and do not define gates.

## Representation and resource admission

Audit Parnet release **0.3.0**, its official history and the IR_iPSCs supporting
repository. Require checkpoint SHA, source commit, true parameter count, output
schema, license and native-length inference validation. A newly recovered model
must be distinguished from the previously excluded artifacts. Never train a new
encoder on RNAddress and call it pretrained. RBPNet remains an independently
identified fallback, with its missing TARDBP channel and human-to-mouse limits.

Primary representations are explicit mutant-minus-reference outputs of one frozen
external model. No edit geometry or absolute parent block is silently appended.
Signed differences and symmetric perturbation magnitudes are separately named;
normalized-profile positive/negative mass are not two independent mechanisms.
Local ViennaRNA features use declared coordinate alignment and matched ref/mut
windows, with settings, version and sequence/model/config cache hashes recorded.
Independent stability training uses external time-course outcomes only. Processing
motifs are nuisance flags, not validated splice probabilities or localization
causes; full reporter context is required before using a genomic splice predictor.

Families M0–M7 follow the controlling prompt exactly: geometry; delta sequence/RBP;
delta structure; independent stability/processing; sequence+structure;
sequence+stability/processing; all admitted mechanisms; all plus external trans
interactions. Unsupported resources remain excluded, not filled with artificial
zeros. A parent-aware model is a separate comparator, never part of the primary
latent representation. Shared latent scores cannot receive source identity.

## Evaluation constraints to resolve before outer model evaluation

Biological parents/genes and duplicate-derived observations stay together. Build
outcome-blind connected groups for exact sequence overlap, with declared near-
sequence and gene-family sensitivities. Fit preprocessing and any nuisance
residualization only on inner training folds. Compact ranking-first candidate
grid, optional simple source heads, uncertainty and abstention rules are selected
within training folds. Freeze exact grid/splits/resources before outer evaluation.

Tie order must be a total deterministic order: minimum primary regret; candidates
within a declared tolerance are compared by declared secondary rank, then model
simplicity, then lexical recipe ID. This order is specified once in configuration
and tested; no prose with a contradictory second tie rule.

True permutation controls act on unique intervention blocks, separately inside
each training/validation/test partition. Global/source/size/parent/joint-stratum
nulls use each donor once. Fixed points are recorded; a cross-parent derangement
that is mathematically impossible is ineligible, never repaired by donor cycling.
All full/control comparisons use the same eligible units and paired bootstrap.

## Gates

No numeric gates have been relaxed. Before outer evaluation, write an explicit
frozen protocol retaining scientifically useful improvement, broad-unit support,
transfer, 2–5 and 6–10 nt harm limits, necessity and integrity requirements. The
old near-miss fraction is not grounds for reducing the unit-support threshold.
Exact SNVs with too few independent parents cannot substantiate universality.
Limited support is not automatic PARTIAL GO: any restricted domain must be
specified without selecting a favorable outer-results subgroup. A failed new
experiment ends universal zero-shot claims; RNAddress-Adapt is only a future plan.
