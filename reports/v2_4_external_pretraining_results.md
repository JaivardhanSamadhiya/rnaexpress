# RNAddress v2.4 external localization pretraining results

The frozen external-only protocol completed over 13,309 decontaminated Mikl natural tiles and 7,115 complete Arora inserts. N-zip outcomes, TDP-43 locked outcomes and astrocyte outcomes were not read during embedding, grouped selection or final external refitting.

## Selected heads

| Dataset | Assay heads | Selected representation | Ridge alpha | Held-out-gene macro Spearman |
|---|---:|---|---:|---:|
| Mikl | 2 | CLS + nucleotide mean + handcrafted absolute sequence | 10,000 | 0.200311 |
| Arora | 4 | CLS + nucleotide mean | 10,000 | 0.140394 |

Both datasets favored the strongest prespecified regularization. Mikl benefited from the handcrafted absolute features, whereas Arora did not: its handcrafted-augmented score at alpha 10,000 was 0.123783. The results support six low-variance assay-specific priors but do not support a standalone high-accuracy external localization model.

## Frozen artifacts

- `data/frozen/v2_4_external_forward_heads.npz` contains only the fitted scalers, coefficients and intercepts for the two Mikl and four Arora heads.
- `data/frozen/v2_4_external_forward_heads.json` records selected representations, alphas, cohort sizes, source-row fingerprints and SHA-256 values for both outcome-independent embedding caches, the complete grouped-CV table and the model artifact.
- `results/v2_4_external/external_grouped_cv.csv` preserves all 30 prespecified representation/alpha results, including unsuccessful settings.

The next N-zip candidate may consume all six external mutant-minus-parent predictions as features, but it may not reopen external model selection or choose heads using N-zip performance.
