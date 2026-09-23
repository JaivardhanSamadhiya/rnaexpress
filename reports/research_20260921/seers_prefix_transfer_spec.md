# SEERS raw-prefix exploratory transfer screen

AI-authored technical specification, 23 September 2026 UTC. This is a new
exploratory screen prompted by failed external transfer gates and available
public raw data. It is not an independent biological confirmation or a novelty
claim. Preserve every historical negative and closed confirmation set.

Archive HRA008408 is explicitly open access. L6 run titles map to one biological
sample SAMC4114749, collected in 2021 and released in 2024. This predates the
revised manuscript and updated processed-data filenames. Its relation to the
revised RT protocol is unresolved. Do not equate four R numbers with four
biological replicates. Only RNA runs HRR1883393 (cytoplasm R1) and HRR1883401
(nucleus R1) may be downloaded/scored here, first 16 MiB of each mate. Prefix
checksums and HTTP ranges establish provenance but do not verify full-file MD5.

DNA genotype QC already examined HRR1883397 R1, first 16 MiB per mate. Fix
45-base inserts with at least five concordant paired Q30 insert reads and exact
flanking anchors. Restrict to exact A/C/G/T count groups with at least five
such inserts (45 groups, 241 sequences). This is fragment ranking, not a
single-mutation or endogenous intervention test. Source sequence length is six;
target length is 45, so shared six-mers are the intended predictor inputs.

Primary predictor: average the existing frozen SRLE kmer123 six-mer predictions
over all 40 overlapping windows. Use the same frozen position-pair predictions
as a secondary descriptive comparator, not a substitute primary. Baselines:
overlapping CCC count, overlapping CCTCCC count, and uniform random selection
(also the exact tie-averaged composition-only baseline within these groups).
No target fitting, regularization changes, threshold search, or sign reversal.
Larger score always predicts greater nuclear enrichment. Freeze code, source
lookup, candidate predictions, DNA QC, archive metadata and this specification;
commit before obtaining RNA outcomes.

Decode all concatenated gzip members, discard incomplete terminal FASTQ records,
require synchronized mate identifiers, exact anchors, exactly 45 A/C/G/T bases,
Q30 at every insert base in both mates and identical insert calls. Count only
frozen candidate sequences. Retain a sequence only if at least ten qualifying
read pairs occur in each RNA fraction. Retain groups with at least five remaining
candidates and nonconstant outcome. Report exclusions without replacement.

Outcome is log2((N+0.5)/(C+0.5)); omitted library-size factors are a common
additive constant and cannot affect within-group ranking or normalized regret.
Evaluate each group's mean normalized regret over maximizing and minimizing
nuclear enrichment, averaging outcomes across exact prediction ties. Equal
weight per composition group. Uniform random expected regret is 0.5. Report
all model regrets and primary advantages over random, CCC and CCTCCC; descriptive
95% percentile bootstrap intervals use 5,000 resamples of composition groups
and seed 20260923. These intervals describe sequence-group variation, not
biological replication or assay uncertainty. Also report overall Spearman as
descriptive, without a significance claim.

An exploratory signal requires at least 20 eligible groups and primary regret
improvement at least 0.05 over every baseline with all descriptive lower bounds
above zero. This screen never authorizes any sealed data or a biological claim,
regardless of result. Do not tune or enlarge RNA prefixes after seeing outcomes
within this experiment. Any follow-up requires a separately documented question.
