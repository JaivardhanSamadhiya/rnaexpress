# RNAddress v4 decision-focused and data literature audit

## Question

Can a future RNAddress model optimize expected experimental decision quality—especially minimum-cost intervention selection—rather than generic pointwise prediction error, and is there a compatible public RNA-localization intervention source missing from Phase A?

## Decision-focused learning findings

The core literature supports optimizing downstream decision loss when predictive error and decision utility are misaligned:

- Donti, Amos, and Kolter, [*Task-based End-to-end Model Learning in Stochastic Optimization*](https://proceedings.neurips.cc/paper_files/paper/2017/hash/3fc2c60b5782f641f76bcefc39fb2392-Abstract.html), NeurIPS 2017, trains models against the downstream stochastic-optimization task.
- Wilder, Dilkina, and Tambe, [*Melding the Data-Decisions Pipeline*](https://ojs.aaai.org/index.php/AAAI/article/view/3982), AAAI 2019, differentiates through continuous relaxations of discrete optimization and shows that ordinary accuracy need not track decision quality.
- Elmachtoub and Grigas, [*Smart “Predict, then Optimize”*](https://pubsonline.informs.org/doi/abs/10.1287/mnsc.2020.3922), Management Science 2022, formalizes decision error and the tractable SPO+ surrogate for optimization with linear objectives.
- Cao et al., [*Learning to Rank: From Pairwise Approach to Listwise Approach*](https://mlanthology.org/icml/2007/cao2007icml-learning/), ICML 2007, provides listwise and top-k probability losses when whole candidate lists—not isolated examples—are the prediction unit.
- Wang et al., [*The LambdaLoss Framework for Ranking Metric Optimization*](https://research.google/pubs/the-lambdaloss-framework-for-ranking-metric-optimization/), CIKM 2018, ties metric-driven ranking losses to listwise ranking objectives.
- Garivier and Kaufmann, [*Optimal Best Arm Identification with Fixed Confidence*](https://proceedings.mlr.press/v49/garivier16a.html), COLT 2016, gives a formal basis for identifying the best candidate with bounded error under costly sampling.
- Chen et al., [*Nearly Optimal Sampling Algorithms for Combinatorial Pure Exploration*](https://proceedings.mlr.press/v65/chen17a.html), COLT 2017, generalizes best-arm and top-k identification to feasible candidate sets.

For selective output and risk control:

- Bates et al., [*Distribution-Free, Risk-Controlling Prediction Sets*](https://www.gsb.stanford.edu/faculty-research/publications/distribution-free-risk-controlling-prediction-sets), JACM 2021, controls expected loss for set-valued predictions using held-out calibration.
- Angelopoulos et al., [*Conformal Risk Control*](https://openreview.net/pdf?id=33XGfHLtZg), ICLR 2024, extends split conformal ideas to monotone risk functions.

These methods do not automatically solve RNAddress. Their guarantees depend on a correctly defined candidate set, exchangeability or other calibration assumptions, and leakage-free held-out groups. Parent-shared variants are not independent calibration examples.

## RNAddress decision formulation supported by Phase A

For a parent context `p`, assay context `a`, candidate set `C(p)`, cost `c(x)`, direction-specific effect `y_a(x)`, and safety/risk constraints, a future decision can be framed as:

`choose x in C(p) minimizing c(x), subject to predicted effect meeting the requested direction/magnitude and calibrated risk limits`.

Equivalent evaluation quantities are:

- realized regret against the best feasible measured candidate;
- excess edit cost relative to the minimum measured successful intervention;
- top-k recall of successful candidates;
- probability that at least one recommended candidate clears the effect threshold;
- abstention/coverage versus failure risk;
- direction-specific regret and reporter/cell-line robustness;
- Pareto regret over effect, edit cost, and uncertainty.

The natural training/evaluation instance is a **candidate set within one held-out biological parent**, not an individual row. Moffatt provides dense within-parent lists but few parents; Mikl and TDP provide thousands of parent contexts but usually smaller candidate lists. Their combination is useful precisely because these weaknesses are complementary.

## Recommended staged method, not implemented

1. Establish grouped predictive baselines and sign/magnitude calibration first.
2. Evaluate candidate-set regret without changing training loss.
3. Compare pointwise loss, pairwise ranking, listwise/top-k loss, and an explicit cost-sensitive decision surrogate under the same nested grouped splits.
4. Calibrate abstention or risk only on held-out parent groups.
5. Predeclare effect thresholds and edit budgets before looking at the final prospective benchmark.

Direct end-to-end decision loss should be accepted only if it improves held-parent realized regret without sacrificing calibration, direction fidelity, or assay robustness. Phase A does not authorize implementation.

## Targeted RNA-localization data search

The primary-source search through 2026-08-31 found no public source that should replace the current role assignments:

- Mikl/GSE173098 supplies many motif replacements across hundreds of genes and two neuronal cell lines.
- Arora/GSE183192 supplies forward 260-nt tiled activity in two reporters and two cell lines, but no general parent-mutant intervention mapping.
- The primary cortical-neuron N-zip study contains mutation designs, but RNAddress's raw reconstruction remains quantitatively non-certified; its outcomes stay NO-GO.
- Moffatt/GSE334718 is the major newly certified development landscape and now contributes five intervention mechanisms, two reporters, and raw biological replicates.
- [SRLE-seq](https://pubmed.ncbi.nlm.nih.gov/42179915/) studies nuclear/cytoplasmic localization in HEK293T using MALAT1 fragments and randomized 6-mers in an HBB reporter. It is valuable secondary evidence for short motif operations, but its fixed scaffold, compartment shift, and lack of a broad natural-parent intervention landscape make it unsuitable as an independent neurite/soma gate.
- Transcriptome-fractionation studies and sequence-only localization predictors are observational forward sources, not parent-mutant intervention truth.
- Astrocyte remains the protected in-vivo exact-SNV prospective benchmark and was not opened, used to define costs, or used to select architecture.

## Feasibility and novelty verdict

Decision-focused RNAddress remains feasible because Phase A now provides explicit candidate sets, exact edit costs, direction-specific measured utilities, replicate information, and 10,406 leakage-grouped parent contexts. It is especially well matched to shortlist prioritization and minimum-budget selection rather than universal effect regression.

The targeted audit found established methods for predict-then-optimize, listwise ranking, best-arm identification, and selective risk control, but did not identify a published system combining all of the following for RNA localization: exact parent-mutant sequence interventions, mechanism-aware edit cost, heterogeneous assay heads, direction-specific localization utility, parent-grouped candidate-set regret, and a sealed prospective biological benchmark. That makes the proposed integration plausibly novel; it is not a claim that each component is individually new or a substitute for a formal prior-art review.
