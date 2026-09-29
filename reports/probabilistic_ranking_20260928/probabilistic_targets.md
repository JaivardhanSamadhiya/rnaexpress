# Probabilistic targets and what they mean

The authoritative definitions, prior, numerical tolerance, fallbacks, optimizer and selection criteria are in `protocol.md`, committed at `1c1f387` before any comparative model result.

H0 uses the author/aggregate order. P1 records the fraction of common finite replicates favoring the first candidate, with half a vote for a numerical tie. P2 adds symmetric Beta(0.5,0.5) smoothing. P3 estimates latent-mean sign support from paired differences, with a two-degree-of-freedom shrinkage toward a training-assay pooled within-pair variance. The pool never includes held-out-assay measurements. These targets answer related but different working questions; none is a demonstrated probability of biological superiority in a future experiment.

When no paired replicate information exists, all methods use the identical aggregate H0 target and flag the fallback. When paired values exist but the training replicate subset cannot identify a variance (for example SRLE's one-replicate half), P3 falls back to P2. No variance is inferred from a model's prediction errors or a held-out measurement.

Soft labels retain disagreements instead of duplicating examples or silently filtering them away. The separately declared Partial control deliberately removes training comparisons lacking sufficient posterior directional support and reports the resulting loss of pairs/contexts. Reliability weighting has a positive 0.25 floor and retains the original biological balance after within-context renormalization.

`replicate_pairwise_evidence.csv` retains wins, losses, ties, common-replicate counts, all replicate differences, mean/sample variance, aggregate difference, P1/P2 support and provenance/fallback status. `training_targets/*.csv.gz` retains the actual target and weight for every fold/model, with P3 noise-pool parameters and heteroscedastic noise-head coefficients in the corresponding fitted JSON. P3 is deliberately not computed as one global all-assay target before fitting.

The first four models use the same coherent latent utility. The pairfree and heteroscedastic variants are secondary and cannot rescue the primary selection gate. The Hraw control checks whether any difference is explained by switching from the author aggregate to raw-replicate means. Calibration always uses held-out observed aggregate labels or empirical replicate support, never smoothed targets relabeled as ground truth.

Only numerical differences <=1e-12 are called exact ties; no cross-assay biological equivalence margin is asserted. Measurement ambiguity is also retained as a separate outcome diagnostic. It does not excuse or erase wrong recommendations.
