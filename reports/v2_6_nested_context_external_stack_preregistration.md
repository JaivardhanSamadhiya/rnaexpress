# RNAddress v2.6 nested contextual/external stack preregistration

Frozen on 2026-08-27 after v2.5 failed and before fitting or computing any v2.6 prediction. TDP-43 locked outcomes and astrocyte outcomes remain sealed.

## Rationale

The frozen v2.2 contextual ridge and v2.5 published Mikl-XGBoost calibration capture different information and reached 0.616730 and 0.620807 macro rank percentile respectively. V2.4 showed that unsupervised high-dimensional compression destroys useful ranking signal. V2.6 therefore keeps the full contextual ridge as a single supervised base score and combines it with the low-dimensional v2.5 representation through strict nested cross-fitting. Neither base representation nor any base hyperparameter is changed.

## Frozen base components

- Contextual base: the exact 4,395 x 2,638 v2.2 matrix with SHA-256 `eeaca4d2c7362877755e850a8bc08fa3e3088c64ffd69fadff72ef409c165e74`; training-parent `StandardScaler`; ridge alpha 2,638; parent-percentile targets; `lsqr`, tolerance `1e-6`, at most 10,000 iterations.
- External/edit base features: the unchanged 18 metadata features followed by the two frozen Mikl-XGBoost mutant-minus-parent probability deltas from v2.5.

## Strict nested procedure

For each of the 15 outer held-out parents:

1. Within the 14 outer-training parents, generate a contextual base score for every training row by an inner leave-one-parent-out loop. Every inner prediction is produced by a contextual ridge that excludes both its inner parent and the outer test parent.
2. Fit one contextual ridge on all 14 outer-training parents and predict the outer test parent.
3. Form exactly 21 meta-features: 18 metadata values, two frozen Mikl probability deltas and the one cross-fitted contextual score.
4. Fit `StandardScaler` on the outer-training meta-features only.
5. Fit ridge regression with intercept and alpha 21 to the same parent-percentile targets, using `lsqr`, tolerance `1e-6` and at most 10,000 iterations.
6. Predict the outer held-out parent once.

No in-sample contextual prediction may train the meta-model. There is no feature, component, head, alpha, seed, model or weight selection. The only candidate is `nested_context_external_stack`.

## Unchanged gate and controls

The candidate must achieve macro rank percentile at least 0.630, gain at least 0.030 over the strongest existing forward model, gain at least 0.020 over metadata-only, improve at least 9/15 parents versus the strongest forward model, retain positive mean gain after removing its two best parent gains, and keep the within-parent shuffled-edit score at most 0.540 using seed `20260826`.

Only if all six primary checks pass, rerun the complete nested procedure after permuting outcomes within parent with seed `20260826`; the shuffled-label score must be at most 0.530. A complete pass authorizes freezing TDP-43 lock predictions. Any failure rejects v2.6 and leaves both outcome locks sealed. This is an adaptive ninth development-stage rescue and must remain visible in reporting.
