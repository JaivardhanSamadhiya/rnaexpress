# RNAddress v2 structure screen

The preregistered ViennaRNA structure/accessibility candidate was evaluated with strict 15-parent leave-one-parent-out predictions. The original N-zip lock remains failed; TDP-43 locked outcomes and Astrocyte outcomes remained sealed.

| Model | Rank percentile | Normalized regret | Spearman |
|---|---:|---:|---:|
| factorized context, sequence only | 0.662 | 0.400 | 0.104 |
| metadata only | 0.612 | 0.438 | 0.111 |
| forward LightGBM | 0.560 | 0.439 | 0.099 |
| factorized context + ViennaRNA | 0.539 | 0.505 | 0.111 |

Verdict: generic MFE, ensemble-diversity and unpaired-probability summaries hurt inverse selection and are dropped. This does not show that RNA structure is biologically irrelevant; it shows that these computational summaries do not add robust recommendation value in this benchmark.
