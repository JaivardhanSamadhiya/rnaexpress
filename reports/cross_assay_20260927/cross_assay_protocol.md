# Frozen exposed multi-assay ranking protocol

This is a distinct development study, informed by historical failures. It does not alter any old gate or restore untouched status. The protocol, canonical roster, feature arrays, model/metric code and exact new gate are committed before the completed model comparison is generated. No future independent resource is inspected at this stage.

## Targets and models

Primary target: relative utility among all eligible small edits of one measured parent/context. Train Bradley–Terry linear scores using candidate-feature differences and logistic preference loss. Raw localization scales are never pooled as continuous targets. Strict positive candidate effect relative to WT supplies a separate logistic direction head; score sign alone is not treated as calibrated localization change. A separate group-level logistic model estimates whether any candidate can meet the requested direction.

Features: edit size, log available-parent length, normalized edit midpoint/square, span fraction, boundary flag and twelve substitution counts (metadata); metadata plus four composition changes; metadata plus 1–2-mer changes; metadata plus 1–3-mer changes. All counts use exact overlapping words and explicit mutant-minus-parent differences. The compact interaction model adds Δmono × parent-local mono/dinucleotide frequencies and Δdinucleotide × parent-local mono frequencies. Test ±3, ±10, ±25, ±50 and full available context, no further window search. A wider unchanged flank cannot change the 1–3-mer difference itself; it changes the parent interaction features. No 4–6-mer search or neural training is justified before these simple models establish transfer.

Models: metadata, composition, delta2, kmer123; shared kmer123 plus assay residual; empirical-Bayes coefficient combination of independently fitted source kmer123 models; and the five interaction windows. All regularized logistic objectives have L2 penalty 0.05, fixed seed 20260927, at most 500 L-BFGS iterations with fixed convergence tolerances. Residual coefficients receive 10× stronger regularization. Hyperparameters are fixed, not selected from target-study performance. Preprocessing mean/std uses training-only hierarchical weights. Held-out studies receive **zero assay residual**, with executable checks. Residual/universal contribution is reported in exposed within-assay and held-parent tasks and is predictive, not causal attribution.

The coefficient-combination model uses source-specific coefficients on the same training-derived scale, working penalized-Hessian diagonal variances divided by training component count, nonnegative method-of-moments between-source variance, and inverse-total-variance shared coefficients. With only two or three training studies this is a descriptive shrinkage model, not a trustworthy meta-analytic biological variance estimate.

Each study has equal total loss weight, then each connected gene/exact-allele group, then each parent/context, then candidate pair. Use all unordered pairs where at most 256 exist; otherwise uniformly sample 256 unique unordered pairs with a context-hash seed before consulting labels. Exclude sampled exact truth ties; normalize remaining weights. Report all-pairs ordering accuracy in evaluation. No seed search, direction flip, significance filter, top-effect candidate subset or post-result model addition is allowed.

## Evaluation and biological units

Core studies: SRLE, GSE330741 astrocytes, GSE173098 Mikl and GSE334718 random substitution. Primary candidates have 1–6 actual corresponding-coordinate substitutions. A valid candidate set has >=2 finite candidate outcomes and nonzero effect range. Both requested directions use the identical candidate roster and one score orientation. Ties use lexical intervention ID. Exact measured ties share best status. Candidate-set size, effect span and source operation remain visible.

Primary evaluation holds out one entire study, including every cell/reporter, and purges any matching biological component or exact allele from training in all other sources. Thus a source study's alternative reporter cannot leak its variants into its own test. Three fixed component folds provide within-study held-parent evaluation; SRLE is ineligible because it has one biological reporter component. Resubstitution is explicitly labeled optimistic and is not validation. Shared case-normalized gene names and all identical alleles are co-grouped before splitting; no claim of complete paralog or near-sequence independence is made.

H2 family restriction trains only on the same endpoint class; projection has three core studies, while nuclear SRLE has no second core training study and is ineligible. Domain holdout separates projection versus nuclear/cytoplasmic systems without claiming they represent the same mechanism. The fixed kmer123, hierarchical and interaction_10 models support these secondary checks. SIRLOIN discovery Rep1/2 receives separate exposed secondary predictions from core training; no reserved outcomes enter it.

Only after the simple model tasks, compare archived frozen 3UTRBERT pooled allele deltas plus kmer123 against matched kmer123 on complete candidate contexts with exact cache coverage in Mikl/Moffatt. The other two core studies lack admitted cached embeddings; no missing-vector fill or substitute encoder is allowed. This two-study comparison cannot pass the four-study gate. Existing mixed Torch/OpenVINO inference limitations remain inherited. It tests candidate regret, not merely correlation. No new encoder is trained or large checkpoint downloaded.

## Metrics and risk

Primary: normalized selected regret, averaged across directions/parent-contexts within biological component, then equally over components within study, then equally over the four held-out studies. Also report candidate-row-weighted metrics, raw regret only within source units, exact all-pairs ordering accuracy (predicted ties half credit), parent Spearman, direction accuracy, wrong-direction rate, best/top-five recovery, and every per-study result.

Separate wrong choices where all candidates move the wrong way from avoidable wrong choices where at least one achieves the requested direction. If only neutral alternatives exist, retain an explicit third category rather than calling those either successful or all-wrong. Report overall wrong direction alongside the decomposition. Positive effect is strict >1e-12.

Abstention is fixed in advance: accept only when **both** selected-candidate desired-direction probability and candidate-set feasibility probability are >=0.8. Both heads train only on allowed training studies/parents. These probabilities are model-based and not proven externally calibrated. Report coverage-risk curves at thresholds [0,0.5,0.6,0.7,0.8,0.9,0.95]; never select the best target cutoff. Report rejected decisions, conditional regret, direction and avoidable failures. Margin and standardized feature distance are retained as diagnostics, not used to invent another threshold.

Prespecified size sensitivity uses 1, 2–3 and 4–6 substitutions; locality sensitivity span<=6. Re-rank saved predictions on these design-defined subsets only when >=2 candidates and nonzero observed range remain. No subgroup can replace the main gate.

## Exact gate and selection before results

Benchmark is the strongest simple comparator **within each held study** among uniform expectation, metadata ranker and composition ranker, ranked by lowest macro regret, then fewer avoidable failures, then lexical name. This is a conservative post-evaluation comparator envelope, not an outcome-informed training rule or deployable oracle baseline.

A candidate architecture must satisfy **all**:

1. All four core studies evaluated; at least three improve regret by >=0.02 against that comparator.
2. Equal-study macro regret improvement >=0.02; leave-the-best-study-out improvement >0.
3. No study accounts for >60% of total positive regret gain.
4. Macro avoidable wrong-direction worsening <=0.02; no individual study worsens it by >0.05.
5. No individual study worsens regret by >0.05.
6. Descriptive 95% Bayesian component-bootstrap lower bound for macro gain >=−0.01.

Use 5,000 fixed independent Exponential(1) weights over global biological components, sharing a component's weight across every source/context where it occurs and normalizing within each study. This Bayesian bootstrap avoids treating repeated study contexts as independent and avoids silently discarding draws without a one-component study. One-component SRLE has degenerate within-study uncertainty; this procedure does not estimate uncertainty over an unlimited population of experiments. Four studies and heterogeneous source breadth limit all broad claims.

Only passing models can be selected. Fixed composite: `macro_regret + 0.25*macro_avoidable_wrong + 0.05*fraction_studies_harmed + 0.10*worst_study_regret`; ties within 1e-12 prefer fewer features then lexical model name. All models and failures stay visible. If none passes: **NO-GO, stop, no independent-dataset search or outcome access**. A descriptive lowest-score model is not a validated final system. A pass permits only a separate metadata-first search and new source-specific committed validation protocol; it is not independent confirmation.

No model/feature/gate revision follows this comparison. The historical SRLE and Astrocyte statements and exposure records remain intact. No money, scheduled tasks, broad pytest or protected-data access is permitted.
