# RNAddress v4 Phase B2 final verdict

# NO-GO

Central answer: **No.** After removing cross-fitted edit geometry and assay-design nuisance, RNAddress does not predict parent-specific residual intervention effects with the distributed, source-robust, matched-context and small-edit consistency required for an unseen RNA-context compiler.

## Frozen gates

| Gate | Result | Decisive value |
|---|---|---|
| A — context beats geometry | FAIL | rank CV +0.0191 (<+0.020); regret CV +0.0011 (<+0.010) |
| B — context necessity | PASS | all three controls lose aggregate incremental value |
| C — distributed units | FAIL | median -0.0101; 44.60% improve; bootstrap low -0.0375 |
| D — Mikl matched context | FAIL | rank CV -0.0033 despite regret CV +0.0067 |
| E — leave-source-out | FAIL | 3/6 tasks; equal mean +0.0026 |
| F — cell/reporter transfer | FAIL | cell 1/4, reporter 2/4 |
| G — small-edit bridge | FAIL | 2–10 regret CV -0.0010 |
| H — direction | FAIL | neither increase nor decrease passes all domains |
| I — source robustness | FAIL | only Moffatt ≥+0.005; TDP -0.0286 |
| J — controls/integrity | PASS | protected data sealed; all B2 mechanism tests pass |

Final verification: **92/92 repository tests passed** in one run, including 21 dedicated Phase B2 tests. A Windows ViennaRNA native-library load-order collision was resolved in test bootstrap only; it did not affect model code or results.

## Interpretation

There is real but fragmented contextual signal. Full models beat the parent-invariant null and all three relationship-breaking controls in aggregate. Increase works within sources and across reporters; decrease works in leave-source-out and small-edit slices. These signals do not align in the same direction/model and are not distributed across biological units. Moffatt increase is heavily driven by one parent, and mandatory Mikl matched rank does not improve.

The permanent Phase B `NO-GO` is unchanged. Phase B2 is a new `NO-GO`; it does not authorize DFL, Astrocyte access, Phase C preregistration, predictions or a UI. A future credible path would require new, independently parented, matched small-edit localization datasets and prospective external validation. The present public development evidence does not support a PV-CARE-level universal compiler.
