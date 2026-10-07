# Exact-sequence context diagnostic

This is a postfit descriptive diagnostic, separate from model selection and the generalization gate.

Exact parent+mutant sequence pairs were matched between CAD/Neuro-2a in Mikl and GFP/Firefly in Moffatt. Ambiguous duplicate aliases were excluded without averaging. Parent sets use only candidates observed uniquely in both contexts. Candidate effect sign concordance and exhaustive aggregate pair ordering compare recorded contrasts; ranks are therefore assessed on the same candidate set.

Directional support uses at least two finite recorded within-context slots and a fixed Beta(.5,.5) tail rule of .9/.1. Within-cell pair preferences subtract candidate contrasts in corresponding slots. Cross-cell slots are never assumed paired. These support values are working binomial summaries, not calibrated biological probabilities or proof that replicate slots are independent. Shared WT measurements and correlations among mutants also prevent treating all pairs as independent observations. Moffatt reproducibility is unavailable because its admitted paired contrast matrix is missing.

| Study | Matched edits | Parent sets | Genes | Gene-macro effect sign agreement | Gene-macro pair-order agreement | Supported opposing effects | Supported opposing preferences |
|---|---:|---:|---:|---:|---:|---:|---:|
| mikl_gse173098 | 6880 | 2408 | 187 | 0.5777 | 0.5343 | 142 / 771 | 216 / 1008 |
| moffatt_gse334718 | 2586 | 6 | 6 | 0.7521 | 0.5492 | 0 / 0 | 0 / 0 |

Supported opposing directions/preferences are conditional counts, with overlapping candidates and pairs. Full counts, denominators, and gene/component summaries accompany this report. They cannot distinguish causal context dependence from systematic measurement/context artifacts without independent reconstruction or confirmation.

A reproducible opposing preference for the same two edits supplies an input ambiguity for an unconditioned deterministic sequence-only model: it cannot give both contexts opposite orderings. Conversely, weak aggregate agreement alone does not establish a biological context effect because sampling noise may generate disagreement. Endpoint conditioning separates nuclear retention from projection enrichment but does not separate CAD from Neuro-2a or GFP from Firefly; this diagnostic addresses that remaining gap.

Matched sequences are already exposed development observations. Any later cross-cell generalization experiment must exclude the matched gene/parent and all exact alleles from every training source. No model was fitted, no new source was discovered, no reserved outcome was opened, and no frozen input was changed.

Verification: 2 synthetic tests passed; all 45 prefit files remain unchanged. Source and code hashes are in context_diagnostic_receipt.json.
