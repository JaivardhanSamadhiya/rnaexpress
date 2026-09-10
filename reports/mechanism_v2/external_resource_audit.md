# Mechanism-v2 external resource audit

Status: resources under validation; no external outcome admitted to a fitted
Mechanism-v2 predictor yet. Reviewed 9 September 2026.

## Independent stability candidate

[Su, Wang et al., eLife 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC11835390/)
report 6,555 designed pairs of 155-nt UTR reference/mutant fragments and time-course
RNA-decay assays in HEK293T and SH-SY5Y. The experiment transfects in-vitro-
transcribed RNA rather than DNA reporters, a relevant distinction for potential
nuclear splicing artifacts. Data are deposited as GSE217518; the
[author repository](https://github.com/chienlinglin/modeling-UTR-variants-stability)
is pinned at `30b9983b77a5673a090316d0068a28ec1c0ef510`.
Designed-pair count is not an analysis-eligible count. Admission requires sequence
mapping, paired alleles, assay semantics, QC, availability/license checks, and
gene/sequence separation from every localization development input. Only external
outcomes may fit this predictor. SH-SY5Y is not a validated mouse neurite context.

## Processing/splicing confound

[Dao et al., Nature Communications, 25 July 2025](https://doi.org/10.1038/s41467-025-62000-9)
show that U-rich elements can activate cryptic reporter splicing and distort
3′UTR MPRA expression measurements. This motivates checking reporter architecture
and testing nuisance features. It does not prove that the RNAddress localization
assays have the same artifact. Local sequence motifs cannot substitute for a
validated full-reporter splice model; neither U content nor a motif match alone
is evidence of a causal localization mechanism. Any risk treatment must be
selected without outer/holdout labels, with unfiltered results retained.

## Structure

[ViennaRNA Python API](https://viennarna.readthedocs.io/en/latest/api_python.html)
supports MFE and ensemble calculations. Version 2.7.2 is installed in an isolated
new runtime. Proposed features are paired ref/mut deltas under fixed folding
settings and local coordinate windows; they are equilibrium in-silico priors,
not measurements of intracellular structure. Window settings, normalization and
cache identities must be fixed before the localization model comparison.

## Remaining admission checks

Fresh BRIDGE/motif/trans-context audits, full stability data retrieval and Parnet
resolution remain underway. No branch is filled with zeros simply because an
external resource is missing. The final admitted feature manifest does not yet
exist, and there is no final evaluation freeze.
