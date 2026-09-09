# RNAddress FinalShot: can RBP-informed models choose transferable RNA-localization edits?

Submission preparation snapshot: 9 September 2026. Target deadline: 13 September
2026. The last cell-context control fold is still running; the computational
release is not yet complete. See `results/finalshot/submission_status.json`.

## Research question

RNA localization concerns where RNA accumulates inside a cell. RNAddress asks
whether a model can choose a sequence edit that increases or decreases that
localization on a biological parent it has not seen during training. The key
gap is between predicting a sequence's properties and reliably choosing an
intervention that transfers across genes, experiments, cell contexts, and small
edit sizes. FinalShot tests whether predicted changes in RNA-binding-protein
(RBP) interactions help close that gap beyond simple edit geometry.

## Study design

The certified development benchmark contains 93,208 assay rows, 62,665 unique
interventions, 445 decision sets, and 213 biological units from Mikl, TDP, and
Moffatt studies. Whole genes or parents stay together in five outer folds;
model selection uses inner biological folds. Both increase and decrease are
evaluated. Performance is averaged by biological unit, source, and direction,
so a large mutant library does not count as thousands of independent parents.

The exact Parnet preprint checkpoint failed the resource audit. The explicitly
permitted fallback uses 103 frozen human HepG2 RBPNet checkpoints, producing
nine parent/change summaries per checkpoint. This is a cross-species mouse
application with incomplete RBP coverage, including no TARDBP checkpoint.

M0 is a weighted Ridge geometry baseline. M1 adds RBP summaries; M2 adds
outcome-independent expression interactions; M3 separates a shared latent score
from monotone assay-specific measurement heads. A fixed 3UTRBERT comparison
provides a generic sequence-representation reference. No new encoder, feature
family, or gate was selected after results.

## Main findings

The nested-selected predictor improves equal-source rank percentile by
0.04229 and reduces normalized regret by 0.04009 relative to geometry. The
paired biological-unit bootstrap interval for regret gain is approximately
[0.00679, 0.07386]. Leave-source-out averages are also favorable.

However, only 54.46% of biological units improve, below the required 55%.
Cell and reporter transfer requirements fail. In the combined 2–10 nt regime,
rank and regret gains are negative; 6–10 nt edits exceed the allowed harm
threshold. Most importantly, RBP-identity scrambling retains 107.97% of rank
gain and 78.84% of regret gain. The delta-block reassignment control also retains
the gain. Thus average predictive improvements do not demonstrate that the
intended RBP-specific mechanism is necessary.

Trans-context and measurement-process retention gates fail. Neither requested
direction satisfies all reported directional conditions. Favorable descriptive
subgroups, including the exact-geometry TDP increase comparison, are not
independently validated discoveries and do not rescue the original claim.

## Integrity and interpretation

An audit found a written Mikl matching cap that was omitted in the implementation
and is inconsistent with the written within-gene minimum subset size. The earlier
numerical matched-gate pass is therefore qualified. Selection tie-order wording,
delta donor cycling, head-control aggregation, and cross-run floating-point
reproduction also require explicit disclosure. None was silently repaired by
changing the frozen experiment after results.

All 103 checkpoint and profile/feature cache hashes, sequence mappings, profile
invariants, and assembled feature blocks passed re-verification. All 36 scoped
software tests passed. These checks support technical auditability; they do not
erase scientific protocol limitations.

The evidence supports **NO-GO for this universal zero-shot RNAddress path**,
not a conclusion that RNA localization cannot be engineered. The potential
contribution is a transparent, decision-focused transfer benchmark and a
negative-mechanism finding: apparently useful pretrained representations can
retain performance when their intended mechanistic information is disrupted.
That contribution should be judged on its actual evidence, not relabeled as a
validated intervention compiler. Novelty of the exact benchmark combination is
qualified, not a proven first.

## Submission map and remaining work

The complete 60-item return is drafted in `finalshot_final_verdict.md`; the
literature comparison is in `finalshot_novelty_audit.md`; limitations are in
`finalshot_integrity_review.md`. Predictions, metrics, confidence intervals,
control results, and provenance are under `results/finalshot/`.

After the final cell-context fold finishes:

1. Run `python -m src.analysis.summarize_finalshot_cell_control`; it rejects
   missing folds and validates row hashes/indices and nested seed metadata.
2. Inspect the new control summary and compare archived prediction/seed means;
   do not alter models or selection rules.
3. Rerun scoped FinalShot tests, recording
   `results/finalshot/submission_tests.xml`.
4. Run `python -m src.analysis.build_finalshot_submission`, review all 60 items,
   and verify the final release's artifact inventory/hashes.
5. Update this overview's completion status, commit the final control and
   reports, deliver the verdict, and end the scheduled follow-up.

No N-zip outcome or Astrocyte data is accessed. Phase C is not justified.
RNAddress-Adapt would be a separate few-shot hypothesis, not an additional
zero-shot rescue phase or a result of this experiment.
