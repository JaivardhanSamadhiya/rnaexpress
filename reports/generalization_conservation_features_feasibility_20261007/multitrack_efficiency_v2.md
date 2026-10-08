# Additive v2: bounded two-track native annotation extraction

This note preserves the v1 plan, 6,006 single-track request roster, and its 23-file preparation receipt unchanged. It proposes a separately frozen, source-checked extraction in `generalization_conservation_native_20261007`; it does not authorize annotation values, aligned bases, feature matrices or supervised fitting.

## Released-source evidence

The official `v495_branch.2` tag resolves to commit `0cfec61f9e66a6db055131a0dc99ef4524783bd6`. The six public source/metadata responses in `artifacts/generalization_conservation_features_feasibility_20261007/kent_source` have immutable URL/status/body-SHA receipts. The source was inspected, not installed, compiled or executed. A release tag and source semantics do not establish the version of the running UCSC API binary.

The released [getData.c](https://raw.githubusercontent.com/ucscGenomeBrowser/kent/0cfec61f9e66a6db055131a0dc99ef4524783bd6/src/hg/hubApi/getData.c) splits a comma-separated native `track` argument and emits each wig array under its track name. Each iteration emits another `dataTime`, `dataTimeStamp`, `trackType`, `track`, `chrom`, `start` and `end` group. Ordinary JSON dictionary decoding loses earlier repeated metadata: the new parser preserves ordered object pairs and binds exactly two complete metadata groups to their corresponding named arrays. It rejects reordering, ambiguous duplicates, unknown schema, overlap, truncation and missing groups.

The released [list.c](https://raw.githubusercontent.com/ucscGenomeBrowser/kent/0cfec61f9e66a6db055131a0dc99ef4524783bd6/src/hg/hubApi/list.c) constructs split physical tables as `chromosome_rootName`. Logical `/list/schema` can instead choose a default chromosome. Therefore logical-track timestamps must not certify every chromosome. The new fixed schema roster comprises two logical schemas and the exact `chrN_phyloP60wayAll` / `chrN_phastCons60way` schemas for the 20 chromosomes already present in the certified site roster. Missing physical schema makes that chromosome's fixed intervals unavailable; there is no alias, different assembly, fallback table or replacement request.

## Bounded efficiency change

The unchanged 15,132 exact sites form 3,003 adjacent-site intervals, each at most 320 bases. A fixed `track=phyloP60wayAll,phastCons60way` request per interval halves the proposed value-call count from 6,006 to at most 3,003. The new 42 schema calls precede a separate observed-metadata value freeze. At 1.05 seconds before each new request, value-call spacing alone is 52.55 minutes; network latency, parsing and missingness checks add time. No performance outcome influenced interval merging or source choice.

The API recommends at most roughly one request per second; the exact public API and data are available without account or payment. The source repository's default MIT license has noncommercial exceptions, including `hubApi`; this educational source inspection does not imply blanket MIT coverage for those CGI sources. See [REST API conditions](https://genome.ucsc.edu/goldenPath/help/api.html), [UCSC licensing](https://genome.ucsc.edu/license/) and the pinned [repository LICENSE](https://raw.githubusercontent.com/ucscGenomeBrowser/kent/0cfec61f9e66a6db055131a0dc99ef4524783bd6/LICENSE).

The representation remains browser/API wig scores, with original download precision unverified. UCSC explains that browser/database conservation representations can differ from full-precision downloads; this route will not relabel API values as original scores. See [UCSC data/download FAQ](https://www.genome.ucsc.edu/FAQ/FAQdownloads.html). Raw unqualified `dataTime` and integer `dataTimeStamp` are preserved as an exact source pair without inventing their timezone.

## Scope stays fixed

Every original row and full parent menu remains present. Annotation availability is complete for the entire dataset-plus-exact-parent group across all candidates and both CAD/Neuro2a menus; one missing required coordinate, site or track disables native covariates for that entire parent. No availability-based candidate deletion is allowed. Native annotations additionally require gene and exact genomic coordinates at deployment, so any future model is sequence plus native annotation, not an arbitrary-sequence-only predictor. Static site constraint cannot distinguish alternate bases at one site, and is not an antisymmetric mutation-effect feature. The allele-aware consensus route remains deferred: these scalar calls retrieve no aligned bases.
