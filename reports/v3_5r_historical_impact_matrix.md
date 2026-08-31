# RNAddress v3.5R historical-impact matrix

## Interpretation rule

Historical artifacts are preserved exactly as originally produced. This audit does not retroactively rewrite the v1 lock failure, the v2/TDP gate failure, or the Phase 3 NO-GO. It adds the following required qualification:

> A post hoc source-data integrity audit discovered that historical N-zip processing treated unresolved source-workbook entries as measured zero outcomes. Raw reconstruction also failed the prospectively frozen publication-coverage and finite-value reproduction thresholds. The original analyses are preserved as historical results; a separately versioned partial reconstruction exists for provenance debugging but is not a validated replacement benchmark.

## Classification matrix

| Historical component | Classification | Reason | Required future action |
|---|---|---|---|
| N-zip sequence-design reconstruction | Unaffected | Sequence and edit identities do not depend on localization labels. | Retain, subject to the separate exact-sequence duplicate audit. |
| External literature audit | Unaffected | Publication and mechanism review did not use the contaminated numeric labels. | Retain. |
| Raw sequence feature extraction | Unaffected | Features are functions of sequence, not workbook outcomes. | Retain after row alignment to the corrected cohort. |
| Astrocyte quarantine and loader protections | Unaffected | Protected outcomes were not opened and were not used in N-zip reconstruction. | Retain sealed boundary. |
| Moffatt quarantine and archive protections | Unaffected | The archive remained opaque and was not used in N-zip reconstruction. | Retain sealed boundary. |
| v1 development and frozen N-zip lock | Label-exposed / requires corrected reanalysis | Training, selection, and evaluation used historical N-zip outcomes. | Preserve historical verdict; rerun only under a future corrected-analysis protocol. |
| v2 rescue screens and v2.6 development | Label-exposed / requires corrected reanalysis | N-zip supervision and model selection inherited unresolved labels. | Remain blocked until a validated truth layer can be recovered. |
| Representation benchmark | Label-exposed / requires corrected reanalysis | Representation comparisons used historical N-zip labels. | Rerun later. |
| Mechanistic ablations and magnitude models | Label-exposed / requires corrected reanalysis | Their target magnitudes and rankings came from the historical benchmark. | Rerun later. |
| Forward and metadata baselines | Label-exposed / requires corrected reanalysis | Baseline fitting, ranking, and selected recommendations used historical labels. | Rerun later. |
| Shuffled controls, seed stability, and uncertainty calibration | Label-exposed / requires corrected reanalysis | Controls and calibration were defined relative to contaminated N-zip labels. | Rerun later. |
| Phase 3 gate and frozen recommendations | Label-exposed / requires corrected reanalysis | Gate inputs and recommendation selection inherited historical N-zip supervision. | Preserve Phase 3 NO-GO and recommendations as historical; do not call them corrected. |
| TDP-43 outcome measurements | Training-data-exposed historical results | TDP outcomes are independent, but evaluated models were trained or selected using historical N-zip labels. | Do not call TDP truth invalid; rerun trained systems later if authorized. |
| Independent source-accession and checksum audits | Unrelated | These are provenance facts independent of N-zip outcome values. | Retain. |

## Boundaries

This phase performs no retraining, performance comparison, hyperparameter search, gate rerun, oracle-identifiability analysis, direction-asymmetry analysis, or recommendation generation. Those activities remain blocked because the final v3.5R verdict is NO-GO; committing the audit manifest does not itself authorize resumption.
