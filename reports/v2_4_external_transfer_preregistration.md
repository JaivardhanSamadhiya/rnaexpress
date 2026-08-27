# RNAddress v2.4 external-localization transfer preregistration

Frozen on 2026-08-27 after external-only model selection and before embedding any N-zip sequence for this candidate, fitting the N-zip model or computing a v2.4 N-zip metric. TDP-43 locked outcomes and astrocyte outcomes remain sealed.

## Rationale

The v2.2 full contextual ridge reached 0.616730 macro rank percentile but failed the absolute and metadata-gain criteria. V2.3's label-tail filtering reduced performance to 0.580995. The new candidate therefore changes the information source and variance control rather than retuning label thresholds: six localization-specific forward heads were learned entirely from external, globally decontaminated sequences and selected by held-out external genes. Their modest external macro Spearman values (Mikl 0.200311; Arora 0.140394) justify treating them as priors, not standalone predictions.

## Frozen features

1. Reuse the exact v2.2 4,395 x 2,638 outcome-independent contextual/edit matrix with SHA-256 `eeaca4d2c7362877755e850a8bc08fa3e3088c64ffd69fadff72ef409c165e74`.
2. Embed each unique N-zip parent and mutant sequence with the same official hash-locked `SpliceBERT.1024nt` checkpoint. Pool CLS and nucleotide mean exactly as in external pretraining and calculate the same 355 handcrafted absolute features.
3. Apply the frozen external scalers and heads from `data/frozen/v2_4_external_forward_heads.npz` (SHA-256 `a727474e6e5c613b499da7c58638cb797b9428cfa4a43256a6308fc7ee8074b2a`). For each intervention, subtract parent prediction from mutant prediction in this fixed order: Mikl CAD, Mikl Neuro-2a, Arora GFP/CAD, Arora firefly/CAD, Arora GFP/N2A and Arora firefly/N2A.
4. Add the unchanged 18-dimensional metadata vector: 16 reference-to-alternate indicators, relative edit position and parent length/100.

No external head is dropped, averaged or reweighted before N-zip fitting. The absolute-embedding cache is keyed by exact sequence and source-row hashes and is generated without reading any outcome.

## Frozen outer model

Use strict leave-one-parent-out evaluation over all 15 N-zip parents. In each outer fold:

- fit `StandardScaler` to the 2,638 reused v2.2 features from training parents only;
- fit randomized PCA with 64 components, `random_state=20260826` and `iterated_power=7` on those scaled training rows, then transform train and held-out rows;
- concatenate 64 PCA components, 18 metadata features and six frozen external-head deltas;
- fit a second `StandardScaler` on this 88-dimensional training matrix only;
- convert each training parent's measured localization delta to average percentile rank from 0 to 1;
- fit deterministic ridge regression with intercept, alpha 88, `lsqr`, tolerance `1e-6` and at most 10,000 iterations;
- predict the held-out parent without any parent-specific recalibration.

PCA is outcome-blind and fold-specific. The 64-component compression and alpha are fixed here; neither explained variance nor N-zip performance may alter them.

## Unchanged gate and controls

The candidate must satisfy every prior v2 gate criterion:

- macro rank percentile at least 0.630;
- gain at least 0.030 over the stronger existing forward model;
- gain at least 0.020 over metadata-only;
- improvement over the strongest forward model on at least 9/15 parents;
- positive mean gain after removing the candidate's two most favorable parent gains;
- within-parent shuffled-edit score at most 0.540 using seed `20260826`.

Only if all six primary checks pass, rerun the complete LOPO ridge stage after permuting labels within each parent with seed `20260826`; the shuffled-label score must be at most 0.530. A full pass authorizes prediction freezing for the TDP-43 lock. Any failure rejects v2.4 and leaves both outcome locks sealed. This is an adaptive seventh development-stage rescue and must remain visible in reporting.
