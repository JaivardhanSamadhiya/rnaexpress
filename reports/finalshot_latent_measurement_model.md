# FinalShot latent measurement model

## Frozen implementation

M3 uses the M2 trans-conditioned 1,837-column design, a shared sparse-group
linear latent score, and one low-capacity monotone measurement head for each of
Mikl-CAD, Mikl-N2A, TDP-CAD, Moffatt-GFP-CAD, and Moffatt-Firefly-CAD. The
head grid was limited prospectively to positive affine and positive two-knot
piecewise-linear forms. Penalty, group-fraction, head form, biological folds,
three seeds (17, 41, 89), optimizer, and stopping rules were frozen before M3
evaluation. Exact numerical semantics are in
`reports/finalshot_model_implementation.md`.

The full nested evaluation comprised 720 inner fits and 15 selected outer
refits. Each inner fit was checkpointed independently. No favorable seed was
selected: the three seed predictions were averaged in every recipe comparison
and outer evaluation.

## Selected recipes

| Outer fold | Lambda | Group fraction | Head form |
|---:|---:|---:|---|
| 0 | 0.1 | 0.75 | affine |
| 1 | 0.001 | 0.25 | affine |
| 2 | 0.001 | 0.25 | two-knot |
| 3 | 0.001 | 0.25 | two-knot |
| 4 | 0.001 | 0.75 | affine |

The more flexible two-knot measurement process was selected in only two of
five folds. This is not evidence for a universally nonlinear assay mapping.

## Held-biological-unit result

Against M0 geometry and equal-weighted over source × requested direction:

| Model | Rank ContextValue | Regret ContextValue | Positive rank tasks | Positive regret tasks | Gate A |
|---|---:|---:|---:|---:|---|
| M2 direct | +0.02024 | +0.03387 | 4/6 | 5/6 | pass |
| M3 latent/head average | +0.05517 | +0.02390 | 5/6 | 6/6 | pass |
| fully nested M1/M2/M3 selection | +0.04229 | +0.04009 | 6/6 | 6/6 | pass |

M3 improves rank more strongly than M2 but has a smaller regret gain. The
fully nested family selector chose M1 in outer folds 0, 3, and 4; M2 in fold 1;
and M3 in fold 2. Its held-fold gains are positive for all six source-direction
tasks. These are within-source held-gene/held-parent results, not the mandatory
leave-source-out test, so Gate J and the final verdict remain unresolved.

## Optimization stability

The three complete seed-specific M3 evaluations all pass Gate A. Their
equal-source ContextValue standard deviations are `0.00939` for rank and
`0.00440` for regret, both within the frozen `0.010` limit. This satisfies the
numerical-variation portion of Gate K for the biological-fold evaluation.
Categorical M3-versus-M2 agreement must still be evaluated in leave-source-out
transfer before Gate K can be decided.

No N-zip outcome or Astrocyte datum was accessed. M3 results do not unseal
Astrocyte and do not independently authorize a GO.
