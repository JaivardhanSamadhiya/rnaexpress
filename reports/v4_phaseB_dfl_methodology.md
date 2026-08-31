# RNAddress v4 Phase B decision-focused methodology

## Established basis

Phase B adapts candidate-ranking methods rather than claiming decision-focused learning itself as new.

- Mandi et al., [*Decision-Focused Learning: Through the Lens of Learning to Rank*](https://proceedings.mlr.press/v162/mandi22a.html), shows that pointwise, pairwise, and listwise losses can optimize solution ranking and regret over controlled solution subsets.
- Donti et al., [*Task-based End-to-end Model Learning in Stochastic Optimization*](https://proceedings.neurips.cc/paper/2017/hash/3fc2c60b5782f641f76bcefc39fb2392-Abstract.html), trains against downstream task quality rather than generic predictive likelihood.
- Wilder et al., [*Melding the Data-Decisions Pipeline*](https://ojs.aaai.org/index.php/AAAI/article/view/3982), differentiates through relaxed discrete decisions.
- Elmachtoub and Grigas, [*Smart Predict, then Optimize*](https://pubsonline.informs.org/doi/10.1287/mnsc.2020.3922), formalizes decision regret and SPO+ for linear optimization. The exact SPO+ construction is not used because RNAddress is a pick-one ranking task with observed utilities rather than prediction of a linear program's full cost vector.
- Yamao et al., [*Robust Decision-Focused Learning via Worst-Case Regret Minimization*](https://proceedings.mlr.press/v337/yamao26a.html), motivates uncertainty sets around observed objective coefficients. Phase B does not implement this robust loss because uncertainty is not semantically comparable across enough sources.

## Implemented losses

All definitive models use the same frozen candidate features and outer biological splits.

### Model 0: predict then rank

A regularized global effect model minimizes weighted squared error on training effects after training-set-only assay centering/scaling. Candidate scores are the predicted signed effect. Assay-specific residual models may be added only for seen-assay evaluation. They are absent for unseen-source, reporter-held-out, and cell-held-out transfer.

### Model 1: pairwise ranker

For direction `s`, training pairs within a decision set are labeled by the sign of `s(y_i-y_j)`. A regularized linear logistic/BPR loss is optimized on at most 2,048 deterministic, utility-stratified pairs per decision set per seed. Decision sets and sources receive equal aggregate weight. This is the pairwise ranking adaptation described by Mandi et al.; it does not require a differentiable downstream solver because the feasible actions are the measured candidates.

### Model 2: softmax decision-focused regret

For each training decision set and direction, scores are converted to a relaxed pick-one decision:

`p_i = softmax(score_i / temperature)`.

Utilities are normalized to `[0,1]` within the training decision set. The loss is:

`L_set = 1 - Σ_i p_i u_i`.

The oracle normalized utility is one, so this is expected normalized regret under the relaxed decision. All candidates are used; no held-out candidate or outcome enters a training set. Sets are averaged within source and sources are averaged equally. L2 regularization is added. This is a listwise pick-one specialization of established relaxed decision-focused/listwise ranking methods.

### Model 3: robust DFL

Not eligible for the definitive comparison. Mikl has valid paired-delta SE, TDP lacks pair-level uncertainty, and Moffatt raw-ratio SE is not uncertainty on the WT-normalized author effect. A cross-source worst-case utility set would therefore mix incompatible quantities. Mikl-only sensitivity analysis may evaluate uncertainty weighting, but it cannot select the global model and is not labeled robust DFL.

## Hierarchical score

The seen-assay score is:

`global_score(parent, intervention, geometry) + assay_residual_score`.

Source identity cannot enter the global head. A residual may use a source/assay key only to select a residual parameter block. For a held-out source, reporter, or cell context, the residual is exactly zero and no target outcomes are used for calibration.

## Decision metrics

For each held-out set and direction, Phase B reports directional rank percentile, normalized regret, raw selected experimental utility, GoodSelection@1/@3/@5, exact oracle recovery, near-optimal enrichment, and Spearman where defined. A good intervention has normalized regret at most 0.10. Metrics are macro-averaged by biological unit and source.

## Distinction from ordinary prediction

Predict-then-rank is selected by effect prediction and only later converted to a choice. Pairwise/listwise and DFL models are trained on within-set ordering or relaxed selected utility. A DFL claim requires lower held-out normalized regret or better GoodSelection@K than predict-then-rank; improved MSE or pooled correlation alone is insufficient.
