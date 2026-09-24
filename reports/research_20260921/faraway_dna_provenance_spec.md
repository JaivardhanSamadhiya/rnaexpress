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
