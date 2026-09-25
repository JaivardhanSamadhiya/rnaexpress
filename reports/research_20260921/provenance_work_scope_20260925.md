# Additive measurement-lineage and evidence audit

Written before calculating the new lineage discrepancies, after reading the
existing findings. Post hoc provenance audit; no model, split, gate, candidate
choice, normalization choice or performance threshold will be tuned.

Read only the admitted SRLE Table 5 member from the pinned supplement; original
SRLE prediction/split records; saved 4,096-by-four count matrix; saved replicate
scores/QC; official run metadata and raw-file receipts. Recover physical workbook
rows and exact sequence identity. Preserve U-to-T normalization exactly as in the
old loader, and check all 4,096 published values against both saved benchmark
tables. Recompute only the already-fixed half-count, separately depth-normalized
replicate scores from the saved counts. Compare those arithmetic values against
the archived scores (exact computation check), and separately report their
differences from the published aggregate (different quantities, no equality
claim). Do not search pooling, strand, pseudocount or normalization alternatives.

Export one row per six-mer and original library, carrying raw counts, fixed
replicate score, workbook row, published value, explicit statuses and gaps.
Unknown construct-specific IDs, third-replicate count source and the original
published normalization/export must remain empty or UNRESOLVED, not inferred.
Record replica pairs and identifiers as archived labels, not verified biology.

Inspect only source-code text and history from the already-admitted official
SRLE repository to look for the missing production step. Cache public free
responses inside this project, verify Git blob IDs, and execute no downloaded
code. Do not load its prediction-data CSVs or serialized models.

Acceptance rubric: PASS requires the authoritative complete sample/count/statistic/
export route with reproducible Table 5 values. PARTIAL means exact benchmark-table
mapping and internal count arithmetic are verified, but the source production
route remains unknown. FAIL means benchmark identity or required arithmetic is
inconsistent. Numerical tolerance for saved floating-point arithmetic is 1e-12;
this is a computational equality check, not a biological performance gate.

Review existing dataset exposure only. New-dataset discovery remains blocked by
the prior automatic review; do not claim a global search was completed. No target
evaluation protocol or scoring is justified without an admitted independent
resource. Reuse existing anonymous replay packages in fresh isolated directories
for verification, without new modeling or new outcome-dependent diagnostics.

Create a machine-readable all-claims ledger and source/exposure inventory. Keep
unsupported mechanism and universal-transfer claims distinct from bounded
positives and unresolved provenance. Preserve all existing artifacts, failures,
user edits and sealed outcomes. Use bundled Python and additive files only.
