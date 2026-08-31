# RNAddress v4 Phase B frozen development protocol

Protocol freeze date: 2026-08-31

Starting commit: `36e836ea1dfd0d20b688cb0b77f914aa9964955c`

Phase A verdict: `GO — STRONG DEVELOPMENT FOUNDATION`

## Scope and protected data

Eligible outcomes are only the Phase A certified Mikl/GSE173098, TDP-43/GSE288185, and Moffatt/GSE334718 records. N-zip outcomes are permanently prohibited. Astrocyte outcomes and labels remain untouched. No historical model result or N-zip representation winner may influence Phase B selection.

Phase B ranks finite measured interventions. It does not generate arbitrary edits, train on Astrocyte, or authorize prospective reveal.

## Decision sets

The exact construction and counts are frozen in `reports/v4_phaseB_decision_set_audit.md` and `results/v4_phaseB/decision_set_audit.json`.

- Mikl: gene × cell-context landscape.
- TDP: gene landscape.
- Moffatt: parent × assay-family × reporter landscape.
- Minimum five finite candidates and positive effect range.
- 445 eligible base sets and 890 directional tasks.
- Good candidate: normalized regret ≤0.10.

Direction is evaluated separately for requested increase and decrease. Raw assay effects remain unchanged. Within-set outcome normalization is allowed only for training labels and evaluation metrics; it never becomes an input feature.

## Biological splits

- Mikl primary: five deterministic hash folds by gene. Secondary: parent-held-out sensitivity within training genes.
- TDP primary: leave-one-gene-out over all 16 genes.
- Moffatt primary: leave-one-biological-parent-out over all 10 labels, reporting every parent. Exact-sequence-equivalent labels are co-held in a strict sensitivity analysis.
- All outcomes, reporters, intervention families, and variants for a held biological unit remain held out.
- No outcome statistic, scaler, residual, hyperparameter, or calibration component is fit on an outer test fold.

## Frozen representation benchmark

Maximum families: three.

1. **3UTRBERT 3-mer**, `yangheng/3utrbert`, pinned revision `220d80829deb077d1d640463a4267a96e9e70b1d`, local checkpoint SHA-256 `7aca71823ab74771006be1030d9e7239220bba40a16858575929a02e6d2a7471`.
2. **SpliceBERT 1024nt**, official Zenodo model archive SHA-256 `2d07fb041c3784a538559c368805ae84ca3daeb888772aa3bbe82f48dd576662`, selected checkpoint SHA-256 `2ad91428c318e6c49233154073ca7a35f5f7899c9f4be3444775bae3dba0149d`.
3. **RiNALMo 650M** is excluded before performance evaluation: this host has no CUDA runtime/GPU, no pinned local checkpoint, and the official 650M model would require multi-gigabyte weights and CPU inference over tens of thousands of 150–260-nt pairs. Acquiring a new runtime would make the comparison operationally incomparable. The exclusion is computational, not biological.

The benchmark cohort contains every eligible decision set and at most 64 candidates per set, selected outcome-blind by deterministic candidate hash with round-robin edit-band coverage. Both evaluated encoders use frozen weights. For each pair, extract parent absolute, mutant absolute, global delta, edited-region delta, and radius-10 local delta. Each semantic block is compressed by a fixed seed-41017 sparse random projection to equal 128-dimensional blocks.

The matched learner is `StandardScaler + Ridge(alpha=100)`. Scaling is fit inside the training fold. The target is training-set directional rank utility. Evaluation uses held biological units and equal source weighting. Representation selection score is the equal-weight mean of directional rank percentile and `1-normalized_regret` over source and direction. If scores differ by less than 0.01, prefer SpliceBERT because it is smaller and faster. One representation is then frozen for all definitive comparisons.

## Frozen intervention features

No sequence is truncated. Caches are keyed by exact sequence SHA-256. Candidate features contain:

- parent absolute representation;
- mutant absolute representation;
- contextual mutant-minus-parent delta;
- edited-region and radius-10 local deltas;
- changed-base/edit-distance count;
- changed fraction and operation-aware edit cost;
- insertion, deletion, replacement lengths;
- changed-block count, mean/first/last edit position, and edit span;
- GC/A/C/G/T composition changes;
- broad operation class and Phase A edit-cost tier.

Source identity is absent from the global head. Source/assay identity may select a residual head only. Intervention metadata and sequence representations are fitted/scaled on training groups only.

## Definitive model families

### Model 0 — predict then rank

Regularized global Ridge effect model plus optional assay residual Ridge. Alpha grid `[1, 10, 100, 1000]` is selected by three-fold inner biological-group normalized regret. Residual alpha is fixed at 100.

### Model 1 — pairwise ranker

Regularized linear pairwise logistic ranker, separately optimized by direction. Candidate C grid `[0.01, 0.1, 1.0]`, selected by inner normalized regret. At most 2,048 deterministic utility-stratified pairs per training decision set.

### Model 2 — decision-focused regret model

Linear softmax pick-one model using all candidates in each training set. Temperatures `[0.10, 0.25, 0.50]`, L2 coefficients `[1e-4, 1e-3, 1e-2]`, Adam learning rate `1e-3`, maximum 150 epochs, early stopping patience 15 on inner grouped normalized regret. Gradient norm is clipped at 5. Direction-specific heads are trained separately.

### Model 3 — robust DFL

Excluded from model selection because comparable outcome uncertainty does not exist across enough sources. A Mikl-only uncertainty-weighting sensitivity may be reported; no TDP uncertainty is fabricated and Moffatt diagnostic SE is not treated as author-effect SE.

Prespecified seeds are `[17, 41, 89]`. No full encoder fine-tuning is allowed.

## Baselines and ablations

Mandatory: exact random expectation, edit-size heuristic, parent-only, mutant-only, edit-only, metadata-only, source-only, nearest-neighbor retrieval, predict-then-rank, and absolute forward difference `f(mutant)-f(parent)`. Representation ablations are parent only, mutant only, delta only, parent+delta, and metadata only.

Negative controls: outcome permutation within source, intervention permutation within decision set, parent permutation, source-only, edit-size-only, and parent-only. Permutations are deterministic per seed and verified by tests.

## Transfer evaluations

- Leave-Mikl-out, leave-TDP-out, and leave-Moffatt-out; global head only.
- Moffatt GFP→Firefly and Firefly→GFP; global head only.
- Mikl CAD→Neuro-2a and Neuro-2a→CAD; global head only.
- Leave edit tiers out for small (2–5), motif (6–12), regional (13–99), and large (≥100), where at least five test candidates exist per set.
- Edit-size bands: exactly 1, 2–5, 6–10, 11–25, 26–50, and >50.
- Train excluding 1–5 and test 1–5; train excluding 1–10 and test 1–10.
- Exact 19 SNVs are descriptive only and cannot independently pass a gate.

## Metrics and weighting

Primary priority: normalized regret, selected normalized utility, GoodSelection@3/5, directional rank, unit robustness, and leave-source-out transfer. Report raw selected utility only within source/assay scale. Spearman and MSE are secondary.

Metrics are first macro-averaged over eligible decision sets, then biological units, directions, and sources. Every source has equal selection weight. Candidate-rich Moffatt parents do not receive row-count weight.

## Numerical development gates

All gains are paired on identical held-out decision tasks.

- **A — within-source:** selected candidate must lower normalized regret by at least 0.01 and improve directional rank by at least 0.01 versus the strongest conventional baseline in at least two sources, with no source degradation worse than 0.03.
- **B — robustness:** median biological-unit regret gain >0; more than 50% of units improve; leave-best-unit-out mean gain >0; paired bootstrap mean gain >0 with 95% lower bound no worse than -0.005.
- **C — leave-source-out:** global-only rank >0.52, regret below exact random by ≥0.02, and metadata/edit-size regret improvement ≥0.01 on at least two of three source holdouts. Collapse on all three is NO-GO.
- **D — reporter/cell transfer:** global-only rank >0.52 and regret below random by ≥0.02 in at least two of the four directional CAD/N2A transfer tasks and at least two of the four directional GFP/Firefly tasks.
- **E — small-edit bridge:** 2–5 and 1–10 held-out regimes each require rank >0.52, regret below random by ≥0.02, and degradation in rank ≤0.10 relative to all-edit global transfer. Sharp collapse fails Astrocyte readiness.
- **F — direction:** a direction passes only if rank >0.52 and regret below random by ≥0.02 in at least two sources and in the equal-source leave-source-out aggregate. Directions pass independently.
- **G — DFL value:** Model 2 must improve normalized regret by ≥0.01 and GoodSelection@3 by ≥0.01 over Model 0 in at least two sources, with no source regret degradation >0.03. Otherwise DFL is dropped.
- **H — robust DFL:** not applicable unless the uncertainty audit reverses the predeclared exclusion; it may not be added after seeing model results.
- **I — controls:** permutation-control rank and regret must be within 0.02 of their exact random expectations after source/direction macro-averaging; no control may beat the real model by chance-consistent margins without diagnosis.
- **J — seeds:** primary equal-source regret standard deviation ≤0.02 and the categorical verdict must agree across all three seeds.

## Auxiliary tasks

Mikl/TDP stability is tested only as a training-only auxiliary ablation; measured stability is never required at inference. It is retained only if held-group localization regret improves by at least 0.01 without worsening source transfer.

Moffatt SHAPE is an intervention design family with localization outcomes, not a measured sequence-level structural label. No structural auxiliary head is authorized unless a provenance-valid structural target is found without using outcomes to redefine the protocol.

## Stop and verdict

The final verdict must be one of the six Phase B choices in the controlling prompt. A Phase B GO authorizes only a separate Phase C prospective freeze. It does not authorize Astrocyte inspection or prediction. At Phase B completion, stop.
