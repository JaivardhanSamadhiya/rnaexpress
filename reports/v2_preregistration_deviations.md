# RNAddress v2 preregistration deviations

## 2026-08-26 — first-pass fixed-center screening

Recorded before fitting a v2 model or generating any v2 outer-fold prediction.

The first development pass uses the prespecified grid-center configurations for `factorized_context_ranker`, `context_lambdamart`, and `forward_lightgbm` rather than running the full nested grid. This is a compute-screening pass: bilinear rank 8, hidden width 32, learning rate `1e-3`, L2 `1e-3`; LambdaMART/forward LightGBM use 15 leaves, 30 minimum child samples, learning rate 0.03 and 300 trees.

No fixed value was chosen from v2 performance. All predictions remain strict outer leave-one-parent-out. If no custom candidate approaches the frozen gate, the expensive nested grid is scientifically uninformative and will not be used to search for a lucky configuration. If a candidate approaches or passes the gate, the full inner-parent selection required by the preregistration will be run and only those nested predictions can authorize the TDP-43 lock.

## 2026-08-26 — grouped inner-fold compute specification

Recorded after the fixed-center screen triggered the preregistered nested follow-up and before any nested prediction was generated.

The full 36-configuration factorized-ranker grid is retained. For each outer parent, the other 14 parents are assigned outcome-blindly to three inner folds by SHA-256 ordering and round-robin allocation. Inner screening uses 50 epochs and 300 sampled pairs per training parent; the selected configuration is refit for the frozen 200 epochs and 600 pairs per parent before predicting the outer parent. This is a training-budget surrogate, analogous to early stopping, and reduces the projected nested run from several hours to approximately one hour. Every outer prediction remains untouched by its outer parent's outcomes.

## 2026-08-27 — prespecified structure candidate implementation

Recorded after the sequence-only nested candidate failed and before fitting the preregistered structure-aware candidate. No locked outcome has been accessed.

ViennaRNA 2.7.2 computes, per parent and mutant: MFE per nucleotide, ensemble free energy per nucleotide, ensemble diversity per nucleotide and mean unpaired probability. Edit features add parent/mutant/delta mean unpaired probability at changed bases and within a radius-10 window, plus deltas of the global structure summaries. The fixed-center screening architecture is unchanged (rank 8, hidden width 32, learning rate `1e-3`, L2 `1e-3`, 200 epochs, 600 pairs per parent). Structure calculations are cached by exact sequence SHA-256 and never use outcomes.

## 2026-08-27 — TDP-43 development-only auxiliary candidate

Recorded after the structure candidate failed and before auxiliary model fitting. The four TDP-43 locked-gene outcomes remain unopened.

The auxiliary model has shared parent and edit encoders and separate additive edit heads for N-zip and TDP-43. TDP-43 ranking groups are genes, because each 260-nt oligo has one motif-complement intervention; N-zip groups remain parent sequences. Training uses equal aggregate pairwise loss from N-zip and TDP-43 development per epoch, with 600 high-versus-low pairs sampled per group, rank 8, hidden width 32, learning rate `1e-3`, L2 `1e-3`, and 200 epochs. Feature scaling is fitted to each outer fold's N-zip training parents plus the fixed 12-gene TDP-43 development set. No gene identifier is a feature.

## V2.1 checkpoint column-name correction

After all 105 frozen real-label seed fits had completed and been checkpointed, the evaluator stopped before computing any metric because one shuffled-edit line still referenced the pre-rename ensemble column `pred_factorized_context_ensemble`. It was corrected to `pred_factorized_context_seed_ensemble`. No model was retrained, no prediction changed, no gate metric had been computed, and both outcome locks remained sealed. The evaluator then resumed from the complete source-row-validated checkpoint.

## 2026-08-27 — v2.2 deterministic solver implementation

Recorded after the v2.2 method was frozen and before embedding any project sequence or fitting the model. The deterministic ridge implementation uses scikit-learn's `lsqr` solver with tolerance `1e-6` and at most 10,000 iterations. SpliceBERT inference batches 32 sequences at a time. These are compute/solver specifications; the representation, regularization rule, labels, folds and gate are unchanged.

## 2026-08-27 — v2.3 copied feature-hash correction

The first v2.3 invocation stopped at its pre-fit integrity check because the v2.2 feature hash had been transcribed with an extra `1` in the v2.3 report and code (`...409c1165e74` rather than the immutable gate/cache value `...409c165e74`). The actual feature file matched the committed v2.2 gate, retained its original creation/modification timestamps, and matched the frozen source rows. The copied hash was corrected before any v2.3 model fit or metric computation; both outcome locks remained sealed.

## 2026-08-27 — v2.4 descriptive v2.2-column merge

The first v2.4 invocation completed all 15 frozen candidate folds but stopped before metric computation because the v2 base source table did not contain `pred_splicebert_contextual_delta_ridge`, a prior prediction column requested only for descriptive comparison in the v2.4 metric table. No v2.4 aggregate or parent metric was computed, printed or saved. The implementation now merges that already-frozen v2.2 column from `results/v2_2/nzip_splicebert_predictions.csv.gz` by unique `source_row` with a complete one-to-one guard. The v2.4 representation, folds, targets, candidate predictions, gate baselines, checks and thresholds are unchanged. Both outcome locks remained sealed.
