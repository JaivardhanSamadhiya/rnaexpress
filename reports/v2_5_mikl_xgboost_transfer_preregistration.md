# RNAddress v2.5 published Mikl-XGBoost transfer preregistration

Frozen on 2026-08-27 after the two external classifiers and their hashes were frozen, and before reading any N-zip outcome for v2.5, fitting its N-zip calibration or computing a v2.5 metric. TDP-43 locked outcomes and astrocyte outcomes remain sealed.

## Rationale and applicability

V2.4 failed after combining weak external regressors with a 64-component compression of the contextual matrix. V2.5 instead reconstructs the primary Mikl paper's task-specific nonlinear 4-mer classifiers. The frozen external models achieve gene-held-out auROC 0.774603 for neurite enrichment and 0.732797 for soma enrichment across 304 decontaminated genes.

An outcome-blind application check was permitted before this freeze. After adapting each N-zip sequence to 150-nt-equivalent 4-mer counts, the frozen classifiers produced a nonzero combined mutant-minus-parent response for 4,367/4,395 SNVs, 202-300 distinct combined values per parent and nonzero within-parent standard deviation for all 15 parents. No N-zip localization measurement was used in that check.

## Frozen N-zip representation

For each unique N-zip parent and mutant:

1. compute all 256 lexicographically ordered 4-mer counts;
2. multiply by `147 / (sequence_length - 3)` so the feature sum equals the 147 4-mer positions in every 150-nt Mikl training insert;
3. apply the hash-locked neurite classifier (`b7df2c9dd92110afd0a12cb0422c2b4d94bd9d2c5a1cac6920863304aa7f13558`) and soma classifier (`9fc23ef557bf9913e694af37c41a37f2394d9b1f52d13f34acaed08fff069ed2a`);
4. subtract parent probability from mutant probability separately for the neurite and soma heads.

The N-zip model receives exactly 20 features in this order: the unchanged 18 metadata features (16 substitution indicators, relative edit position, parent length/100), neurite probability delta and soma probability delta. The combined published score delta, `delta_neurite - delta_soma`, is retained only as a prespecified zero-shot descriptive comparator; it is not used as an additional collinear feature.

## Frozen outer model

- Strict leave-one-parent-out evaluation over all 15 N-zip parents.
- Within every training parent, convert measured localization delta to average percentile rank from 0 to 1.
- Fit `StandardScaler` on the 20 training features only.
- Fit deterministic ridge regression with intercept, alpha 20, `lsqr`, tolerance `1e-6` and at most 10,000 iterations.
- Predict the held-out parent without recalibration or head selection.

There is one candidate only. No classifier head, 4-mer, interaction, component, tree threshold, alpha or feature weight may be selected using N-zip performance.

## Unchanged gate and controls

The calibrated candidate must achieve macro rank percentile at least 0.630, gain at least 0.030 over the strongest existing forward model, gain at least 0.020 over metadata-only, improve at least 9/15 parents versus the strongest forward model, retain positive mean gain after removing its two best parent gains, and keep its within-parent shuffled-edit score at most 0.540 using seed `20260826`.

Only if all six checks pass, repeat the complete calibration after permuting labels within parent with seed `20260826`; that score must be at most 0.530. A complete pass authorizes freezing TDP-43 lock predictions. Any failure rejects v2.5 and leaves both outcome locks sealed. This is an adaptive eighth development-stage rescue and must remain visible in reporting.
