# Final claim: predicting the localization consequence of a small RNA edit

**Within the measured SRLE HBB reporter assay, sequence-based models predict localization changes associated with composition-preserving two-position substitutions.** On the original 1,744 directed candidate links, frozen short 1–3-mer predictions correlate with measured changes at **r = 0.609 and 0.597** in the two reconstructed replicates, with **73.1% and 70.3% sign accuracy**. Quantitative RMSE is **0.272 and 0.294**, compared with **0.344 and 0.366** for composition-only/no-change prediction. The localization endpoint is mutant-minus-parent **log2 nuclear-retention score**.

These edits change **two positions within a six-nucleotide element**. This is neither a single-nucleotide result nor a claim that six bases were replaced. Composition is held constant, so the signal reflects sequence order beyond base composition. A simple short-mer model is a strong competitor; the positional-pair model does not demonstrate a unique advantage over it.

The corresponding Pearson 95% composition-class bootstrap intervals are **[0.565, 0.649]** and **[0.533, 0.664]**. These intervals describe the fixed experiment and models; candidate edges overlap and are not independent biological replications. The 592 candidate anchors are sequences within **one shared reporter context**, not 592 independent parent RNAs or genes. Source training and replicate evaluation arise from the same experiment. Exact held-out sequences do not establish held-out biological parents, context, or assay. Full raw-to-author-Table-5 measurement lineage remains **PARTIAL**.

The original within-assay candidate-selection result is preserved, including its errors. Positional-pair choices move in the wrong direction in both replicates for **20.78% of decrease and 23.57% of increase** decisions; short-mer rates are **25.13% and 22.11%** (composition-class weighted). Predictability does not mean dependable choice for every candidate set.

## What the stronger evaluation showed

The new frozen Mikl study directly tested author-processed mutant-minus-WT **log2(neurite/soma)** change with held-out parent genes. It produced **19,438** predictions, separately for CAD and Neuro-2a, using only one-to-six-base substitutions. All ten nested training selections chose short 1–3-mer features rather than the paired interaction representation.

For four-to-six-base substitutions, selected-model effect correlations were only **0.032 CAD / 0.037 Neuro-2a**. Direction balanced accuracy was **0.518 / 0.515**. On candidate sets from **173 genes**, normalized selection regret was **0.504 / 0.503**, compared with **0.500** for uniform selection averaged across desired directions. The model did not convincingly outperform ΔAU; paired regret gains were **−0.0057 [−0.0515, 0.0385]** and **0.0181 [−0.0236, 0.0603]**. Quantitative MSE was worse than ΔAU in both cells by paired gene-bootstrap intervals.

One-base Mikl evaluation has only **13 variants from 11 genes per cell**, with no multi-candidate parent sets. SIRLOIN supplies **223 finite single-base variants from two parents**, but frozen source-model effect predictions do not transfer consistently across its two discovery replicates. Neither supports a broad single-nucleotide prediction claim.

## Exact scope of the defensible conclusion

- **Supported:** bounded prediction of two-position swap effects in the measured SRLE reporter experiment, beyond composition-only controls, with competitive simple short-mer models.
- **Not established:** reliable single-base prediction, a unique advantage of a complex architecture, general small-edit selection for unseen biological parents, unseen-context or unseen-assay transfer, independent experimental confirmation, or a new molecular mechanism.
- **Novelty:** not certified by this analysis. Prior literature assessment and the provenance limitations still apply; an empirical association or new evaluation alone does not establish a completely novel mechanism.
- **Status of other evidence:** prior failed gates remain failed. The new Mikl folds prevent current training leakage, but their already-exposed source makes this exploratory development evidence.

## Next three tasks, in order

1. Finish the outstanding SRLE measurement-lineage audit from the already-admitted source materials: identify the exact author production transformation and resolve the remaining replicate/normalization ambiguity without changing frozen predictions or gates. Until resolved, retain the PARTIAL provenance label.
2. Specify an independent confirmation dataset contract: measured reference and multiple one-to-six-base mutants for multiple independent parents, replicated localization outcomes, declared coordinates, compatible scales, and admission rules fixed before outcome access. The current inventory does not supply a clean unused cohort satisfying this contract; additional discovery remains blocked, not exhausted.
3. Only after a qualifying dataset is independently admitted, apply a single frozen predictor and all simple controls once, using parent/gene grouping and direction/selection risk as well as correlation. Until then, present the bounded SRLE result and the full Mikl/SIRLOIN failures together.

## Do not touch

Do not open Astrocyte, N-zip or quarantined TDP EV5 stability outcomes; do not use reserved SIRLOIN outcomes; do not load unadmitted source outcomes. Do not change historical NO-GO records, frozen representations, splits, hashes, candidate neighborhoods, seeds, tie rules, models or gates. Do not overwrite previous results or unrelated working-tree changes, add unmeasured RNA designs, rerun model searches against exposed test outcomes, spend money, create scheduled tasks, or claim independent validation from another split/replicate of the same experiment.

## Confidence gaps

The remaining scientific gaps are independent small-edit parent diversity, compatible and repeatable paired measurements, unresolved full SRLE production provenance, and absence of independent confirmation. External discovery is blocked and cannot be described as an exhaustive negative search. The existing results do not determine whether a better model would overcome these limits; no success guarantee or competition outcome follows from them.

All quantitative tables, seven figure categories and per-candidate predictions are linked in [the results report](small_edit_prediction_results.md). The primary goal remains predicting the consequence of an edit; the broader version of that goal is **not yet achieved**.
