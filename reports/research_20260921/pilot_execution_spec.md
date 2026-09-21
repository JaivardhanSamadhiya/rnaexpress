# AI-authored pilot execution specification

Operational record for code execution, not a student-authored research plan or
STS submission. Written after inspecting public paper descriptions and source
table schemas, before calculating these pilot scores. Literature-informed,
exploratory hypotheses; no claim of complete novelty or independent preregistration.

## A. Sequence order conditional on composition (SRLE-seq)

Use Table S5's full exhaustive 4096 six-mer library and NRS(log2FC), interpreted
as nuclear/cytoplasmic enrichment. Check this sign against the paper before use.
One HBB reporter context only. No original RNAddress data enter fitting.

Split by SHA-256('srle-order-20260921|' + kmer) modulo 5: bucket 0 is test;
others training. Exact nucleotide counts define 84 composition classes. Training
class means are the composition-only baseline; residual outcomes are modeled
with Ridge(alpha=10) on positional bases and all positional base-pair products.
Features are standardized using training rows only. No alpha/model selection.
Discard evaluation classes with fewer than two train or two test sequences.

Primary quantity: fraction of held-out squared residual error removed beyond
the training composition means. Secondary: paired normalized-regret improvement
when selecting high and low NRS within each eligible test composition class,
using a lexical tie break. Report score/target residual Pearson correlation.
Permutation p: 999 shuffles of test outcomes within composition, with training
and predictions fixed. Bootstrap 2000 composition classes for conditional
intervals. These intervals describe sequence-class variation, not independent
biological experiments. A promising pilot requires residual-error reduction >0.10,
positive regret improvement, and one-sided permutation p <=0.01. All failures
remain reported. No claim of unseen-parent or cross-assay validation follows.

## B. External six-mer scores in a neuronal assay (GSE183192)

Score each native 260-nt tile by the negative mean of its overlapping SRLE-seq
six-mer NRS values. The direction is fixed: reduced nuclear retention is the
hypothesized direction of improved neurite enrichment. No target fitting.
Comparators: A/G fraction (the published strongest simple rationale), A/U fraction,
and negative C fraction. Candidate cohorts are identical across comparisons.

Use only Rep1 and Rep2 UMI counts for the discovery pilot, with matched neurite
and soma samples separately in CAD/N2A and GFP/Firefly. Rep3 and Rep4 are not
opened by the pilot. Scores are mean log2((neurite UMI + 0.5)/(soma UMI + 0.5));
library-size constants do not affect within-gene rankings. Require >=10 UMIs in
each pilot fraction/replicate, finite values and exact ID agreement. Exclude
non-260 nt FASTA records before outcome analysis; one 195260-nt record was
detected during metadata inspection and will not be silently repaired.

Each gene with >=20 eligible tiles is a unit. Compute Spearman within gene and
regret at both selection directions. Average genes equally, then four contexts
equally. Report all genes and separately genes absent from the old benchmark.
Overlapping tiles and repeated contexts are NOT independent samples. Bootstrap
whole genes with all contexts retained (2000 replicates).

An external-transfer pilot is promising only with mean regret advantage over
A/G >=0.01, at least 3/4 positive contexts, and a gene-bootstrap lower 95% bound
above zero. Full confirmation additionally needs adequate independent genes and
stronger controls. Never promote a favorable individual gene/context after the
fact. Rep3/4 remain closed if the pilot fails; no alternate sign or window search.

## Shared operational requirements

Record source/code/spec hashes and Git commit before scoring. Unit-test synthetic
known sequence-order effects, composition-only effects, deterministic partitions,
namespace write guards, and the replicate holdout exclusion. Record predictions,
all metrics, exclusions, failures, library versions and exact commands. No old
pipeline is re-scored. No protected datasets, spending or remote code execution.

These pilots assess feasibility for new scientific work, not the original frozen
universal RNAddress gates. Student review and interpretation are required.
