# RNAddress v4 Phase B uncertainty results

## Valid uncertainty scope

Only Mikl standard errors are certified as effect uncertainty suitable for a sensitivity analysis. TDP has no pair-level uncertainty, and Moffatt raw-ratio diagnostic standard errors are not author-scale localization-effect uncertainty. Uncertainty was not fabricated or pooled across incompatible sources.

## Prespecified weighting sensitivity

Weights are inverse `1/(SE² + 0.25²)`, median-normalized, and clipped to [0.1, 10]. Relative to the unweighted model:

| Direction | Rank gain | Regret gain | Good@3 gain |
|---|---:|---:|---:|
| Decrease | -0.0208 | -0.0110 | -0.0344 |
| Increase | -0.0097 | -0.0053 | 0.0000 |

The frozen retention rule requires regret gain ≥0.01 without worse transfer. Weighting fails and is rejected.

## Robust DFL

Robust DFL was not implemented because a common, scientifically valid uncertainty set is unavailable across the three sources. This is a non-applicable Gate H, not a failed robust-model result.

## Auxiliary-label eligibility

- Stability auxiliary: not tested. Certified Mikl stability effects are all missing, and TDP EV5 remains quarantined because of duplicate keys.
- Structural auxiliary: not tested. Moffatt SHAPE identifies an intervention-design family; it is not a certified sequence-level structural outcome.

No unavailable label was inferred, imputed, or repurposed.
