# SRLE measurement-provenance review, 24 September 2026

AI-authored bounded review of cached admitted-paper text, counting/upstream source,
repository-tree metadata, pinned README/configuration text, receipts and the local
table-loader definition.
No outcome workbook, raw reads, protected data or new dataset was opened. No
downloaded code was executed and no existing artifact was changed.

**Conclusion: the published score definition is clear, but the exact route from
replicate counts to the consumed Table 5 score remains unestablished.** The
inspected public counting script is not sufficient to reproduce that route.

## Published definition and actual table used

Methods `sec7` defines NRS as log2(nuclear CPM / cytoplasmic CPM), with CPM
normalized by each sample's sequencing depth. It separately describes DESeq2
analysis of raw counts from three biological replicates for depth normalization,
dispersion, Wald testing and multiple-testing correction. Methods `sec6` also
states triplicate collection. Neither inspected passage specifies exactly how
replicate-specific quantities become the single supplied NRS value, or a
zero-count pseudocount. [SRLE analysis methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC13191086/#sec7),
[collection methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC13191086/#sec6).

The consumed source is **Supplement Table5.xlsx**, not Table S2. The local
`pilots.read_sixmers` definition loads `srle_epmc_supplement`, its nested
`csbj.0107.f1.zip`, then `Supplement Table5.xlsx`; it uses the active worksheet
and `NRS(log2FC)` column. This was established by reading code, without loading
the workbook. Article `sec15` also points to Table S5 for the six-mer results;
`sec6` identifies Table S2 as PCR-primer information.
[Local loader](D:/rnaexpress/src/research_20260921/pilots.py:28),
[published six-mer results](https://pmc.ncbi.nlm.nih.gov/articles/PMC13191086/#sec15).

## What the inspected counting script actually does

The cached `kmer_location_analysis.py` accepts one nuclear mate pair and one
cytoplasmic mate pair per invocation. It counts the two mates independently;
there is no pair-concordance, explicit reverse-complement operation, biological
replicate combination, or DESeq2 invocation in this file. Upstream trimming and
the actual flank/orientation command arguments are not recovered by this script
alone. [Cached source](D:/rnaexpress/data/external/research_20260921/srle_author_count_code:17).

Three concrete implementation observations matter:

1. Lines 108-128 form one denominator from nuclear plus cytoplasmic accepted
   counts and use it for both quantities called CPM. This differs from separate
   sample-depth normalization described in the paper.
2. At lines 140-141, both terms of `nes` use cytoplasmic CPM. With its 0.5
   pseudocount, that field is therefore zero. A separate `log2fc` field uses the
   raw-count ratio with 1e-6 pseudocount; it is not an implemented replicate-aware
   DESeq2 contrast. Output is `kmer_complexity.info.csv`, not the named workbook.
3. Length/N filtering at line 77 requires `library_complexity`, but the CLI
   choices at line 24 are `kmer_complexity` and `fragment_complexity`. The filter
   branch is unreachable through the displayed CLI.

These are observations about one authenticated public code blob. They do not
establish that the published workbook was generated using this code, that its
measurements are wrong, or that every historical implementation has these issues.

## What remains missing

An auditable Table 5 production record needs the exact sample/replicate manifest,
flank/orientation and read-counting rules, actual replicate count matrix and
normalization/contrast or aggregation code, pseudocount policy, and workbook
export step. Pooling raw counts, taking a ratio of mean CPMs, averaging log ratios,
and reporting a DESeq2 coefficient are not interchangeable definitions. The
`NRS(log2FC)` column name alone does not identify which route was used.

The cached recursive tree lists counting, splitting, diversity and model scripts,
configuration and README files, but no clearly named DESeq2/Table-5-export script.
The initial review covered the counting file; the four upstream scripts were
subsequently inspected as documented below. The downstream prediction directory
and repository history remain uninspected. Do not state that no such pipeline
exists anywhere. This review resolves neither replicate-3 identity nor
the original workbook's full generation provenance.

## Pinned README and configuration follow-up

The subsequently supplied README and configuration were read as text, without
execution or additional network access. Their SHA-256 and Git blob identifiers
were independently checked against their receipts and cached tree entries.
**They do not close the replicate-pooling or Table 5 production gap.**

README section 4, line 147, describes a QC requirement of CPM greater than one
in at least one of Total, Nuclear or Cytoplasmic compartments. Its displayed
counting command supplies only nuclear and cytoplasmic mate pairs. The inspected
counting script has neither a Total input nor that stated CPM filter. The text
could describe an upstream step, but its implementation and connection to Table 5
are not established by these files.
[Pinned README](D:/rnaexpress/data/external/research_20260921/srle_pinned_README_md_20260924:147).

At README line 185, the output description calls log2 fold change "cytoplasm vs.
nucleus". The paper's explicit NRS formula and the script's separate `log2fc`
formula use nuclear over cytoplasmic abundance. This is a documentation/score-field
ambiguity, not grounds to reverse any recorded score or select whichever sign
performs better. The README also describes its scatter axes as CPM, while the
inspected script plots raw counts. NRS/NES/NSE naming is inconsistent across the
inspected materials and does not resolve the workbook mapping.
[Output description](D:/rnaexpress/data/external/research_20260921/srle_pinned_README_md_20260924:183).

The configuration supplies software executable paths and a genome-index path;
it contains no biological-replicate manifest, aggregation rule, DESeq2 contrast
or Table 5 export settings. Listing a paired-read merging executable there does
not establish that the displayed six-mer count command invokes it.

No exact-composition swap-selection or decision-regret benchmark was found in
this bounded README review. As with the article review, absence from this text
does not prove absence from all code, supplements, repository history or prior
literature, and does not establish novelty.

## Pinned upstream-script follow-up

The four additional scripts and LICENSE were read as text only. Their byte counts,
SHA-256 values and Git blob IDs independently match their supplied receipts.
**None supplies biological-replicate pooling, DESeq2 analysis or a Table 5
workbook-export path.** Their actual roles in this snapshot are:

| Pinned file | What the inspected code supplies |
| --- | --- |
| [library_split.py](D:/rnaexpress/data/external/research_20260921/srle_pinned_library_split_py_20260924) | Primer-based demultiplexing of one mate pair into library files and a count summary. Its CLI parser is commented out and the active inputs are local hard-coded paths. It is not a replicate manifest or aggregation step. |
| [kmer_diversity_evaluation.py](D:/rnaexpress/data/external/research_20260921/srle_pinned_kmer_diversity_evaluation_py_20260924) | Single-library diversity counts/CPM and plots. It normalizes reverse-orientation matches, selects at most one extracted insert per mate pair, and filters to the requested length. These behaviors differ from the separate localization-counting script and do not establish which code produced Table 5. |
| [randomfrag_diversity_evaluation.py](D:/rnaexpress/data/external/research_20260921/srle_pinned_randomfrag_diversity_evaluation_py_20260924) | Fragment-library PEAR merging, flank extraction, genome alignment, coverage, counts/CPM and plots. This concerns fragment-library processing, not the six-mer score workbook. |
| [randomfrag_location_analysis.py](D:/rnaexpress/data/external/research_20260921/srle_pinned_randomfrag_location_analysis_py_20260924) | One nuclear/cytoplasmic fragment-file pair, PEAR merging, extraction/alignment and separate coverage/count summaries. It has no three-replicate statistical fit or workbook export. |

The pinned LICENSE is MIT; that software-use statement does not validate the
measurement chain. This review excludes the downstream prediction subdirectory,
model/data files, repository history, other snapshots and all biological outcome
files. No displayed commands or downloaded source were executed. The Table 5
production and replicate-pooling gaps remain unresolved within this precise scope.

## Source identity

Local SHA-256 hashes were checked against their existing receipts:

- Article XML: `12401286a3de1fa15a2910aaea8806a97ce993521ff09b7c772f4121c67ecb3c`.
- Counting source: `5446a47b70d741ac78b9a06f4f06a98f3bfa2dd7e12ffd03974c7ac039c4911c`.
- Repository tree: `8007a47932d41c5d756c220f1048492920778d2e0e7269c093a70163a9afde81`.
- Pinned README: `3c6db9767c9f071e2ddb1f301b29c67addeeac27e7787defbdf51ef30fdddf45`;
  Git blob `07b880eaa3805853ab16d7cf8ff43bb588f5ab4f`.
- Pinned configuration: `79b228dc0f65960de92bdfde106d8820186c8171d7a42628e04816b297d830d8`;
  Git blob `9f9295da208eea84c3e1e611846b77c3973e49c0`.

The computed counting-source Git blob ID is
`95b65ba603a7712f7d4d3e92e6e6e9fc2bb5ccbf`, matching the cached tree entry.
The tree response SHA is `a65b8d3d26258647d41611cf1656c08ea34e9196`;
it is recorded as a tree identifier, not assumed to be a commit.
[Official source repository](https://github.com/lysovosyl/SRLE-seq),
[exact counting blob](https://api.github.com/repos/lysovosyl/SRLE-seq/git/blobs/95b65ba603a7712f7d4d3e92e6e6e9fc2bb5ccbf).
