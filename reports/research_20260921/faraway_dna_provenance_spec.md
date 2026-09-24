# DNA-only construct provenance audit

AI-authored, 24 September 2026 UTC. This is a measurement/provenance audit,
not a new localization test or a change to a prior result.

Admit only official ENA run ERR12019311, identified by E-MTAB-13330 SDRF as
plasmid_sequencing, material DNA, synthetic source. Official ENA metadata states
341,076,082 compressed bytes, MD5 591291d31db03888856f11dbfb6d0981,
231,531 reads and 382,186,856 bases. Download this free public file into the
research namespace. Verify total size, archive MD5, SHA-256 and full gzip/FASTQ
integrity. Preserve metadata and download receipts. Do not retrieve ERR12019312
(RNA), fractionation RNA files or any new localization values.

The published processed file plasmid_barcodes.txt contains sequences only,
not barcode→genotype→numeric-table-ID mappings. The author scripts assign
numeric barcode IDs based on RNA barcode occurrence ordering within each assay;
those IDs are not directly the DNA barcode-list row numbers. Reconstructing DNA
identities alone therefore cannot prove the processed table IDs or ratios correct.

Assess whether raw DNA can independently recover barcodes and known design
identities from the already-public ordered-fragment references. Report ambiguous
or incomplete records as such. This audit may diagnose data limitations; it
cannot establish a biological mechanism, clean barcode independence or new
generalization. No outcome-based thresholds or model changes are permitted.

All existing confirmation and other-assay outcome restrictions remain in force.

The initial feasibility calculation uses exact matches to the two published
20-nt barcode flanks, a 17–23-nt barcode with every base at Q10 or higher, and a
single unambiguous occurrence in either read orientation. Inventory all verified
DNA reads, but attempt full construct classification only on the first 5,000
FASTQ records. This is a fixed scope, not the first 5,000 successful records.

Locate each of eight fragment regions with position-specific 15-mers, requiring
at least eight matches; pad the anchored region by 50 nt on each side and reject
windows over 1,200 nt. Align all four existing publisher fragment alternatives
with local alignment (match +2, mismatch -3, gap open -5, extension -1). Accept
the highest score only if its margin is at least 20, at least 95% of its reference
is aligned, score per reference base is at least 1.3, and fragment intervals are
ordered with no overlap greater than 20 nt. Reject if any of eight positions
fails. These conservative feasibility thresholds are not estimates of mapping
accuracy. Report all rejection categories. Reference recovery tests are software
checks, not independent real-read validation.

Biopython 1.88 is installed from a SHA-256-verified PyPI Windows wheel in a new
isolated research runtime. Its license is Biopython's open-source license; no
paid service is used. Existing frozen analysis runtimes remain unchanged.
