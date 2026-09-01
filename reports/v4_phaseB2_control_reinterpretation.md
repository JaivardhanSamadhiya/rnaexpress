# RNAddress v4 Phase B2 control reinterpretation

Freeze date: 2026-09-01

Phase B commit `6ce5729fd31554e719588b8a940b0288ce0c827c` and its `NO-GO` verdict are permanent.

## What Phase B established

Phase B's context-permutation control retained rank `0.5978` and regret `0.4288` because it deliberately preserved intervention geometry. The result remains a failed prospectively frozen Phase B control and is not altered here.

The scientific interpretation is narrower than “permutation should be random.” Edit size, operation family, location and composition carry genuine total predictive signal. Therefore destroying parent context while preserving those features should approach the geometry/metadata baseline, not exact random selection.

## Phase B2 null and alternative

- Null: parent state and sequence-dependent edit context add no reproducible selection value beyond cross-fitted intervention geometry and assay-design nuisance.
- Alternative: authentic parent context improves held-biological-unit selection beyond the same cross-fitted nuisance baseline.

Phase B2 defines positive ContextValue so that larger is always better:

- rank ContextValue = `rank(full) - rank(nuisance)`;
- regret ContextValue = `regret(nuisance) - regret(full)`;
- shortlist ContextValue = `Good@K(full) - Good@K(nuisance)`.

The full model is compared with geometry nuisance, a parent-invariant residual model, matched-stratum context shuffle, matched-stratum contextual-delta shuffle, and interaction knockout. Shuffled controls may remain above random; they must lose the *incremental* benefit attributed to context.

Exact-SNV transfer is not declared collapsed. It remains unresolved because only 19 unique development SNV intervention pairs exist. A direct row-level audit corrects one nuance in the inherited wording: two reporter-specific trp53 shape sets each contain six exact-SNV candidates, but both concern the same Moffatt biological parent; the other SNV sets have at most three candidates and most are singletons. Thus there is no adequately replicated cross-parent SNV transfer test. Phase B2 reports the eligible trp53 result descriptively and gates only 2–5, 6–10 and combined 2–10-nt interventions.
