# Prespecified validation architecture

Frozen on 2026-08-26 before model development and before any aggregate astrocyte mutation outcomes were inspected.

## Development

- Central task: rank every possible SNV for a requested increase or decrease in N-zip neurite/soma localization.
- Development set: 3,540 measured SNVs from 12 N-zip parents. All tuning uses parent-grouped resampling; no mutant from a held-out parent may enter training.
- Mikl: 11,926 safely paired motif replacements from 6,104 parent sequences may support forward representation/pretraining and protected stability objectives. They are not treated as minimal SNVs or as the central rank benchmark.
- Arora: 7,360 processed 260-nt tiles per main table may support optional forward pretraining only.
- SRLE-seq: all 4,096 6-mers are a secondary fixed-backbone framework demonstration. It cannot be used as evidence of unseen-parent transfer.

## Locked internal test

The three N-zip parents whose SHA256 parent-ID digests sort first are locked: Cdc42_2 (300 SNVs), Cflar_1 (300) and Ndufa2 (255), totaling 855. The exact split is recorded in `data/manifests/nzip_parent_split.csv`. No model or hyperparameter may be selected using these outcomes.

Before unsealing, commit:

1. model artifact and environment;
2. predictions for all 855 candidates in both requested directions;
3. random, motif, retrieval, classical sequence and forward-model-plus-exhaustive-search baselines;
4. metrics, top-k values, protected-property bounds and bootstrap unit;
5. an immutable Git commit identifier and file checksums.

Primary metrics are parent-macro top-k measured gain, normalized discounted cumulative gain, best-in-top-k regret, direction success and bootstrap confidence intervals resampled by parent. Mutation-level confidence intervals are forbidden. Continuous metrics are primary; any success threshold must be chosen on development parents only.

## Locked external test

All 4,553 astrocyte SNVs across all eight 190-nt parents remain external. The feature-only artifact contains no outcomes. After internal lock and predictions are committed, unseal localization (`snin_ctxin_logFC`), ribosome occupancy (`ctxtrap_ctxin_logFC`), local translation (`paptrap_ctxtrap_logFC`) and expression contrasts derived from replicate counts.

Evaluate ranking separately within each parent and direction, then macro-average across eight parents. Report protected-property tradeoffs, all failures and per-parent heterogeneity. Do not tune, retrain, select a checkpoint or change thresholds after reveal. Exact gene overlap with the retained N-zip parents is zero and exact parent-sequence overlap is zero; this does not eliminate shared motif/assay-domain contamination.

## Baselines

- Random: seeded random permutation per parent/direction, repeated at least 1,000 times.
- Motif heuristic: fixed development-only neurite/soma motif log-odds and disruption/creation score.
- Retrieval: nearest development parent/window with measured edit transfer; abstain when no valid analogue.
- Classical sequence model: regularized linear/gradient-boosted model on k-mer change, position, GC and prespecified structure deltas.
- Forward model + exhaustive mutation search: score all `3L` SNVs and rank predicted target gain under protected-property constraints.
- Proposed method must add a distinct intervention-aware objective/calibration or it collapses into the forward-search baseline.

## Leakage prohibitions

No mutation-level random split; no external outcome feature engineering; no homologous parent in train/test; no threshold selected from external labels; no best-of-many external result; no dropping hard parents after reveal; no reporting only micro-averages; and no post-hoc protected-property definition.
