# RNAddress internal-model preregistration

Frozen: 2026-08-26, before model fitting. Parent split and external quarantine were previously frozen at commit `358109d46cd19ca312f6ebdadebc936626f69f85`.

## Primary hypothesis

RNAddress will rank localization-changing single-nucleotide edits on completely held-out parent sequences better than random selection, substitution averages, motif heuristics, retrieval, local sequence regression, and a strong absolute forward model followed by exhaustive mutation search.

## Benchmarks and inference unit

- Primary internal benchmark: N-zip parent-held-out SNV recommendation.
- Development: 3,540 SNVs from 12 parents.
- Locked internal test: 855 SNVs from Cdc42_2, Cflar_1 and Ndufa2. These outcomes are not used for reliability analysis, feature construction, model selection or hyperparameter tuning.
- Primary external benchmark: zero-shot candidate ranking on all eight sealed astrocyte SN-MPRA parents. No outcomes may be read before external freeze.
- Primary unit of inference: parent sequence, never individual mutation.

The frozen three-parent lock is retained. Model selection uses nested leave-one-parent-out evaluation over the 12 development parents. After selection is frozen, the chosen method and every baseline are fit on all 12 development parents and evaluated once on the three locked parents. Only then may the 12 cross-fitted development predictions and three locked-parent predictions be combined into a transparent 15-parent descriptive table; confirmatory inference remains centered on the three-parent lock and uncertainty is reported at parent level.

## Task and candidate set

For each unseen parent and each requested direction (increase or decrease neurite/soma localization), enumerate every assayed SNV and rank it. Candidate identity is `(parent sequence, zero-based position, reference base, alternate base)`. Multi-edit design is out of scope until this task succeeds.

Primary outcome is measured mutant-minus-parent localization change, `delta_localization`. Directional measured utility is `delta_localization` for increase and its negative for decrease. No measured parent outcome is supplied as a model feature.

## Threshold policy

Continuous ranking is primary. Binary success is secondary and uses a development-only threshold fixed by the following rule:

`T_L = max(0.25 log2 units, 1.96 * robust_sigma(WT - shScramble) / sqrt(2))`,

where `robust_sigma(x) = median(|x - median(x)|) / 0.67448975`, computed across development-parent SNVs with both N-zip fields. This rule is based on an a priori biological floor and negative-control assay disagreement; it is not adjusted for class balance or locked-test performance.

## Primary and secondary metrics

Metrics are computed within parent and direction, averaged over the two directions within parent, then macro-averaged over parents.

1. Selected experimental rank percentile, best = 1 and worst = 0. This is the primary model-selection metric.
2. Normalized regret: `(best measured utility - selected measured utility) / measured utility range`, clipped only for a zero range, where it is defined as zero.
3. Experimental regret in log2 localization units.
4. Success@1, Success@3 and Success@5: whether any of the top K recommendations has measured utility greater than `T_L`.
5. Precision@1, @3 and @5: fraction of the top K recommendations exceeding `T_L`.
6. Within-parent Spearman correlation of predicted and measured edit effects.

The development model-selection tie-breakers are macro Spearman, then Success@3. RMSE is diagnostic only.

## Exact random baseline

For `M` successful edits among `N`, random `Success@K = 1 - choose(N-M,K)/choose(N,K)` and random `Precision@K = M/N`. Expected selected effect is the candidate mean, expected rank percentile is 0.5, and expected regret is best utility minus mean utility. Exact order-statistic weighting is used for expected best-of-K regret. Monte Carlo is not the primary random result.

## Models fixed for comparison

- `substitution_mean`: training-parent mean delta for each reference-to-alternate substitution, with global-mean fallback.
- `local_ridge`: ridge regression on edit identity, normalized position, edit-centered one-hot context and parent/local GC. Inner choices: context radius 5 or 10; alpha 0.1, 1, 10 or 100.
- `motif_delta`: additive creation/destruction score from training-only 3–6-mer effect tables with minimum support 5 or 10; inner selection chooses k/support.
- `retrieval`: similarity-weighted mean of training edits with the same substitution, using edit-centered context Hamming distance. Inner choices: radius 5 or 10 and neighbors 5, 15 or 50.
- `forward_extratrees`: absolute sequence model trained to predict mutant localization; candidate score is predicted mutant minus predicted parent. Sequence representation is padded positional one-hot plus normalized 2–4-mer frequencies. Inner choices: 300 trees, leaf size 2, 5 or 10; maximum feature fraction 0.5 or 1.0.
- `intervention_extratrees`: direct delta model using parent global sequence, edit identity/position, local context and mutant-minus-parent k-mer changes. Same tree grid.
- `pairwise_rank`: linear logistic pairwise ranking over direct intervention features. Within each training parent, deterministic pairs from different measured-effect quantiles are sampled; C is 0.1, 1 or 10.
- `mikl_only`: shared k-mer intervention model trained only on Mikl multi-base replacements with intervention type and edit count explicit.
- `intervention_plus_mikl_prior`: direct N-zip model augmented by the frozen prediction of `mikl_only`.
- `nzip_mikl_joint`: shared direct-effect model fit jointly with dataset indicator and equal total weight per dataset.

All stochastic models use seed `20260826`. Candidate features may use sequences, edit identity, position, dataset identity and development-derived motifs. They may not use astrocyte outcomes, locked N-zip outcomes, source gene identity as a predictor, or measured parent localization.

## Nested development selection

For each of 12 development parents, hold that parent out. For every candidate model, select its hyperparameters using grouped leave-one-parent-out folds among the remaining 11 parents and the primary rank-percentile metric. Fit the selected configuration to those 11 and predict the outer parent. Aggregate the 12 genuinely out-of-parent predictions. Select one final RNAddress configuration by primary metric; ties within 0.005 use Spearman then simplicity.

Mikl is retained only if its development outer-fold gain over N-zip-only intervention modeling is positive and is not driven by two or fewer parents.

## Parent similarity and hostile checks

Before internal reveal, calculate sequence similarity without outcomes. Report exact duplicates, maximum local identity and k-mer similarity. After the locked result, run GC-only, metadata-only where available, shuffled-label, shuffled-edit-identity, local-only, leave-gene-out/cluster-held-out, alternate normalization and leave-best/leave-worst-parent sensitivity analyses. Any post-lock analysis is labeled diagnostic and cannot change the locked model.

## Internal GO gate

The internal gate passes only if the selected RNAddress method:

1. exceeds exact random selection on primary rank percentile and normalized regret;
2. exceeds or meaningfully extends the strongest forward-search baseline on the 12-parent nested development evaluation;
3. is not supported solely by one or two parents;
4. shows the same direction of advantage on the three-parent locked test, acknowledging its low power.

If criterion 2 fails, the custom algorithm is not claimed necessary. If criteria 1, 3 or 4 fail, external outcome reveal is not authorized; outcome-blind predictions may be archived for future work, but the external benchmark remains sealed.

## External freeze prerequisites

Before outcome access, commit the final architecture, datasets, features, objective, hyperparameters, threshold, baseline definitions, seed, checkpoint hashes, prediction-code hash and complete outcome-blind rankings for all 4,553 astrocyte SNVs. Any confidence score is trained/calibrated without external outcomes. The prediction file is hashed and committed. No model modification follows reveal.
