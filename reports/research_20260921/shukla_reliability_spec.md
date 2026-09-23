# Repeatability diagnostic after external pilot failure

AI-authored technical specification, 23 September 2026 UTC. The frozen external
pilot failed: source kmer regret 0.5693 versus composition 0.5183, CCC 0.4830 and
random 0.5. Eleven eligible families also fall short of the prespecified twelve.
Those findings motivate this separate diagnostic; the failed gate is unchanged.

Use only the 205 previously eligible fragments and the already-open biological
replicates 1-3. Never parse replicates 4-6 or additional target rows. No model
fitting, parameter search, sequence-QC changes or selection of favorable subsets.

Within each of the twelve eligible gene sets, use each replicate's measured
log2 nuclear/total abundance as a predictor for each other replicate. Report
all six ordered replicate pairs. Calculate Spearman rank correlation and the
same exact-tie-averaged, two-direction normalized regret as the original pilot.
Average replicate pairs, genes within family, then families equally. Compute
paired family percentile intervals with 5,000 draws and seed 20260923 for
regret improvement over random (0.5) and over the frozen source-kmer predictions.

This describes measured endpoint repeatability. It is not a formal noise ceiling,
not a deployable sequence model, and cannot authorize the closed confirmation.
No mechanistic novelty is claimed. Freeze/commit this code and specification
before calculating the diagnostic values.
