# RNAddress v4 Phase B2 matched-context results

Definitive run date: 2026-09-01

Outcome-blind matching produced 688 cross-parent strata, of which 312 met the frozen ≥20-row/≥5-unit rule, and 9,500 within-parent strata, of which 1,943 met the ≥4-candidate rule. Matched controls could map 60,571 of 93,208 rows to a geometry-compatible donor from another biological unit in each direction.

## Mandatory Mikl crossed-context test

The eligible Mikl matched-operation slice contained 21,102 rows, 376 directional base decision sets per direction and 188 biological units.

| Direction | Rank ContextValue | Regret ContextValue |
|---|---:|---:|
| Increase | -0.0036 | +0.0136 |
| Decrease | -0.0029 | -0.0002 |
| Mean | **-0.0033** | **+0.0067** |

Gate D required rank ≥0.010 and regret ≥0.005. Regret passed but rank was negative, so Gate D failed. RNAddress did not demonstrate the required parent-aware improvement on Mikl's repeated motif operations.

## Source-held biological contexts

| Source | Direction | Rank ContextValue | Regret ContextValue |
|---|---|---:|---:|
| Mikl held gene | increase | -0.0049 | +0.0104 |
| Mikl held gene | decrease | -0.0208 | -0.0114 |
| TDP held gene | increase | +0.1314 | +0.0090 |
| TDP held gene | decrease | -0.0119 | -0.0661 |
| Moffatt held parent | increase | +0.0550 | +0.0691 |
| Moffatt held parent | decrease | -0.0343 | -0.0045 |

Moffatt's positive increase mean is concentrated: one of eight parents had regret ContextValue +0.9555, while six of eight had negative increase ContextValue. Across both directions, Moffatt mean regret ContextValue was +0.0323, but this concentration does not support a broad parent compiler. TDP decrease was the strongest source-level negative result at -0.0661 regret ContextValue.
