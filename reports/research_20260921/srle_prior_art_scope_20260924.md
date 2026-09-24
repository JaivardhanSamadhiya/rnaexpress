# SRLE admitted-paper prior-art scope, 24 September 2026

AI-authored documentation of the already-admitted paper, not submission prose or
a claim of established novelty. This review used the cached article XML and its
receipt only: no broad search, new source discovery, outcome-table access,
experiments or sequence recommendations.

Source: *High-throughput Screening of Sequence Elements Associated with RNA
Localization*, DOI [10.34133/csbj.0107](https://doi.org/10.34133/csbj.0107),
[PMID 42179915](https://pubmed.ncbi.nlm.nih.gov/42179915/), PMCID PMC13191086.
Cached XML SHA-256:
`12401286a3de1fa15a2910aaea8806a97ce993521ff09b7c772f4121c67ecb3c`.

**What the paper explicitly provides.** The synthetic HBB screen measures all
4,096 six-mers using nuclear/cytoplasmic counts. Figure 3F and Results section
`sec15` report GC enrichment among nuclear-associated motifs and AT enrichment
among cytoplasmic-associated motifs. Figures 3G-J validate selected insertions
in reporters with and without introns. Those are motif and reporter-context
controls, not an explicit comparison conditional on identical A/C/G/T counts.
[Screening results and Figure 3](https://pmc.ncbi.nlm.nih.gov/articles/PMC13191086/#sec15).

Methods `sec9` and Results `sec16` compare an NRS-guided transcript classifier
with randomized NRS assignments having the same score distribution, and with a
baseline containing six-mer information. They evaluate classification accuracy,
ROC and precision-recall performance. Randomizing scores controls their assignment
to motifs; it does not by itself isolate nucleotide order from base composition.
[Prediction methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC13191086/#sec9),
[Figure 4 analysis](https://pmc.ncbi.nlm.nih.gov/articles/PMC13191086/#sec16).

**What was not located in the inspected text.** No explicit exact-composition
stratification, composition-preserving swap decision set, held-out parent/candidate
selection-regret benchmark, or pairwise-versus-short-motif decision comparison was
found in the cached main article and included figure captions. This is a bounded
negative finding about the inspected text, not proof that these analyses are
absent from every supplement, code version, other publication or prior field work.
No novelty conclusion follows solely from their absence here.

**Difference from the saved reanalysis.** The project defines admissible choices
as composition-preserving swaps among already-measured six-mers and evaluates
fixed choices using normalized regret, with composition-class grouping and
short-motif baselines. The raw reconstruction checks consistency of the same
experiment's constituent data. It supplies no new biological measurements: the
exhaustive published library already contains the alternatives being compared.
Similarly, existing alternative-construct measurements are not a newly performed
parent-to-edited-transcript intervention experiment.

The reanalysis supports an assay-specific decision-benchmark result. It does not
establish that positional interactions outperform ordinary short-motif counts,
that the counting reconstruction is independent biological replication, or that
the method controls endogenous transcripts or new biological contexts. The prior
paper already screens and validates localization motifs and uses their measured
scores in prediction; those broad contributions cannot be claimed as new here.

Potential distinction for later verification: the particular exact-composition
decision question and evaluation package. Describe it as a candidate contribution
until a properly scoped prior-art comparison and compatible independent validation
support a stronger claim. The current note does not reopen any failed test or
authorize any new dataset access.
