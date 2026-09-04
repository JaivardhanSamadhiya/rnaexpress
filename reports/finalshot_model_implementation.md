# FinalShot model implementation lock

Status: implementation semantics fixed before any complete M1/M2 aggregate,
M3 prediction, transfer result, control result, or FinalShot gate decision.
This note resolves numerical details inside the already frozen families; it does
not add or alter a feature, model, fold, hyperparameter, metric, or threshold.

## M1/M2 sparse-group objective

For training rows with hierarchical weights normalized to mean one, the solver
minimizes

`0.5 * sum_i(w_i * (y_i - b0 - x_i'b)^2) / sum_i(w_i)`

`+ 0.5 * 1e-5 * ||b||_2^2`

`+ lambda * [(1-eta) * ||b_RBP||_1 + eta * sum_g sqrt(p_g)||b_g||_2]`.

`eta` is the group fraction, matching the protocol wording. Geometry receives
only the `1e-5` ridge floor. Each RBP's nine base summaries and, for M2's 98
eligible channels, its nine same-RBP expression interactions form one group;
there are always 103 RBP groups. The `sqrt(p_g)` factor gives the conventional
group-size normalization. The intercept is unpenalized.

Standardization uses unweighted training-row mean and population standard
deviation (`ddof=0`); zero-variance columns receive scale one. Weighted
centering then profiles out the intercept exactly. FISTA starts from all-zero
coefficients, uses a deterministic 24-step power estimate with a 1.05 safety
factor and deterministic majorization backtracking, a monotone restart if an
accelerated step increases the objective, at most 500 updates, and the frozen
relative objective tolerance `1e-6`. A candidate must converge in every inner
fold and in the outer refit.

M2 column storage is group-contiguous rather than block-contiguous: geometry,
then each RBP's nine base summaries followed immediately by its nine allowed
interactions. This is a pure column permutation of the frozen representation
and makes the proximal group boundary explicit.

## M3 latent normalization and heads

M3 uses the same M2 matrix and sparse-group penalty. Its five head labels are
exactly Mikl-CAD, Mikl-N2A, TDP-CAD, Moffatt-GFP-CAD, and
Moffatt-Firefly-CAD. The affine head is `a_h + softplus(s_h) * phi`. The
two-knot head adds two positive hinge slopes at the 1/3 and 2/3 training-score
quantiles. Heads never receive sequence, edit geometry, parent, source identity
features, or outcomes from a held context.

During minibatch optimization, latent values are centered and unit-scaled in
the frozen 2,048-row optimization batch. The sparse and ridge penalties are
applied to the correspondingly scale-normalized latent coefficient, preventing
the coefficient/head rescaling degeneracy. The archived predictor is recentered
and unit-scaled exactly on all training rows. Final two-knot locations are the
1/3 and 2/3 quantiles of that archived training latent score.

Each M3 fit uses Adam at `1e-3`, deterministic seed-specific shuffling, gradient
norm 5, at most 100 epochs, and training-objective patience 10. An improvement
must exceed `1e-8` to reset patience. The three frozen seeds 17, 41, and 89 are
fit and averaged; none is selected.

## Computational and integrity behavior

The 927-feature RBP matrix remains memory mapped. A job materializes only one
outer training block and its held block. Each family/fold result is written by
atomic replacement only after all inner fits, the frozen recipe selection, and
the converged outer refit succeed. Existing artifacts are validated against the
frozen row and RBP-matrix hashes before being skipped.

The first real M1 and M2 smoke fits used outer fold 0 training rows only and
were not retained as evaluation outputs. At `lambda=0.01, eta=0.75`, M1
converged in 152 updates and M2 in 203 updates. This established feasibility on
the available 16 GB CPU-only host. No N-zip outcome or Astrocyte path is used by
the implementation.
