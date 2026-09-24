# Bounded processed-file correspondence check

AI-authored, 24 September 2026 UTC. This verifies public-file correspondence;
it is not independent biological validation or another selection experiment.

The official E-MTAB-13329 file inventory includes the first-transfection and
transfection-timepoint TSVs. Header-only inspection shows the same fields as
Supplementary Table 3, with numeric barcode IDs but no barcode-sequence field.
Download these free official files and retain SHA-256/URL receipts.

Parse identifiers, sequence-pattern labels, replicate and time fields across
the two files for metadata correspondence. Numeric localization fields may be
parsed ONLY for the already-open original development decision rows and frozen
8-hour target rows, identified by exact barcode ID, replicate, time (8 hours
only), and genotype. Require one-to-one keys and verify genotype/count metadata.
Read corresponding nucleus/cytoplasm/ratio values from the already-admitted
workbook rows only. Report exact-string-independent floating-point differences
and any missing/extra metadata keys; do not expand the comparison to additional
rows when identifiers fail. Original training values need not be re-read.

Do not parse localization values for original confirmation, noncandidate rows,
the later time point, doxycycline, CLK or stability. This cannot establish the
missing DNA-barcode→numeric-ID relationship or validate original raw counts.
