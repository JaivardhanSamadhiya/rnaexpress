# RNAddress v4 Phase B2 transfer results

Definitive run date: 2026-09-01

Every transfer was trained without target outcomes. The target assay/source residual was disabled, and prediction used global geometry nuisance plus a shared context head.

| Transfer | Direction | Rank ContextValue | Regret ContextValue | Gate task ≥0.005 regret |
|---|---|---:|---:|---:|
| Leave Mikl out | decrease | +0.0220 | +0.0103 | pass |
| Leave Mikl out | increase | -0.0551 | -0.0162 | fail |
| Leave Moffatt out | decrease | +0.0221 | +0.0215 | pass |
| Leave Moffatt out | increase | -0.0472 | -0.0175 | fail |
| Leave TDP out | decrease | +0.0505 | +0.0203 | pass |
| Leave TDP out | increase | +0.0208 | -0.0029 | fail |
| CAD→Neuro-2a | decrease | -0.0208 | -0.0104 | fail |
| CAD→Neuro-2a | increase | +0.0032 | -0.0005 | fail |
| Neuro-2a→CAD | decrease | +0.0149 | +0.0014 | fail |
| Neuro-2a→CAD | increase | +0.0076 | +0.0206 | pass |
| Firefly→GFP | decrease | +0.0272 | -0.0008 | fail |
| Firefly→GFP | increase | +0.0586 | +0.0540 | pass |
| GFP→Firefly | decrease | -0.0291 | -0.0170 | fail |
| GFP→Firefly | increase | +0.0939 | +0.0213 | pass |

Gate E failed: only three of six leave-source-out direction tasks reached +0.005; the equal task mean was +0.0026 rather than +0.005. Two source means were positive and none was below -0.010, but those conditions were insufficient.

Gate F failed: only one of four cell-direction tasks passed, although two of four reporter-direction tasks passed. The pattern is asymmetric—decrease transfers across source identity, whereas increase transfers across reporter identity—but no direction satisfies the complete direction gate.
