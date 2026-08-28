# RNAddress v3 experiment log

All entries must be labeled **DIAGNOSTIC**, **DEVELOPMENT**, or **FROZEN VALIDATION**. TDP-43 outcomes are post-lock development data. Astrocyte outcomes remain sealed.

## 2026-08-27 — Phase 0 repository audit — DIAGNOSTIC

- Started from `rnaddress-v2-rescue` commit `99957beaafe44529296372b9c074c8bf314766df` and created branch `rnaddress-v3-mechanistic-selective`.
- Inspected git history, reports, manifests, committed frozen artifacts, source references and the inherited test suite.
- Verified the committed outcome-free Astrocyte feature artifact has 4,553 rows, eight parents and exactly 13 allowlisted columns.
- Verified raw Astrocyte workbook SHA-256 `1d17c0631fc962b762dddf3f27f76494dadf882f28a0154b5af76dbedd57c3f6` and GEO archive SHA-256 `88c883f41530b485ccacd98b276e90c8955138e64d7d02babf1a7738bee25f1f` without parsing either file.

### V3 protocol deviation discovered during the audit

The inherited `tests/test_pairing.py` called `src.pairing.audit_astrocyte.audit()`. That legacy function loaded the complete `S8_lib2_results_summary` worksheet into memory to verify element-key completeness and nonmissing outcome counts, even though it exported only outcome-free features. The full inherited test suite was run once after the v3 prompt was received, so this loader executed once during v3 Phase 0.

No Astrocyte outcome value, row, distribution, correlation, ranking or model metric was printed, inspected or used. Test output contained only the pass count. Nevertheless, loading the result worksheet violated v3's stricter requirement not to read outcome fields and is recorded rather than hidden.

Mitigation implemented immediately:

- ordinary `audit()` now verifies hashes and loads only the committed outcome-free feature CSV and historical audit JSON;
- the exact 13-column schema is an allowlist and outcome-like names fail closed;
- raw source reconstruction is moved behind `reconstruct_from_source()` and requires an explicit reveal-stage environment token;
- tests monkeypatch `pandas.read_excel` to fail if the safe audit path attempts workbook access;
- tests require raw-source reconstruction to fail closed and injected outcome columns to be rejected.

This incident cannot inform v3 model design because no values or summaries beyond already committed historical completeness counts were exposed. It does reduce the purity of the statement “the workbook was never loaded during v3,” which must not be claimed.
