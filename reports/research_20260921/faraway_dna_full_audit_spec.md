# Full-file DNA provenance follow-up

AI-authored, 24 September 2026 UTC, explicitly after the first-5,000-read pilot.
The pilot yielded 351 passing eight-segment calls, 349 barcode strings, and only
two barcodes observed twice. Twelve previously admitted 8-hour genotypes were
represented. To measure support across the rest of the DNA file, apply precisely
the existing barcode and alignment filters to all remaining DNA records. Reuse
the saved pilot calls; verify that its full-file barcode inventory reproduces.
Do not change scores, thresholds, references, signs, or any localization model.

Report all read-level calls and ambiguous/conflicting barcode groups. Call a
barcode association repeat-supported only if at least three called DNA reads
support the same genotype and at least 90% of its passing genotype calls agree.
Also report less-supported associations separately, without treating their
diversity as independently verified construct diversity. Read support may include
PCR duplicates; it is not a count of independent starting DNA molecules.

Compare called genotypes only to existing metadata. Report representation of
the previously admitted 207 8-hour genotypes; do not select new outcome rows.
No numeric assay barcode IDs can be inferred from these DNA calls alone.

"Eight-segment call" means all eight regions pass declared local-alignment
filters. Coverage is aligned reference span, which can include deletions;
permitted overlap and unbounded intervening gaps mean an intact, error-free
plasmid has not been demonstrated. Barcode extraction rejects multiple qualifying
exact-flank occurrences, not every possible concatemer. These qualifications
apply equally to the original pilot's `complete` field names.

The original source scripts and pilot outputs are preserved. Hash the imported
faraway_design.py dependency and the isolated alignment extension in the new
receipt. No RNA files, new outcomes, or held-out assay measurements are admitted.
