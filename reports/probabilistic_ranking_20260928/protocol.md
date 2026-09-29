# Probabilistic preference supervision: frozen development protocol

This generation starts at `363d5ba`. Prior cross-assay NO-GO and all historical results remain immutable. All four assays are development-exposed. No new data discovery or independent validation is part of this experiment, even if this first gate passes. A pass permits only a separately frozen representation-combination experiment. No spending, scheduled tasks, quarantined/reserved outcomes, broad pytest, prior modification, or new encoder.

## Controlled comparison and admission

Reuse the exact 26,258 primary measurements, parent/context roster, case-normalized gene/exact-allele components, original held-parent assignments, and whole-study purge from `cross_assay_20260927`. Assays are astrocyte GSE330741, Mikl GSE173098, Moffatt GSE334718 random substitutions, and SRLE. SRLE remains one HBB reporter and is ineligible for independent held-parent evaluation. The other sources have two, 187, and six gene components respectively, before cross-study purging.

The fixed sequence representation is the previous lowest-composite `interaction_3`: 246 metadata, 1–3-mer delta and ±3-nt parent×edit features. No new sequence representation is introduced. This choice follows the current user request and supersedes the earlier short-k-mer-only proposal. Four primary models H0/P1/P2/P3 have the same latent linear candidate utility, training-only feature scaler, L2=0.05, seed, weighting, optimizer and pair roster. Their only difference is the pair supervision.

Historical H0 is Bradley–Terry: sigmoid(s_i−s_j). Reproduce its original fitted scores and selected decisions before accepting any new comparison. All original held-study and held-parent train/test ID hashes must match. Reuse seed 20260927 for original within-context pair sampling: all unordered pairs if <=256, otherwise the same deterministic 256 pairs. Pair sampling precedes labels. Preserve all sampled pairs in the evidence table; training uses the original aggregate non-tie roster so H0 is exactly comparable. Aggregate ties remain evaluation/inventory records. No additional replicate-disagreement pair is deleted in P1/P2/P3.

## Replicate reconstruction and targets

Use only the already-admitted exact candidate-minus-WT replicate contrasts in the canonical table. Do not synthesize replicates from aggregate means/SEs. Astrocyte labels are 1–9 and 11–15; Mikl has three source-array slots, SRLE Rep1/2. Four expected Moffatt slots have no admitted paired contrasts and stay explicitly missing. These are paired localization contrasts, not absolute localization measurements. Raw Mikl/astrocyte estimators differ from author-processed targets; no claim of exact raw-to-published reconstruction is made.

For i/j in the same context, compare common finite replicate contrasts. Positive and negative differences use numerical tolerance 1e-12; differences within that tolerance are unresolved/tied and carry half a vote. No assay-independent biologically meaningful equivalence margin is known. Variable signs retain their uncertainty; small magnitudes are additionally addressed by P3. Record every magnitude, valid count, wins, losses, ties, mean, sample variance, aggregate difference, and target provenance.

* H0: original aggregate preference, q=0/1 for non-ties.
* P1: (wins + 0.5*ties)/n. Empirical replicate support, not a precise biological probability.
* P2: (wins + 0.5*ties + 0.5)/(n+1), symmetric weak Beta(0.5,0.5) prior. Half-ties are fractional working observations. Posterior tail and variance are working uncertainty summaries, not validated biological intervals.
* P3: normal latent-mean sign support Φ(mean(d)/sqrt(v_shrunk/n)), where v_shrunk=((n−1)*sample_variance+2*v_pool)/(n+1). Each v_pool is the pair-weighted mean within-pair sample variance from that training assay only (n>=2), floored at 1e-12. Pool weights retain context/component balance. For n=1, shrink to available source pool; if the training subset has no identifiable replicate variance, use P2 and flag it. P3 is a working latent-mean sign model, not the probability that another replicate will win.

If n=0, all methods use H0 with an explicit missing-replicate flag; this applies to Moffatt. No fabricated uncertainty. No held-out outcome, replicate, pooled noise estimate or performance-derived quantity enters training targets, scaling, weighting or optimization. Training target tables retain fold-specific P3 pooling parameters. The hard-raw-mean secondary control is necessary to separate estimator change from uncertainty modeling.

## Loss and matched weighting

Optimize weighted soft logistic cross-entropy plus L2=0.05 using zero-initialized L-BFGS-B, maxiter=500, ftol=1e-11, gtol=1e-7. H0 uses the original algebraic signed-logistic implementation for numerical replay. Weight equally by study, then biological component, then parent/context, then sampled training pair. Candidate scaler uses the original equally balanced row weights. Never duplicate pairs to approximate fractional labels.

Primary models are coherent latent utilities. Secondary models, run only after the four primary methods, are fixed in advance:

1. Hraw: hard sign of the mean common raw replicate differences (tie q=0.5; missing fallback H0), same latent architecture.
2. P2_weighted: P2 with reliability factor 0.25+0.75*abs(2*P1−1), missing-replicate factor 1. Renormalize within each parent before retaining original context/component/study totals; disagreement never receives zero weight.
3. Partial: keep a pair only when n>=2 and Beta posterior P(theta>0.5)>=0.9 or <=0.1; label by replicate majority. Missing-replicate pairs retain H0 and are flagged. Entire emptied contexts/components are explicitly counted; retained groups are rebalanced. This is a separately labeled deletion control, never the soft-label primary model.
4. H0_pairfree and P2_pairfree: same candidate representation, plus 17 antisymmetric adjacent-metadata wedge terms z_i[j]*z_j[j+1]−z_i[j+1]*z_j[j], j=0..16. Scale wedges by training pair-weighted RMS, with no intercept or centering, so p_ji=1−p_ij. This permits nontransitive pair classification. Fixed ranking is mean predicted pairwise wins over every other candidate, computed exactly in batches. No sequence architecture search.
5. P3_hetero: one Thurstone/probit variant. Derive dimensionless pair SE from source replicate variance divided by sqrt(v_pool), clipped to [0.25,4]. Fit a ridge noise head (L2=0.05) on intercept plus absolute differences of the first 18 standardized metadata features, targeting log(SE). It uses measurement structure only, no prediction errors. Missing/unidentifiable noise pairs do not fit this head. Use the head's clipped predicted scale in BOTH utility training and prediction; never use held-out measured uncertainty at inference. Fit soft probit cross-entropy with the same regularization and optimizer. Rank by exact expected pairwise wins. Record the working variance model and all fallbacks.

Secondary models do not rescue failure of the primary supervision hypothesis. Only P1/P2/P3 can be selected for the next representation-combination experiment. All secondary results remain visible. There is no broad prior, loss, seed or architecture search.

## Evaluation sequence

First run held-parent sanity checks for H0/P1/P2/P3 on the original component folds in astrocyte, Mikl and Moffatt. SRLE is ineligible. These checks do not select hyperparameters or redefine eligibility. Then run the fixed cross-replicate diagnostic, then four whole-study holdouts. H0/P1/P2/P3 precede the secondary grid. Preserve all completed fits and do not retry seeds.

Cross-replicate diagnostic: within each assay with available contrasts, split source slots into alternating A/B, then reverse. Train on A, evaluate B; no B values enter training targets or noise/scaler fitting. Use the same historically eligible candidate universe and original outcome-independent sampled pair roster, removing only training-mean ties for a matched four-model comparison. Here H0 is explicitly hard training-replicate-mean preference, not the author aggregate that includes B. P3 falls back to P2 when a one-replicate training subset cannot identify noise. This shares parents/sequences and is measurement robustness, not biological-context generalization. Replicate-mean outcomes differ from the author aggregate.

Whole-study evaluation uses exactly the established train/test ID hashes and gene/allele purge. Evaluate all four methods against the SAME held-out author/aggregate outcome. Secondary evaluation scores those same predictions on every omitted-replicate candidate set from the failure audit. Empirical cross-replicate decision reproducibility is recomputed on these exact same raw-outcome subsets using the other replicates. The recovery fraction (uniform−sequence regret)/(uniform−replicate regret) is reported only when the denominator >1e-12 on matched raw targets; it may be negative or above one. Never compare aggregate-target model regret directly with raw-replicate regret as a ceiling.

## Decisions, calibration and ambiguity

Primary metric: normalized selected regret, equally averaged across direction/context within component, components within assay, then four assays. Report per-assay and variant-weighted regret, median gain, helped/harmed counts, worst harm, all-pairs ordering accuracy, Spearman, direction selection, avoidable/unavoidable/neutral-only wrong selection, best/top-five recovery. Raw scales are never pooled.

BT candidate ranking uses latent score; pairfree/probit-hetero use expected pairwise wins. Lexical candidate ID breaks score ties. Both requested directions use the same roster. For every candidate retain latent score where defined, expected win fraction, minimum win probability, mean pairwise binary entropy, and rank. Entropy is a model diagnostic, not a confidence interval. Pairwise probability is not P(edit beneficial versus WT). Keep the historical H0 source-only direction head fixed across the matched methods for absolute-direction calibration diagnostics; it cannot demonstrate an uncertainty-supervision benefit. Correct/wrong selection uses observed signs independently of that head.

Calibration uses sampled held-out pairs with both orientations at half weight and the same biological hierarchy. Report expected per-replicate Brier q*(1−p)^2+(1−q)*p^2, log loss, ten fixed equal-width reliability bins, ECE, mean abs(2p−1) sharpness, and aggregate-label scoring separately. q is empirical replicate support with half-ties; Moffatt has aggregate-only scoring and cannot certify replicate calibration. Do not score calibration against smoothed targets as if they were observed truths.

Pairwise calibration improvement is declared only if the three replicate-covered whole-study evaluations show macro Brier reduction >=0.005 and log-loss reduction >=0.01 versus H0, no assay Brier harm >0.01, and macro ECE<=0.05. No calibrated-benefit or future-biological-probability claim follows.

Conditional conservative selection/abstention: eligible only if BOTH replicate-covered held-parent assays (astrocyte and Mikl) improve Brier >=0.005 and log loss >=0.01 with ECE<=0.05 versus H0. Then test the fixed maximin pairwise-win candidate and abstain unless its minimum win probability >=0.8. This means confidence versus measured alternatives, not confidence of improvement over WT. If no method qualifies, record NOT_RUN; do not retry the old absolute-benefit threshold.

Measurement ambiguity is separate from and never erases errors: with available replicates, a decision has a strongly supported unique optimum only if one candidate has Beta posterior superiority >=0.9 against every alternative with >=2 common replicates. Otherwise label AMBIGUOUS; missing replicate data are UNAVAILABLE. Directional reversal is handled explicitly. Report these alongside overall wrong-direction and feasibility failures; they overlap rather than partitioning away unfavorable outcomes.

## Frozen new gate and model selection

For each primary P1/P2/P3 require ALL of:

1. Four complete held-study evaluations and equal-study macro regret <=0.468, at least 0.020 below the user-specified 0.488 reference.
2. Macro gain >=0.020 against the original strongest-simple envelope, and >=3 of 4 studies improve over that envelope by >=0.020.
3. At least 3 of 4 improve over matched H0 by >=0.010.
4. Mikl and SRLE each worsen regret by at most 0.010 versus BOTH H0 and the simple envelope; no other study worsens versus the simple envelope by >0.050.
5. Macro avoidable-wrong increase <=0.020 and every-study increase <=0.050 versus BOTH H0 and the simple envelope.
6. Removing the best study still leaves positive gain versus the simple envelope; no study contributes >60% of positive gain.
7. Descriptive 95% lower component-bootstrap gain bound >=−0.010: 5,000 shared global-component Exponential(1) draws, seed 20260928, normalized within study. One-component SRLE uncertainty is degenerate; this is not a population-of-experiments interval.

Calibration is an additional condition for probability-calibration claims and for the conditional policies above, not a substitute for decision performance. Select only passing primary models by the old composite macro regret +0.25*macro avoidable wrong +0.05*fraction assays harmed +0.10*worst-study regret; ties within 1e-12 choose P1, then P2, then P3. Report all failures and secondary results regardless.

Prespecified descriptive hypothesis: gains might be larger in lower-repeatability astrocyte/Mikl than SRLE. Report every assay, plus the three-assay association with the recorded repeatability values; n=3 cannot establish mechanism or justify selection. No tuning to those assays.

If no primary model passes, preserve NO-GO and stop this generation. The tested uncertainty formulations then do not explain enough of the previous failure to enable the requested transfer; this does not prove label uncertainty has no role. No prior/smoothing/noise-formula retries. If a primary passes, freeze a distinct second experiment before combining representations; do not open a new independent dataset now.

## Audit and delivery

Preserve all eight required reports, seven CSV artifacts, nine figure topics, fitted parameters/scalers/noise heads, training target tables, ID hashes, fallbacks, and checksums in the new namespaces. Code, roster, features, targets and protocol receive a prefit manifest/commit before comparisons. Test soft-loss gradients, antisymmetry, probability limits, whole-study purging, training-only noise estimation, and H0 replay. Use bundled Python and local existing dependencies. Existing unrelated modifications remain untouched.
