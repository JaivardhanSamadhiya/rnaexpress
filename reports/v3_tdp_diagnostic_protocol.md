# RNAddress v3 Phase 2 TDP-43 diagnostic protocol

Status: prespecified before broad association testing. This is a post-lock
development diagnosis, not an untouched validation experiment.

## Fixed boundaries

- Preserve the 4,566 historical parent-to-mutant interventions exactly.
- Treat all TDP-43 outcomes as post-lock development data.
- Use the three frozen historical predictions without retraining for the
  four former lock genes. A separate leave-one-gene-out diagnostic may refit
  the fixed v2 model family, but it must be labeled post-lock and may not tune
  hyperparameters or support a validation claim.
- Do not inspect Astrocyte outcomes or any member/value in the Moffatt TAR.
- Do not benchmark representations or train a v3 predictive model.
- Pair sources only by explicit construct identifiers, exact sequence,
  documented construct class, or genomic coordinates. Quarantine duplicates
  and ambiguous mappings.

## Primary hypotheses and fixed analyses

### 1. Stability mediation

Primary stability quantity: the authors' source-provided
`log_ko_wt_stb_delta` from Figure 6C. The intervention quantity is mutant minus
parent, paired by exact natural oligo ID and the explicit `TDP-43 motif` versus
`Mutant motif` label.

Primary localization quantity: the historical mutant-minus-parent
`delta_localization`.

Report overall and within-gene Spearman correlation, Pearson as a descriptive
linearity check, Theil-Sen slope, and 2,000-replicate bootstrap intervals.
Within-gene estimates are primary; pooled estimates must retain gene labels.
Fit descriptive models `localization_delta ~ stability_delta`, then add fixed
gene effects and the prespecified mechanism terms. Do not call this formal
causal mediation.

### 2. Motif, CLIP occupancy, and binding context

Count the canonical DNA-equivalent motifs `GTGTG`, `TGTGT`, and `GTATG` with
overlaps allowed. Prespecified variables are parent count, mutant count,
destroyed count, remaining unedited count, edited motif identities, and motif
multiplicity. CLIP is the source-provided reporter-overlap indicator; it is not
to be converted into unsupported base-level occupancy. RBNS is the mean
500-nM R value calculated exactly as in the paper from normalized counts, with
mutant-minus-parent difference when both constructs exist.

Primary contrasts are CLIP-supported versus unsupported interventions,
single versus multiple edited motifs, presence versus absence of remaining
unedited motifs, and low versus high RBNS affinity using fixed within-source
quartiles. Report effect sizes and within-gene estimates.

### 3. Local structural accessibility

Use the authors' Figure 4F per-motif base-pair probabilities first. Compare
these with independently cached ViennaRNA ensemble unpaired probabilities at
the same motif coordinates. Independently calculated intervention features
are mean/minimum/maximum accessibility at edited motif bases and local means
at fixed radii 5, 10, and 20 nt, for parent, mutant, and mutant-minus-parent.

Primary tests relate these fixed variables to localization effect, custom
rank error, and custom-minus-forward rank advantage. Whole-sequence MFE is a
sanity covariate, not the structural hypothesis.

### 4. Outcome-free development support / OOD distance

Use the frozen SpliceBERT paired-delta cache and fixed sequence/mechanism
features. Compute nearest-development cosine distance and Euclidean distance
after development-only standardization. For each formerly locked gene,
exclude that gene and summarize median, 90th percentile, and fraction above
the development 95th-percentile leave-one-gene-out support threshold.

The fixed question is whether Fam160b2 and Lars2 are consistently farther from
development support than Diras1 and Synj2bp. If not, OOD is rejected as the
main explanation.

### 5. Frozen-model disagreement

Because historical model scores use different scales, convert each model to
within-gene percentiles before measuring disagreement. Primary disagreement is
the per-intervention standard deviation across the three model percentiles;
maximum pairwise percentile difference is a sensitivity measure.

Relate disagreement to custom absolute percentile error and identify the
disagreement of each selected top-1 edit. Abstention analyses are descriptive:
show fixed quantile summaries, but do not optimize a deployment threshold.

### 6. Extreme-effect regret and percentile compression

Reproduce the historical gate unchanged. For each gene, direction, and model,
report oracle rank, selected effect, oracle effect, regret, normalized regret,
top-3 and top-5 oracle coverage, and behavior in the highest 5%, 10%, and 20%
of measured utility. This tests whether percentile-oriented learning ranks
ordinary good edits but misses extreme magnitude.

Magnitude-aware learning is justified only if custom rank remains reasonable
while its selected-edit effect is repeatedly far from the oracle, especially
where forward LightGBM captures an extreme edit.

## Statistical safeguards

- The four former lock genes are the independent biological contexts for the
  principal transfer claim. Mutation-level p-values will not be treated as
  independent biological replication.
- Report gene-stratified effects and bootstrap intervals prominently.
- Use a fixed random seed of `20260828` and 2,000 bootstrap replicates unless
  a computation is deterministic.
- No variable or threshold will be selected because it maximizes association.
  The 5%, 10%, 20%, quartile, and 95th-percentile thresholds are fixed here.
- Missing source measurements remain missing. No row-order joins and no
  outcome-based imputation are permitted.

## Secondary exploratory variables

Secondary analyses include edit fraction, GC change, local dinucleotide
context, individual motif identity, source-reported significance classes,
gene-level endogenous RNA behavior, RBNS concentrations other than 500 nM,
and whole-sequence ViennaRNA summaries. These can generate hypotheses but
cannot outrank a failed primary explanation without explicit caveats.

## Required interpretation order

1. Determine whether stability coupling differs by gene and aligns with
   transfer success.
2. Determine whether occupied/accessibile/simple motif architecture explains
   custom advantage better than motif existence alone.
3. Test OOD and disagreement as trust signals.
4. Decompose the regret paradox and decide whether effect magnitude needs an
   explicit objective.
5. Separate evidence-supported conclusions from plausible but unproven
   interpretations in every gene profile.
