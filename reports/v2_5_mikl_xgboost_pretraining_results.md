# RNAddress v2.5 Mikl published-model pretraining results

The external-only reconstruction completed on 35,428 globally decontaminated Mikl sequences grouped across 304 source genes. N-zip outcomes, TDP-43 locked outcomes and astrocyte outcomes were not read.

## Selected external classifiers

| Setting | Value |
|---|---:|
| Maximum depth | 3 |
| Minimum child weight | 1 |
| Learning rate | 0.03 |
| Trees | 500 |
| Gene-held-out neurite auROC | 0.774603 |
| Gene-held-out soma auROC | 0.732797 |
| Unweighted mean auROC | 0.753700 |

All eight prespecified settings achieved mean auROC between 0.692744 and 0.753700. The selected shallow, low-rate setting outperformed every depth-6 setting and both depth-3 high-rate settings. This supports reproducible nonlinear 4-mer localization signal across unseen genes while remaining below the paper's less stringent randomly held-out reporter auROC of 0.83.

## Frozen artifacts

- `data/frozen/v2_5_mikl_neurite_xgboost.json`: neurite classifier, SHA-256 `b7df2c9dd92110afd0a12cb0422c2b4d94bd9d2c5a1cac6920863304aa7f13558`.
- `data/frozen/v2_5_mikl_soma_xgboost.json`: soma classifier, SHA-256 `9fc23ef557bf9913e694af37c41a37f2394d9b1f52d13f34acaed08fff069ed2a`.
- `data/frozen/v2_5_mikl_xgboost_heads.json`: source fingerprint, exact 4-mer order, class counts, selected setting, runtime version and artifact hashes.
- `results/v2_5_external/mikl_xgboost_grouped_cv.csv`: complete eight-setting grouped-CV table, including all rejected settings.

These results establish an external localization prior. They do not establish N-zip SNV ranking; the booster outputs must be frozen before a separately preregistered mutant-minus-parent gate.
