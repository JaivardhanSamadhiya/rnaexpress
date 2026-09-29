# Interpreting improved probability scores

This is a postfit analytic reference, not a new fitted comparator, gate or selection rule. A constant pair probability of 0.5 has expected per-replicate Brier score 0.25 and log loss log(2)=0.693147, for every target fraction. With both orientations equally weighted it also has marginal ECE zero and sharpness zero. It supplies no candidate-ranking information.

| model | dataset | brier | log_loss | brier_gain_vs_constant_half | logloss_gain_vs_constant_half |
| --- | --- | --- | --- | --- | --- |
| H0 | astrocyte_gse330741 | 0.25429 | 0.70194 | -0.00429 | -0.00879 |
| P1 | astrocyte_gse330741 | 0.25314 | 0.69959 | -0.00314 | -0.00644 |
| P2 | astrocyte_gse330741 | 0.25175 | 0.69669 | -0.00175 | -0.00354 |
| P3 | astrocyte_gse330741 | 0.25270 | 0.69868 | -0.00270 | -0.00553 |
| H0 | mikl_gse173098 | 0.27625 | 0.75621 | -0.02625 | -0.06306 |
| P1 | mikl_gse173098 | 0.27111 | 0.74281 | -0.02111 | -0.04966 |
| P2 | mikl_gse173098 | 0.26513 | 0.72690 | -0.01513 | -0.03375 |
| P3 | mikl_gse173098 | 0.27194 | 0.74527 | -0.02194 | -0.05212 |
| H0 | srle | 0.25766 | 0.70889 | -0.00766 | -0.01575 |
| P1 | srle | 0.25219 | 0.69755 | -0.00219 | -0.00440 |
| P2 | srle | 0.25183 | 0.69682 | -0.00183 | -0.00368 |
| P3 | srle | 0.25138 | 0.69597 | -0.00138 | -0.00283 |

Every primary method remains worse than the constant-0.5 reference on both probability scores in all three replicate-covered whole-study evaluations. Thus P2's improvement over H0 in Brier/log loss should be understood as reduced probabilistic error; it does not demonstrate informative or calibrated transfer. Better calibration scores and useful discrimination are distinct. The frozen calibration-claim gate and decision gate both remain failed, and no abstention policy was activated.

The numerical reference is valid for the exact expected per-replicate scoring definitions used here. It is not the squared error against an empirical fraction, whose null score would differ. No hard-label, model, candidate, or evaluation endpoint changed for this calculation.
