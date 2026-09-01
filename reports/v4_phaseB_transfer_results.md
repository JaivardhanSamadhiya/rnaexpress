# RNAddress v4 Phase B transfer results

## Global-head-only rule

Every transfer result below uses the global head only. Target residuals are absent, target outcomes are not used for calibration, and source identity is not an input. These are development-only prospective-like simulations.

## Leave-source-out transfer

| Held source | Direction | Rank | Regret | Random regret | Metadata regret | Pass |
|---|---|---:|---:|---:|---:|---|
| Mikl | Decrease | 0.5050 | 0.5303 | 0.5239 | 0.5169 | No |
| Mikl | Increase | 0.5131 | 0.4753 | 0.4761 | 0.4749 | No |
| Moffatt | Decrease | 0.6004 | 0.2884 | 0.4093 | 0.2116 | No |
| Moffatt | Increase | 0.5290 | 0.5112 | 0.5907 | 0.4954 | No |
| TDP | Decrease | 0.6471 | 0.5801 | 0.6172 | 0.4535 | No |
| TDP | Increase | 0.4996 | 0.3703 | 0.3828 | 0.3417 | No |

The equal-source leave-source-out aggregate is rank 0.5490, regret 0.4593 versus exact-random regret 0.5000, Good@1 0.0605, Good@3 0.1345, and Good@5 0.1933. Decrease has rank 0.5842 and random-regret gain 0.0505; increase has rank 0.5139 and gain 0.0309. However, the contextual model loses to the strongest metadata/edit-size comparator on all six tasks. Gate C therefore fails.

## Cell-context transfer

| Transfer | Direction | Rank | Regret | Random regret | Good@3 | Pass |
|---|---|---:|---:|---:|---:|---|
| CAD → Neuro-2a | Decrease | 0.5079 | 0.5099 | 0.5253 | 0.2116 | No |
| CAD → Neuro-2a | Increase | 0.5447 | 0.4369 | 0.4747 | 0.2487 | Yes |
| Neuro-2a → CAD | Decrease | 0.5353 | 0.4926 | 0.5224 | 0.2116 | Yes |
| Neuro-2a → CAD | Increase | 0.5453 | 0.4567 | 0.4776 | 0.2434 | Yes |

Three of four directional cell-context tasks pass the frozen signal criterion.

## Reporter transfer

| Transfer | Direction | Rank | Regret | Random regret | Good@3 | Pass |
|---|---|---:|---:|---:|---:|---|
| Firefly → GFP | Decrease | 0.8082 | 0.2186 | 0.4180 | 0.3583 | Yes |
| Firefly → GFP | Increase | 0.6788 | 0.4721 | 0.5820 | 0.0333 | Yes |
| GFP → Firefly | Decrease | 0.7059 | 0.3216 | 0.3744 | 0.3722 | Yes |
| GFP → Firefly | Increase | 0.6372 | 0.5415 | 0.6256 | 0.1222 | Yes |

All four reporter tasks pass, so Gate D passes. This is the strongest positive Phase B result.

## Operation-class transfer

Seven frozen operation families were held out. Macro-averaged across families, decrease achieves rank 0.7163/regret 0.3224 versus random regret 0.4512; increase achieves rank 0.6098/regret 0.4665 versus random 0.5488. Results are heterogeneous: Mikl motif replacement is near chance, while several Moffatt operation families rank strongly. This supports operation-family signal but does not repair failed unseen-source transfer because operation and source are highly entangled in the available data.

## Interpretation

Reporter and cell-context transfer show that useful signal exists inside biologically related assay families. The decisive unseen-assay test does not establish representation value beyond edit metadata. Consequently, this is not evidence for a general unseen-assay RNA intervention rule.

Machine-readable sources: `results/v4_phaseB/transfer_aggregate_metrics.csv`, `transfer_biological_unit_metrics.csv`, `transfer_set_metrics.csv.gz`, and `transfer_scenario_audit.json`.
