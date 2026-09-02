# RNAddress v4 Phase B2 context model

Definitive run date: 2026-09-01

## Frozen representation and heads

The encoder remained frozen 3UTRBERT revision `220d80829deb077d1d640463a4267a96e9e70b1d`; no fine-tuning or encoder search occurred. Parent and contextual-delta 128-vectors were projected with seed 42017. M1 used 32 parent + 32 delta + four numeric geometry dimensions. M2 added low-rank elementwise parent×delta features. M3 added outcome-blind matched contrast rows. M4 applied one conditional source-balanced refit.

All residual heads were selected by inner biological holdout only. Outer winners were heterogeneous:

| Direction | M1 | M2 | M3 | M4 |
|---|---:|---:|---:|---:|
| Increase | 2 | 1 | 1 | 1 |
| Decrease | 1 | 2 | 0 | 2 |

M4 was eligible in three increase and four decrease folds and won one and two folds, respectively. Its mean eligible inner ContextValue was +0.0473 rank/+0.0359 regret for increase and +0.0307/+0.0273 for decrease. It was not stable enough to define one global architecture.

For target-free transfer, only configurations evaluated in all five outer-training cohorts were eligible. The frozen 0.002/simplicity rule selected:

- increase: M3 matched-contrastive, rank 16, alpha 1000;
- decrease: M1 residual contextual Ridge, alpha 1000.

The decrease consensus therefore contains parent and delta main effects but no explicit bilinear term; it cannot by itself establish parent×edit interaction. This is one reason positive decrease leave-source-out values do not authorize a disruption compiler.

## Nulls and relationship controls

Equal source/direction gains of full over each comparator were:

| Comparator | Rank gain | Regret gain |
|---|---:|---:|
| Parent-invariant residual null | +0.0378 | +0.0134 |
| Context shuffle | +0.0246 | +0.0082 |
| Contextual-delta shuffle | +0.0024 | +0.0169 |
| Interaction knockout | +0.0082 | +0.0138 |

These controls pass Gate B at the aggregate level and show that authentic relationships contain some incremental signal. They do not establish distributed transfer: the unit median, source robustness, matched Mikl, cell transfer and small-edit gates all fail.
