# RNAddress locked internal results

Frozen prediction hash verified before reveal: `3b1fb0d494052fa6001615c3cbc257ff627e3464454457c846ab6cb153d37ad8`.

## Macro results over three locked parents

| Method | Rank percentile | Normalized regret | Spearman | Success@1 | Success@3 | Success@5 |
|---|---:|---:|---:|---:|---:|---:|
| pairwise_rank | 0.566 | 0.480 | 0.049 | 0.500 | 0.500 | 0.500 |
| retrieval | 0.279 | 0.573 | -0.012 | 0.500 | 0.500 | 0.500 |
| forward_extratrees | 0.624 | 0.421 | 0.094 | 0.500 | 0.500 | 0.500 |
| nzip_mikl_joint | 0.578 | 0.456 | 0.097 | 0.500 | 0.500 | 0.500 |
| random_exact | 0.500 | 0.500 | 0.000 | 0.464 | 0.501 | 0.503 |

## Gate decision

**FAIL**.

Pairwise rank percentile is 0.566, compared with 0.279 for retrieval, 0.624 for strong forward search and 0.500 for exact random. Normalized regret is 0.480 versus 0.500 for random.

## Parent-level locked recommendations

| Parent | Direction | RNAddress edit | Measured rank percentile | Forward edit | Forward rank percentile |
|---|---|---|---:|---|---:|
| ENSMUSG00000006699\|Cdc42_2\|31 | increase | C1T | 0.749 | T53A | 0.137 |
| ENSMUSG00000006699\|Cdc42_2\|31 | decrease | C48G | 0.993 | C59G | 0.769 |
| ENSMUSG00000014294\|Ndufa2\|11+12 | increase | C1T | 0.364 | G82C | 0.957 |
| ENSMUSG00000014294\|Ndufa2\|11+12 | decrease | C84G | 0.636 | T44A | 0.636 |
| ENSMUSG00000026031\|Cflar_1\|14 | increase | A5T | 0.304 | T35A | 0.916 |
| ENSMUSG00000026031\|Cflar_1\|14 | decrease | A46C | 0.348 | C82A | 0.331 |

## Parent-bootstrap uncertainty

| Comparison (RNAddress minus baseline) | Rank-percentile difference | 95% CI |
|---|---:|---:|
| random_exact | 0.066 | [-0.174, 0.371] |
| retrieval | 0.287 | [-0.050, 0.681] |
| forward_extratrees | -0.059 | [-0.298, 0.418] |

Only three parent units are available, so confidence intervals are necessarily wide and cannot establish population-level certainty. The external outcome reveal is not authorized by the preregistered gate.

The model was not modified after reveal. Astrocyte outcomes remain sealed.
