# SRLE provenance questions — concise unsent revision

Additive to the 24 September question list. Prepared for review; **not sent**.
No contact is authorized by this document. These are requests for provenance,
not allegations about the published data.

Subject: Reproducing SRLE Supplement Table5.xlsx from public six-mer reads

We can map all 4,096 NRS(log2FC) values exactly into our computational benchmark,
but would like to reproduce their original measurement-processing chain. Could
you provide pointers to these records for DOI 10.34133/csbj.0107?

1. **Samples and replicates:** the six-mer nuclear/cytoplasmic accession manifest,
   including how HRR3059162/65 relate to MALAT1-labeled HRR3059175/76. Their inspected
   read prefixes match; were they pooled and demultiplexed, and which files/rules
   recover the intended replicate-3 libraries?
2. **Counts and read processing:** the exact three-replicate input count matrix,
   publication code version/commands, flank/orientation rules, quality filters,
   and whether mates were merged, counted once per fragment or separately.
3. **Score and statistical definitions:** is Table5 NRS(log2FC) a mean of replicate
   log ratios, a ratio of pooled/mean normalized abundances, a DESeq2 coefficient,
   or another quantity? What sample-depth/size-factor, zero-count, filtering and
   contrast settings were used? How do FoldChange, BaseMean and pvalue relate?
4. **Export provenance:** the script/notebook and intermediate table that wrote
   Supplement Table5.xlsx, including sequence orientation and any construct-ID map.
   Was current `kmer_location_analysis.py` blob
   `95b65ba603a7712f7d4d3e92e6e6e9fc2bb5ccbf`, historical
   `library_location_analysis.py` blob `be84cb6c8d84b893674d3cc037917c7ba5b7c02d`,
   or a different implementation used?

Our two-replicate fixed-normalization diagnostic is deliberately separate from
the published aggregate. Code/documentation differences do not establish that
the published table is incorrect. A link to an existing authoritative workflow
would be sufficient; no new wet-lab work is requested.
