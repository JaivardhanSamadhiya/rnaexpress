# Frozen SRLE small-edit prediction and sequence-group evaluation

26 September 2026. User-directed fixed reanalysis of **already-exposed SRLE data**. Historical model results and outcomes are known. Freeze this complete analysis and code before new aggregate comparisons; commit the freeze before fitting. No external discovery, requests, provenance search, new outcomes, architecture search or historical-record changes. The prior 27.0428705752478% squared-error reduction has already replayed exactly, including its historical confidence interval. This is a computational requirement, not independent confirmation.

## Units, estimands and fixed cohorts

The experiment measures all 4,096 local six-mers in a shared HBB reporter assay. Use only the admitted published NRS(log2FC) score table, original predictions/split, saved constituent NRS1/NRS2 and archived raw-covered candidate decisions. The full reporter sequence and physical clone identities are not established in the admitted row-level table; leave missing rather than reconstructing a speculative full sequence. Source raw-to-author-Table-5 provenance remains PARTIAL and does not prevent this explicitly bounded predictive analysis.

Describe the edit class as **composition-preserving six-nucleotide sequence swaps / localized six-mer edits**. The fixed existing swap roster exchanges two unequal bases inside that six-position window: **two changed positions, not six substitutions and not a single-nucleotide edit**. Record the two positions and their span. All candidates are already measured sequences; no unmeasured designs are generated.

Preserve the original 3,234 training / 862 test sequence assignment. Score the same original 855 eligible test sequences from 70 composition classes at every evaluation level. Use the same 1,744 directed candidate links, 592 anchors and 60 composition classes in the original raw-covered candidate roster. Its historical eligibility includes >=2 test candidates, nonzero published candidate range and >=20 raw counts in each of four libraries for the whole neighborhood; disclose that outcome/coverage conditioning rather than claiming a wholly outcome-blind cohort. Replicate candidate ranges must remain nonzero or stop with an error. Do not filter additional examples.

The 592 anchors are not independent biological parents. Candidate links overlap and include reverse pairs. There is **one biological reporter context**, two admitted constituent replicate pairs, 70 statistical score groups and 60 statistical candidate groups. These are not 70/60 independent biological experiments. No biological-family IDs or second parent context exists in this admitted table.

## Analysis A: direct held-out prediction

Fit published score y=f(sequence); predict the edit consequence as f(candidate)-f(anchor), with both endpoints excluded from fitting. Primary target is published-score change; evaluate NRS1/NRS2 changes separately as constituent-measurement consistency, not new independent validation. Also report absolute published-score prediction separately, to reproduce the historical 27.04% result without mislabeling it as an edit-effect improvement.

For each scheme/model/target, export MAE, RMSE, MSE, R², Pearson and calibration slope with 2,000 composition-cluster bootstrap intervals (seed 20260926), plus descriptive Spearman. Bootstrap complete groups with all correlated rows intact; point losses/correlations remain row-weighted, matching the historical error convention. R² uses the measured target variance and may be negative. Spearman is a point estimate, not silently assigned a Pearson interval. These intervals condition on the fitted models/splits and one observed experiment; they omit model-refitting uncertainty and cannot support biological-population inference.

For all model pairs, compute paired bootstrap relative MSE reduction, including sequence models versus composition, versus additive short-k-mers, and incremental 1-mer/2-mer/3-mer comparisons. Retain every comparator and both favorable and unfavorable differences.

## Three fixed holdout schemes, common scored cohort

1. **Original sequence holdout:** exactly the original deterministic hash split; train 3,234, score 855. Exact sequences are absent from training, but composition and close variants are shared. This supplies the historical reference. No misleading random-edge split is added: sharing an endpoint between training and testing would not be a clean edit holdout.
2. **Whole-composition-group holdout:** for each of the 70 scored composition classes, remove every member of that class from the original training pool. Score only its original test members. The other original test sequences never enter training. Training count is 3,089–3,231. Composition overlap is zero; neighbors differing by one base can still cross the boundary. Composition is a mathematical sequence group, not a biological family.
3. **Purged composition-group holdout — primary:** additionally remove all original training sequences whose nucleotide-count vector is within L1 distance <=4 of the held composition vector. With the exhaustive six-mer class, this removes every sequence within two substitutions of **any** class member. A single Levenshtein operation changes count-vector L1 distance by at most two, so the retained L1 distance >4 also guarantees global Levenshtein distance >=3. Score the same original test members. There are 70 fits with 578–2,827 training sequences; the predefined minimum is 200. No split may be relaxed after seeing results.

Record training/scored-test counts, excluded class size, group overlap, exact overlap, minimum Hamming distance and mask hashes for every fit. Independently verify the distance bound and endpoint exclusion. The full ACGT^6 graph connected by one-base changes has **one connected component**; demanding disjoint whole connected components would leave no train/test evaluation. Purging defines a finite separation radius, not a claim of no shared motifs at all.

**Unseen biological parent/context and biological-family holdout are unavailable**, not failed numeric tests or zero-valued scores. The figure must show this explicitly. The stricter sequence schemes do not substitute for that missing level. Changes across schemes reflect both group coverage and reduced training size; they do not isolate a causal effect of one source of leakage.

## Models, fitting and controls

Use existing alpha=10 Ridge with StandardScaler fit only on training rows. No hyperparameter or seed search. Train on published scores only; do not calibrate to replicate targets. Primary named model is the existing positional-pair model; the existing additive 1–3-mer is a prespecified strong comparator, not a model chosen from new test results.

The original nuisance composition prediction is a training-only mean within each represented composition class. Preserve that exactly for original holdout. In a wholly unseen class, the composition prediction is a prespecified fallback: alpha=10 standardized Ridge on A/C/G/T counts, fitted to training published scores only. It is constant within the held class. Do not impute an unseen class from its test outcomes.

All sequence-order models fit residuals from training-class means, as in the historical implementation, then add the same composition baseline at inference. Evaluate: composition; position-independent 1-mer; isolated overlapping 2-mer counts; isolated 3-mer counts; additive 1–3-mer counts; position-additive one-hot; and position-pair (position-additive plus all two-position interactions). The 1-mer block adds no information to this saturated training-composition baseline: each class's residual sums to zero and 1-mer features are constant within class. Set its residual to exactly zero as the analytic solution, preventing floating-point noise from creating artificial ranks. Report this identity plainly.

No random projection was part of the original admitted SRLE model comparison; do not add one merely because another dataset used it. No neural model search. Save all coefficients/scalers/class means and every held-out prediction. Reproduce original composition/pair/position-additive/kmer123 predictions and the 27.04% score improvement to 1e-12 before proceeding to stricter fits.

## Analysis B: direction, ranking and candidate choice

Use quantitative score differences; do not invent calibrated probabilities. For all candidate edges report strict sign accuracy and pairwise ranking accuracy; exact prediction ties receive 0.5 credit only in the explicitly labeled ranking/balanced metrics. True effect ties are excluded from binary denominators; numerical tolerance is 1e-12. The composition and 1-mer change prediction is zero, so strict directional accuracy and chance ranking must not be conflated.

For each fixed anchor roster and each requested direction, predict/rank every candidate before scoring outcomes. Use lexical candidate ties, unchanged from the original policy. Choose the largest/smallest predicted measurement. Save all candidates, published/replicate deltas, ranks, selections and actual direction outcomes. Do not add abstention or an unchanged-parent option.

Compute normalized regret, correct/wrong/tie direction fractions, best-candidate recovery, wrong-in-both-replicates, correct-in-both and replicate-opposite fractions. The choice is identical across replicate evaluation. Compare with composition, all sequence controls, and **exact uniform expected choice**, not one random seed. Uniform paired-replicate risk averages joint candidate outcomes, not the product of marginal error rates. Flat lexical choice and uniform expected regret both average to 0.5 over the two requested directions, although their separate-direction risks differ.

For decision summaries average anchors/directions within composition, then classes equally. Report each direction and both combined; paired bootstrap differences preserve matched groups. Reproduce all 9,472 historical model/replicate/direction selected identities. Also report score/delta and decision tables separately so absolute-score signal cannot stand in for intervention utility.

## Failures and figure examples fixed in advance

Analyze primary purged pair-model errors descriptively against published effect magnitude (absolute delta bins <=0.1, 0.1–0.25, 0.25–0.5, >0.5), replicate delta difference using the same bins, C count, CCC presence in either endpoint, changed-position span and replicate sign disagreement. Candidate Hamming distance is always two and biological context is always one, so their effects cannot be estimated; do not invent variation. No resulting subgroup is removed or promoted to a new headline.

Choose figure examples deterministically, separately for increase/decrease: the anchor closest to median average replicate regret; plus, among choices wrong in both replicates, the choice closest to that subset's median regret. Resolve ties lexically by parent then candidate. Show all four when available, even if they look unpersuasive; if no wrong-both example exists, say so. These are descriptive examples, not additional tests.

The centerpiece has observed/predicted held-out delta, composition/1/2/3-mer/pair comparisons, a holdout gradient with unavailable biological-context holdout marked explicitly, direction success/failure and the preselected example rows. Save PNG/SVG and all candidate CSVs.

## Interpretation and stopping

All data have been used in development or prior evaluation; this fixed extension estimates robustness on exposed data and cannot become fresh confirmation. Report whether sequence signal persists under purging and whether pair features improve over short k-mers; do not require the pair model to win. No claim of a new molecular mechanism or novelty follows automatically. Never choose the unseen-biological-context claim because that evaluation is structurally unavailable. Select the strongest qualified predictive wording only after this frozen run.

Stop after the specified fits, evaluation, diagnostics, replay verification and deliverables, irrespective of outcome. Correct execution defects transparently without changing scientific choices; preserve partial outputs. Do not open new datasets, reserved outcomes or restart provenance work.
