# RNAddress v4 Phase B ablation and control results

## Representation/shortcut ablations

Equal-source/direction means:

| Feature/model | Rank | Regret | Good@1 | Good@3 | Good@5 |
|---|---:|---:|---:|---:|---:|
| Parent only | 0.5308 | 0.4672 | 0.1095 | 0.1760 | 0.2681 |
| Mutant only | 0.4876 | 0.5124 | 0.0653 | 0.1173 | 0.2337 |
| Delta only | 0.5471 | 0.4862 | 0.0587 | 0.1745 | 0.2279 |
| Parent + contextual delta, global | 0.5840 | 0.4354 | 0.0893 | 0.2192 | 0.2747 |
| Edit geometry only | 0.5491 | 0.4722 | 0.0678 | 0.1636 | 0.2030 |
| Metadata/geometry | **0.5960** | **0.4218** | 0.1043 | 0.1966 | 0.2727 |
| Nearest neighbor | 0.5481 | 0.4571 | 0.0646 | 0.2270 | 0.3206 |
| Absolute forward difference | 0.5075 | 0.5047 | 0.0719 | 0.1319 | 0.1913 |

Parent plus delta beats parent-only, mutant-only, and delta-only on regret, so explicit context and intervention information help relative to those weak ablations. However, metadata/geometry is stronger than the contextual model on the primary aggregate regret criterion. This is a magnitude/class shortcut concern.

## Source-residual ablation

| Head | Rank | Regret | Good@3 | Good@5 |
|---|---:|---:|---:|---:|
| Global only | 0.5840 | 0.4354 | 0.2192 | 0.2747 |
| Global + assay residual | 0.5908 | 0.4265 | 0.2091 | 0.2951 |

Residual heads improve rank by 0.0069, regret by 0.0089, and Good@5 by 0.0204, while reducing Good@3 by 0.0101. They are never used for unseen-source transfer.

## Mandatory controls

| Control | Rank | Regret | Exact-random regret | Within ±0.02 |
|---|---:|---:|---:|---|
| Outcome permutation within source | 0.4893 | 0.5026 | 0.5000 | Yes |
| Intervention permutation within set | 0.5065 | 0.5049 | 0.5000 | Yes |
| Parent/context embedding permutation | 0.5978 | 0.4288 | 0.5000 | **No** |
| Source-only exact expectation | 0.5000 | 0.5000 | 0.5000 | Yes |

The failed parent/context control was diagnosed. It shuffles both the 128-dimensional parent block and the 128-dimensional contextual-delta block within source; edit geometry remains attached to each intervention by design. Its residual performance is consistent with the strong metadata/geometry baseline. This is not label leakage—the outcome and intervention permutations return to chance—but it shows the model can largely exploit edit class/magnitude without correct parent context. Frozen Gate I fails.

## Seed stability

The selected Ridge model is deterministic, so its prespecified-seed result is identical across seeds. DFL and pairwise stochastic components used seeds 17, 41, and 89; no seed was selected post hoc. Gate J passes, but seed stability cannot rescue the failed scientific transfer gates.
