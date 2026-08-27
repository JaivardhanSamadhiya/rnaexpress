# RNAddress v2.5 Mikl published-model pretraining protocol

Frozen on 2026-08-27 before fitting any v2.5 external classifier. This stage uses Mikl outcomes only; it may not read N-zip outcomes, TDP-43 locked outcomes or astrocyte outcomes.

## Published basis

Mikl et al. trained separate XGBoost classifiers for significant neurite and soma enrichment using all 256 4-mer counts from each 150-nt biological insert. A neurite positive required positive localization log fold change with P < 0.05 in both CAD and Neuro-2a; a soma positive required negative localization log fold change with P < 0.05 in both. Their final localization score was `P(neurite) - P(soma)`, and their 4-mer model achieved reported held-out reporter auROC 0.83. The primary article is [Mikl et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC9561380/); the official library-design/mapping repository is [RNAloc_MPRA](https://github.com/martinmikl/RNAloc_MPRA).

The paper's strict read filter and sequence deduplication reproduce its 36,731-sequence modeling cohort exactly. Global removal of every normalized N-zip gene leaves 35,428 sequences across 304 genes, including 679 neurite positives and 177 soma positives. There is no full-parent or exact 31-mer overlap with N-zip. Exact source hashes and counts are frozen in `data/frozen/v2_5_mikl_xgboost_source_manifest.json`.

## Frozen external feature and model selection

- Use counts of all 256 lexicographically ordered DNA 4-mers from the 150-nt insert; primers and barcode are excluded.
- Use deterministic five-fold `GroupKFold` by source gene. All variants from a gene remain in one fold.
- Fit two `XGBClassifier` heads with `objective=binary:logistic`, `eval_metric=auc`, `tree_method=hist`, `n_estimators=500`, `subsample=0.8`, `colsample_bytree=1`, `reg_lambda=1`, `reg_alpha=0`, `gamma=0`, `random_state=20260826` and four CPU threads.
- Within each fold and head, set `scale_pos_weight` to training negatives divided by training positives.
- Evaluate the fixed Cartesian grid `max_depth in {3, 6}`, `min_child_weight in {1, 10}` and `learning_rate in {0.03, 0.1}`.
- Score each setting by the unweighted mean of neurite and soma out-of-fold auROC. Select the highest mean, breaking ties by shallower depth, larger minimum-child weight and lower learning rate.

After selection, refit both heads on all 35,428 decontaminated sequences with their full-cohort class weights. Freeze both XGBoost booster JSON files, selected settings, class counts, 4-mer order, source-row fingerprint, model hashes and the complete eight-setting CV table before defining or fitting a v2.5 N-zip candidate.

For later sequences shorter than 150 nt, the only permitted length adaptation is to multiply normalized 4-mer frequencies by 147, the number of 4-mer positions in a 150-nt insert. This equals raw counts for every external training sequence and prevents shorter N-zip fragments from being interpreted as globally depleted for every 4-mer. No N-zip outcome may alter this rule.
