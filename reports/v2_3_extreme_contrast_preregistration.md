# RNAddress v2.3 SpliceBERT extreme-contrast preregistration

Frozen on 2026-08-27 after the v2.2 contextual percentile-ridge candidate failed and before fitting the v2.3 candidate. TDP-43 locked outcomes and Astrocyte outcomes remain sealed.

## Rationale

V2.2 produced the strongest strict-LOPO global ordering correlation so far (Spearman 0.194) but only 0.617 top-choice rank percentile. It passed four of six primary criteria but failed the absolute threshold and metadata margin. This pattern supports a loss/objective mismatch rather than discarding the frozen contextual representation.

Learning-to-rank research distinguishes pointwise regression from ranking losses and notes that top-ranked decisions require greater emphasis on high-relevance examples or pairs. V2.3 therefore changes only the downstream training target to focus symmetrically on the two recommendation extremes.

## Frozen model

- Reuse without modification the cached v2.2 feature matrix with shape 4,395 × 2,638 and SHA-256 `eeaca4d2c7362877755e850a8bc08fa3e3088c64ffd69fadff72ef409c165e74`.
- Strict leave-one-parent-out evaluation over all 15 N-zip parents.
- In every training parent, order candidates by measured delta localization and then `source_row` for deterministic tie-breaking. Let `q = floor(n / 4)`.
- Assign the lowest `q` candidates target -1 and the highest `q` candidates target +1. Exclude all middle candidates from model fitting.
- Fit `StandardScaler` on all rows from the training parents only, preserving the v2.2 feature geometry independently of extreme labels.
- Fit deterministic `sklearn.linear_model.Ridge` on the extreme rows with intercept, `alpha = number of input features`, `solver='lsqr'`, tolerance `1e-6`, and at most 10,000 iterations.
- Rank every held-out candidate by the raw ridge score. The same score is reversed for decrease recommendations.
- No feature, quartile, tie, regularization, seed, model, or blend selection is allowed.
- Shuffled-edit control permutes the final candidate scores within each parent with seed `20260826`.
- Only if every primary criterion passes, repeat the downstream LOPO fit after permuting outcomes within parent with seed `20260826`; the frozen features are unchanged.

## Unchanged gate

Rank percentile must be at least 0.630; gain must be at least 0.030 over the strongest forward model and 0.020 over metadata; the candidate must improve on at least 9/15 parents and retain positive mean gain after removing its two best parents; shuffled edit must be at most 0.540; and the conditional shuffled-label model must be at most 0.530.

Only a complete pass authorizes freezing TDP-43 lock predictions, code, environment and hashes before opening its 1,006 outcomes. This sixth adaptive development-stage rescue must be disclosed in any final claim, regardless of result.
