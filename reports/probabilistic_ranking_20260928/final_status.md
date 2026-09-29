# Probabilistic ranking: final status

**NO-GO: no primary probabilistic supervision method passed the frozen decision gate.** The generalizable RNA-localization edit predictor goal remains unconfirmed by an untouched biological experiment. The old NO-GO remains intact.

The tested probabilistic targets did not remedy the universal-model failure sufficiently to pass the frozen gate. Hard labeling alone is therefore not a supported main explanation for that failure in this controlled experiment. This does not prove that label uncertainty has no role or rule out every possible uncertainty model.

Soft supervision reduced some probability errors relative to H0, but every primary model remained worse than a constant 0.5 prediction on held-out replicate Brier score and log loss. No primary model passed the probability-calibration claim gate. This distinction is documented in `calibration_reference.md` and does not change model selection.

## Main decision results

| model | regret | avoidable_wrong | wrong_direction |
| --- | --- | --- | --- |
| H0 | 0.48823 | 0.34542 | 0.48344 |
| P1 | 0.50306 | 0.33402 | 0.47203 |
| P2 | 0.50572 | 0.33435 | 0.47236 |
| P3 | 0.48942 | 0.33448 | 0.47249 |

Lowest macro regret among primary soft methods: `P3` (0.489424); this is a descriptive label, not a selected model unless it passes every gate condition. Selected method: **none**. Per-assay benefits and harms remain in `leave_one_assay_out_results.md` and the gate report.

## What is complete

Reconstructed 127,603 replicate records with explicit missingness; preserved the original candidate/pair/feature/split structure; ran matched H0/P1/P2/P3, held-parent checks, alternating cross-replicate tests, whole-study evaluation, and every fixed secondary control. Pairwise calibration, exact candidate ranking, measurement ambiguity, all wrong-direction categories, and matched raw-target reproducibility comparisons are delivered. Conditional policy status: **NOT_RUN_CALIBRATION_REQUIREMENTS_NOT_MET**. No absolute-benefit calibration claim is made.

The nine figure topics are covered by seven PNG/SVG figures and a contact sheet. All eight requested reports and seven CSV artifacts are included, together with exact fitted coefficients, scalers, source-noise parameters, per-fold training targets, rankings, probabilities, role-specific diagnostics and checksums.

## Verification

235,630 pair probabilities replayed from saved coefficients (maximum error 0); 108,720 selected decisions and 40 study/model macro regrets independently checked. Four fresh P1 fits reproduced coefficients (maximum error 0); nine scoped tests passed. Historical H0 scores and choices reproduced. All 26 prefit hashes, prior 319/28-member bundles, and 33 preexisting modified tracked files remain unchanged.

## Limits and stopping boundary

All studies are exposed development data. Biological breadth is unequal: one SRLE reporter, two astrocyte genes, six Moffatt parent/gene groups, and 187 Mikl genes. Variant counts do not supply independent biological experiments. The prior cross-assay NO-GO is unchanged. Moffatt has no admitted paired replicate deltas, so all main supervision methods fall back to its aggregate labels. Source raw-versus-processed estimator differences remain; Hraw provides an explicit control. Shared WT contrasts, correlated replicate labels, few independent systems and limited parent diversity constrain probability interpretation. Calibration against measured replicate support does not prove future biological calibration.

Stop this generation. Do not vary priors, smoothing constants, uncertainty formulas, windows or seeds to obtain a pass. No new representation combination or independent-dataset search was started. Remaining explanations include endpoint-specific biology, inadequate transferable sequence/context information, limited source diversity and systematic measurement/provenance differences. This experiment narrows the supervision hypothesis; it does not uniquely identify the biological cause or establish novelty.

No money, downloads, scheduled tasks, broad pytest, or protected outcomes were used. See `reproducibility.md` and the delivery receipt for artifact reconstruction and exact execution provenance.
