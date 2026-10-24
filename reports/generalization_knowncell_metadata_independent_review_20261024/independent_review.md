# Independent source-only metadata-verifier review

No concrete source blocker identified. The reviewer did not author this helper.
All 16 pins in manifest
`1909f90290c0f83d350ee0cf9bdae8af528e16eb1855fa06e5a39237bd4aad23`
match current bytes, and ten pinned Python files parse. The current source
hashes and 28 test definitions match preserved receipt
`161e43fc8384fe8c0a38e90f979d645eeaeab5d2f36b0a092335f06e2bb90339`.
Tests were not rerun by this reviewer.

The source parser uses an independent standard-library DictReader rather than
the acquisition parser. It requires a unique complete header, exact record
widths, one physical record per row, all 26,258 nonempty unique original IDs,
full original ID order and exact selected source positions. It retains only
the ten Mikl metadata fields and converts only bounded inherited-fold tokens.
Unused effects are CSV strings and are never converted to numerical labels.
The exact twelve-field parsed metadata structure is compared with acquisition
JSON, then the helper separately rebuilds every original menu, paired and
unmatched contexts, all three outer and six inner masks, and complete row/OOF
coverage. Gene, component or original-allele contradictions stop rather than
introducing a new purge, cohort repair or favorable intersection. The original
row-ID and metadata digest conventions match the frozen source definitions.

Canonical JSON handles the original contract's tuple/list representation
without changing serialized scientific values. All supplied rows remain in
the cohort. The helper imports no existing parser or contract builder and
performs no path, Git, resource or scientific-runtime operation. It consumes
but does not close its caller's CORE text stream.

The supplied-CORE API proves copying/derivation relative to its supplied stream;
it does not prove that the stream came from the exact original raw file. The
separate owned caller must bind the raw CORE SHA, committed acquisition bytes,
source/approval/owner evidence and resource checks. Author biological lineage
remains explicitly unverified. Preparation and invented tests are not an actual
full-size metadata PASS, an array/label/FIT admission or a generalization result.
No actual bundle, CORE, worker output, array, label or checkpoint was read in
this review, and no test, native probe or worker was executed. This report is
outside the unchanged 16-pin helper manifest.
