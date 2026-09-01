# RNAddress v4 Phase B final verdict

# NO-GO

RNAddress v4 has not demonstrated a sufficiently transferable rule for choosing useful RNA-localization interventions on unseen biological contexts and small-edit regimes. The selected contextual model is a hierarchical predict-then-rank Ridge model, but a metadata/edit-geometry Ridge is stronger on the primary aggregate regret metric and on every leave-source-out task.

## Frozen gates

| Gate | Result | Decisive evidence |
|---|---|---|
| A — within-source generalization | Fail | Beats metadata only on Moffatt; loses on Mikl and TDP |
| B — unit robustness | Fail | Median gain -0.0068; 46.95% units improve; bootstrap includes zero |
| C — leave-source-out | Fail | No task beats the generic comparator by the required margin |
| D — cell/reporter transfer | Pass | 3/4 cell tasks and 4/4 reporter tasks pass |
| E — small-edit bridge | Fail | 2–5 and 1–10 regret gains are 0.0104 and 0.0126, below 0.02 |
| F — direction | Decrease only | Decrease passes; increase fails |
| G — DFL value | Fail | No source passes the joint DFL improvement rule |
| H — robust DFL | N/A | Comparable uncertainty is unavailable |
| I — controls | Fail | Parent/context permutation remains above chance via edit geometry |
| J — seed stability | Pass | Deterministic selected head; all prespecified stochastic seeds retained |

## Why this is not a conditional GO

The unresolved conditions are central rather than peripheral: contextual value beyond metadata, distributed biological-unit improvement, unseen-source transfer, and the small-edit bridge all fail. Exact-SNV descriptive signal is also absent. A conditional GO would understate the number and importance of the failures.

## What remains scientifically valuable

- Phase A remains a strong, provenance-clean development foundation.
- Frozen 3UTRBERT representations outperform SpliceBERT in the outcome-blind matched benchmark.
- Reporter transfer is strong, three of four cell-context tasks pass, and disruption/decrease is more promising than enhancement/increase.
- The fully reproducible candidate, split, embedding, transfer, control, and gate pipeline is now available for a new preregistered cycle.

## PV-Care-level path

The current model is not PV-Care-level and does not justify a Phase C Astrocyte freeze. A credible research path remains only through a new cycle with substantially more paired 1–10-nt and exact-SNV interventions across the same parents, reporters, and cell contexts; counterfactual/matched edit designs that break edit-size/source confounding; and a newly frozen model family required to beat metadata under leave-source-out evaluation. Iterative active-learning/MPRA acquisition may be appropriate, but it must be evaluated in a new protocol and cannot retroactively change this verdict.

## Stop

Astrocyte remains untouched. No Astrocyte outcomes or localization/expression/translation labels were inspected, no final Astrocyte predictions or preregistration were generated, and no UI was built. Phase B stops here.
