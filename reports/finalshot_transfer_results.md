# RNAddress FinalShot frozen transfer results

## Scope and integrity

The seven prespecified transfers are complete for M0 geometry, matched R1
3UTRBERT Ridge, direct M1/M2, and latent M3. Every scaler, model, penalty,
latent function, and available assay head was fit using only the training
partition. Target-test outcomes were not used for fitting or selection. N-zip
outcomes were not accessed, and no Astrocyte data were accessed.

The transfer-specific nested selector chose M3 for both cell transfers, both
reporter transfers, and leave-Moffatt; it chose M2 for leave-Mikl and
leave-TDP. These choices were made from training-partition biological-fold
predictions before evaluating the corresponding target partition.

## Selected-model ContextValue by transfer

ContextValue is paired against M0 on identical test decisions. Rank is full
minus M0; regret is M0 minus full, so positive values are favorable.

| Transfer | Direction | Rank ContextValue | Regret ContextValue |
|---|---:|---:|---:|
| CAD to N2A | decrease | -0.01381 | -0.01657 |
| CAD to N2A | increase | -0.02701 | +0.00306 |
| N2A to CAD | decrease | +0.01886 | +0.00958 |
| N2A to CAD | increase | +0.00324 | -0.00124 |
| Firefly to GFP | decrease | +0.04760 | -0.00389 |
| Firefly to GFP | increase | -0.09719 | -0.12157 |
| GFP to Firefly | decrease | +0.03080 | +0.02852 |
| GFP to Firefly | increase | +0.03921 | +0.00932 |
| leave Mikl out | decrease | +0.06053 | +0.03629 |
| leave Mikl out | increase | +0.02972 | +0.02605 |
| leave TDP out | decrease | +0.04711 | +0.06220 |
| leave TDP out | increase | +0.02884 | +0.00788 |
| leave Moffatt out | decrease | +0.16941 | +0.11787 |
| leave Moffatt out | increase | +0.22816 | +0.16500 |

## Frozen gates

### Gate D — leave-source-out: PASS

All six source-by-direction tasks have positive regret ContextValue. Their
equal-task mean rank ContextValue is `+0.09396`, and mean regret ContextValue is
`+0.06921`, exceeding the frozen `+0.010` requirement. Moffatt contributes
68.11% of summed positive regret gain, below the 75% concentration ceiling.

This is strong evidence that the nested selector can recover contextual value
when transferring among the three assay sources. It does not rescue the full
compiler because other mandatory gates are conjunctive.

### Gate E — cell/reporter transfer: FAIL

Only one of four cell-direction tasks has both positive rank and regret
ContextValue; the cell-transfer means are rank `-0.00468` and regret
`-0.00129`. Only two of four reporter-direction tasks have both positive
metrics; reporter means are rank `+0.00511` and regret `-0.02191`.

The strongest failure is Firefly-to-GFP increase, with rank `-0.09719` and
regret `-0.12157`. The reciprocal GFP-to-Firefly transfer is positive in both
directions, demonstrating directionally asymmetric transfer rather than a
reporter-invariant rule.

### Gate J — measurement process: FAIL

Across leave-source-out tasks, raw M3 beats direct M2 by mean rank `+0.03314`
and mean regret `+0.02238`, satisfying the magnitude clause. However, M3
worsens regret by more than 0.020 on both leave-TDP direction tasks, exceeding
the allowed maximum of one. M3 is therefore dropped by the frozen rule.

The result is mechanistically informative: the measurement-layer model helps
strongly on leave-Moffatt but transfers poorly to TDP. It does not establish a
universal assay-independent latent phenotype.

### Gate K — transfer seed conclusion: stable

Seeds 17, 41, and 89 all reach the same categorical Gate J failure. Their mean
M3-over-M2 regret improvements are `+0.02170`, `+0.02885`, and `+0.02304`, but
each seed has two leave-source direction tasks worsening by more than 0.020.
This agrees with the previously reported primary-evaluation seed stability;
the deterministic M0-M2 smoke-reproduction requirement remains to be archived
with the final integrity suite.

## Interpretation

Gate D demonstrates real cross-source decision value after nested selection,
but Gate E rejects cell- and reporter-invariant transfer and Gate J rejects M3
as a generally transferable measurement-process correction. Together with the
already failed distributed-unit Gate B and small-edit Gate F, these results
make `FULL GO — ORIGINAL RNADDRESS SURVIVES` impossible. The remaining
mechanism-breaking controls determine whether any narrow effect satisfies the
strict `PARTIAL GO` rule or whether the final verdict is zero-shot NO-GO.

Machine-readable records are in `results/finalshot/transfer_summary.json`,
`transfer_context_values.csv`, `transfer_task_metrics.csv`,
`transfer_unit_metrics.csv`, and `transfer_set_metrics.csv.gz`.
