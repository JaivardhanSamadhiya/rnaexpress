# Prospective pandas admission scope correction

Root source review identified an overbroad prerequisite in the first loader preparation: `PASS_OLD_PINNED_VS_CURRENT_PANDAS_DEFAULT_CSV` could imply an actual bitwise cross-interpreter comparison. The exact historical Python patch and binaries are unavailable. No such comparison can honestly be certified. No project loader, biological label, array, native runtime or fit ran before this correction.

The first 18-test receipt and first readiness draft are preserved byte-for-byte:

- `synthetic_tests_receipt.json`: `e8b1477cabf00d3609c53e2808d5087ab87de30946919829cbde27f2c3d47727`.
- `readiness_manifest.json`: `5f92c8c74235cc2c8281f94b1daa9fae7d1bc0de6e7b1b012c3ee42ecb16a4cb`.

The reviewed source instead requires the narrower `PASS_PINNED_PANDAS223_CURRENT_PYTHON_AND_INVENTED_ORIGINAL_PARSER` certificate. Both package versions must be literal 2.2.3; actual original package/native-byte identity must be established, current Python/module/native origins must be pinned, and meaningful invented original-parser options/results tests must pass under the current interpreter. `old_interpreter_bitwise_parity_established` must explicitly be false. The NumPy-only bridge still does not certify pandas. Mock tests in this preparation do not certify the actual package/runtime or parser.

The original pandas parser, defaults, selected columns, physical-row skip mask and conversion call remain unchanged. Only the required provenance claim is narrowed. It does not establish historical-interpreter equality, and future parsed current-interpreter effects must still be hashed and independently replayed consistently. No scientific model, weight, cohort, split, feature, lambda, resource requirement or gate is changed.

Reviewed tests write a new `synthetic_tests_receipt_reviewed.json`. Source preparation writes a new `readiness_manifest_reviewed.json`, pins both original records as history, and points every future metadata/FIT-label admission to the reviewed readiness. Existing records are never rewritten. Actual project loading remains pending separate root review, commit and explicit admission.
