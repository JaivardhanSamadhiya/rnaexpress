# Unsent technical provenance questions for the SRLE study

Prepared for the student's review. No message has been sent and no author contact
is authorized by this file. These are factual questions, not an allegation that
the published data are erroneous. Source study: DOI 10.34133/csbj.0107.

Subject: Reproducing Supplement Table 5 from the public SRLE-seq six-mer reads

I am studying computational evaluation of the published six-mer landscape and
would like to reproduce Supplement Table5.xlsx, especially its NRS(log2FC) column.
The article defines NRS using nuclear/cytoplasmic CPM and describes DESeq2 across
three biological replicates. Could you point me to the exact processing record
or public code version used for that table?

The specific details that would resolve our remaining ambiguities are:

1. The accession-to-sample manifest for all three six-mer nuclear and cytoplasmic
   replicates, distinguished from the MALAT1-fragment library, and any corrected
   archive assignments or preferred read files.
2. The exact count matrix and code producing Table 5, including whether NRS(log2FC)
   is an average of per-replicate log ratios, a ratio of combined/mean normalized
   abundances, a DESeq2 coefficient, or another explicitly defined quantity.
3. The normalization, pseudocount, filtering and contrast settings, plus the
   library/reference orientation used for the reported six-mer identifiers.
4. The read-processing command/version: whether mates are merged, counted once
   per fragment, or counted separately, and how trimming, exact flanks and quality
   rules enter the count matrix.
5. Whether the public kmer_location_analysis.py in the archived repository tree
   a65b8d3d26258647d41611cf1656c08ea34e9196 was part of the publication workflow,
   or whether another historical implementation produced the workbook. Our
   inspected blob is 95b65ba603a7712f7d4d3e92e6e6e9fc2bb5ccbf.

Pointers to existing public files or a correction of our interpretation would be
very helpful. We are keeping our reconstruction separate from your published
results and are not treating a code/documentation discrepancy as proof that the
published measurements are incorrect.

## Why these questions matter

The current reconstruction checks the first two constituent replicates, not an
independent experiment. Additional files should not be treated as validation
until their identity and relationship to the published training aggregate are
clear. The exact table-production chain is needed to judge that dependence.
These questions request computational provenance only, with no new wet-lab work
or purchase. A response would not itself authorize opening protected outcomes;
admission and any subsequent analysis would still need a separate fixed scope.
