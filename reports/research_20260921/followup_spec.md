# AI-authored post-pilot robustness specification

Written after seeing both pilot results. These analyses are post hoc robustness,
not independent confirmation or a student-authored STS research plan.

Keep the original six-mer split, training composition means, eligible test
classes, standardized Ridge alpha=10 and random seed 20260921. Compare positional
additive features (24), overlapping 1–3-mer counts (84), and the original
positional pair model (264). All models predict training composition residuals.
Report every model's error reduction and selection regret against composition,
and pair-model error differences versus each stronger baseline. Bootstrap the
same 70 composition classes 2000 times; intervals are conditional, not biological.
No hyperparameter search, alternate split, or significance-based model selection.

Also evaluate a concrete edit task: for each held-out six-mer, enumerate distinct
single swaps of two unequal bases, retaining only held-out variants in eligible
classes. Require at least two candidate variants. Select the highest predicted
NRS variant for each model (lexical ties); compare measured improvement over the
unedited sequence and normalized regret versus uniform candidate selection.
Report downward selection symmetrically. Aggregate parents within composition
before bootstrapping composition classes because neighborhoods overlap.
These are measured sequences in one public reporter experiment, not new
experimental validation or proof of a biological mechanism.

Before raw analysis, acquire only SRLE six-mer Cyto/Nuc samples 1 and 2 (eight
FASTQ files, approximately 0.85 GB total), with archive MD5 verification and
local SHA-256 receipts. Sample 3 metadata show >10 GB per pair and match sizes
of MALAT1 sample 3; defer until sample identity is resolved. Do not silently
pool these files. Inspect source primer documentation and read structure before
fixing a count rule; this is technical QC, not outcome-driven model tuning.

The published aggregate table already incorporates biological replicates, so
reconstruction of them can assess consistency but is not untouched validation.
Arora Rep3/4 remain closed after the transfer pilot failure.
