# Review of processed-file correspondence, 24 September 2026

AI-authored read-only review of `faraway_processed_correspondence.py`, its test,
specification and saved output JSON. No source outcome tables were opened, no
experiment or download ran, and no existing code or frozen record was changed.

**No observed outcome-whitelist violation or comparison arithmetic bug.** The
native TSV reader checks the exact barcode-ID/replicate/time key before converting
localization values. For admitted keys it checks genotype identity, rejects a
later condition in timed mode, rejects duplicates, requires positive finite
values, and validates the supplied ratio. Missing admitted keys fail closed.
Other rows contribute metadata only. The test checks that nonnumeric sentinels
in an excluded later condition and an excluded same-time barcode are not converted.

The saved result reports agreement within 1e-10 for all 1,104 development rows
and all 726 eight-hour rows, with maximum absolute log2-ratio differences around
1.31e-14. Metadata keys and genotype labels agree across the 32,310-row first
experiment and 16,077-row time-course representations. This review checks the
implementation and recorded summary, not an independent rerun of those values.

Two concrete limitations should accompany the result:

1. **Only derived localization ratios are compared between formats.** Both sides
   independently check their ratio against their own nucleus/cytoplasm values,
   but the implementation does not compare individual nucleus or cytoplasm CPMs
   across files. A common multiplicative rescaling would preserve the tested
   ratio. Say that localization ratios and metadata correspond; do not claim
   complete numeric-cell or raw-count equivalence.
2. **Standalone eight-hour access needs stronger provenance binding.** `run()`
   verifies the original experiment freeze, but regenerates the eight-hour scope
   through `target_metadata()` rather than verifying the secondary freeze and
   using its frozen target-row manifest. An independent successful verification
   of that secondary freeze can support the completed run. A future standalone
   runner should verify the secondary metadata/row-manifest hashes before access.
   This is a defense gap, not evidence that extra rows were opened here.

The native time-course TSV also labels the later condition `16 hr`; therefore
the discrepancy with the author code/archive metadata is shared by both processed
representations, not unique to the workbook. Later-condition values remain closed.

Agreement between two official formats may reflect a shared upstream export.
It is useful file correspondence, not independent measurement validation, a
resolution of DNA-barcode-to-numeric-ID mapping, or proof against persistent
barcode effects. The saved output correctly leaves the DNA mapping unresolved.

The single test covers the central no-conversion boundary. It does not exercise
the explicit changed-genotype, duplicate-key, missing-key, inconsistent-ratio or
mistakenly admitted later-condition failure branches; these are code-reviewed
here, not newly executed. No expansion of testing or data access is required to
retain the bounded existing correspondence claim.
