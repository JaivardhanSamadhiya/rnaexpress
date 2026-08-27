# RNAddress v2.4 external localization pretraining protocol

Frozen on 2026-08-27 before embedding any external construct or fitting any external outcome. This is an external-only representation/regularization selection stage, not the N-zip development gate. TDP-43 locked outcomes and astrocyte outcomes remain sealed.

## Cohorts and decontamination

- Mikl: use only the 13,309 natural `wt scanning 50` 150-nt inserts remaining after global exclusion of every normalized N-zip gene. The fixed 18-nt primers and 12-nt barcode are removed. The two heads are CAD and Neuro-2a neurite/soma log fold change.
- Arora: use the 7,115 260-nt biological inserts with complete outcomes in GFP/CAD, firefly/CAD, GFP/N2A and firefly/N2A. PCR handles, 14 labeled controls and 750 unlabeled random controls are excluded.
- The exact source hashes, table semantics and zero-overlap checks are frozen in `data/frozen/v2_4_external_forward_audit.json`.

## Targets

For every assay separately, convert outcomes to average percentile rank within source gene, then center by subtracting 0.5. This removes study-specific absolute offsets and gene-selection effects while preserving sequence-tile ordering. A gene with one construct receives target zero. No N-zip outcome is read.

## Frozen representations

Embed each biological insert once with the official, hash-locked `SpliceBERT.1024nt` checkpoint used in v2.2. The checkpoint stays in evaluation mode and is never fine-tuned. Pool the final hidden state into:

1. the 512-dimensional `[CLS]` vector;
2. the 512-dimensional mean over nucleotide tokens, excluding `[CLS]`, `[SEP]` and padding;
3. the existing 355-dimensional absolute handcrafted vector of normalized 1-4-mer frequencies, fixed localization/context motifs, length, GC and AG content.

Three prespecified candidate representations are evaluated: nucleotide mean; CLS plus nucleotide mean; and CLS plus nucleotide mean plus handcrafted features. The embedding cache is outcome-independent and keyed by exact cohort row order.

## External-only grouped selection

Evaluate ridge regression with intercept at alphas `1`, `10`, `100`, `1000` and `10000`. Standardization is fit inside every training fold. Mikl uses deterministic five-fold gene-grouped cross-validation; Arora uses leave-one-gene-out over its 14 genes. Multi-output ridge preserves every assay as a distinct head.

For each held-out gene and assay, calculate Spearman correlation over its constructs when both target and prediction vary. The score for a dataset is the unweighted mean across assay-specific gene-macro Spearman values. Select representation and alpha independently for Mikl and Arora by highest dataset score, breaking ties by simpler representation, then larger alpha. No N-zip metric, candidate ranking or locked outcome may influence selection.

After selection, refit each dataset's assay heads on its complete cohort and freeze coefficients, intercepts, scalers, selected hyperparameters, source-row hashes and cross-validation results before defining or fitting the v2.4 N-zip candidate.
