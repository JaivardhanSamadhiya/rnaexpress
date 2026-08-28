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

## 2026-08-27 — Phase 1 literature and public-data refresh — DIAGNOSTIC

- Searched 2024–2026 primary literature and public repositories for new RNA-localization intervention landscapes, representation models and mechanism resources.
- Discovered Moffatt et al. 2026, DOI `10.64898/2026.06.09.731215`, GEO `GSE334718`, a neuronal neurite/soma MPRA reporting tens of thousands of mutant localization elements.
- Verified from outcome-free GEO metadata that the study has 80 samples: five library families (`mutation`, `necessity`, `SHAPE`, `shuffle`, `sufficiency`) × two reporters × two fractions × four replicates.
- Downloaded `GSE334718_RAW.tar` and hashed it as an opaque byte stream: `abc6e571ed68833e3fb0c0028209303a0f468347ac5f6efbeffd788c35c7ade1` (12,697,600 bytes).
- Did not open, list, extract or parse the TAR. Did not read any processed-file header, row, UMI count or localization result.
- Frozen the resource as a candidate untouched secondary lock. Exact parent count, construct count and sequence-pair reconstruction remain unresolved, so it is not yet classified as a valid benchmark.
- Determined that it is not clearly superior to the Astrocyte lock overall: it is broader in construct scale and design families but weaker in proven exact-SNV structure, in-vivo context, protected-property endpoints and laboratory independence.
- Refreshed representation evidence for 3UTRBERT and HydraRNA and mechanism evidence for stability/m6A, RBP motifs, local structure and nuclear-retention grammar.
- Corrected the SRLE-seq DOI in the reproducible acquisition generator and manifest to `10.34133/csbj.0107`.

Classification: **DIAGNOSTIC**. No outcome-bearing development experiment and no v3 model training occurred.

Decision: **CONDITIONAL GO** to Phase 2 using only spent TDP outcomes for diagnosis. Astrocyte and Moffatt outcomes remain sealed.

## 2026-08-28 — Phase 2 TDP-43 failure diagnosis — DIAGNOSTIC

- Wrote and committed the prespecified protocol before broad association testing at commit `a38e13c`.
- Audited the complete public TDP-43 source package and validated all 4,566 historical parent/mutant sequences exactly against EV8 after deterministic removal of 20-nt handles. No historical pairing error was found.
- Quarantined raw EV5 stability reconstruction because 10,935 `sample+oligo` keys duplicate `WT_t0_1` and no `WT_t0_3` label exists. Used the exact-paired processed Figure 6C source and excluded 71 non-finite source log values without clipping or pseudocounts, leaving 3,117 finite stability intervention pairs.
- Built a 4,566-row diagnostic table with frozen predictions, localization truth, exact edits, motif architecture, reporter CLIP, source and independent motif accessibility, RBNS, stability, ranking errors, model disagreement and outcome-free support metrics.
- Ran 2,000 seed-fixed clustered bootstrap resamples and generated six publication-quality figures plus machine-readable metric tables.
- Diagnosed the strongest failure as percentile/magnitude objective mismatch combined with multi-base motif-complement versus exact-SNV task mismatch. Conditional binding/CLIP/accessibility/stability biology is important but varies by gene.
- Rejected OOD-only failure, disagreement-only abstention, motif-count-only logic, CLIP-only logic, universal stability mediation and generic global structure as sufficient v3 directions.
- Decision: **GO** to a later Phase 3, with magnitude-aware dual objectives, explicit motif-by-occupancy/binding-by-local-accessibility interactions, optional stability supervision, task separation and multi-signal uncertainty. Phase 3 was not started.
- Astrocyte outcomes were not inspected, analyzed, recorded, or used. The inherited full-worksheet programmatic load remains disclosed. The Moffatt archive was not listed, opened, extracted or used.

## 2026-08-28 — Phase 3 protocol freeze — DEVELOPMENT

- Verified the branch started cleanly at Phase 2 commit `54fa859ff48b03ddca1d9b15c1f3a46b9b0bfd79`.
- Performed outcome-free feasibility checks for contextual representations. The author-hosted 3UTRBERT 3-mer checkpoint was pinned at revision `220d80829deb077d1d640463a4267a96e9e70b1d`, hashed and loaded with finite hidden states.
- Excluded HydraRNA from the definitive benchmark because its official Linux/CUDA/Mamba/FlashAttention/custom-fairseq extraction stack is not reproducible on this Windows CPU-only host. This is not a performance result.
- Audited the N-zip supplement schema. The 4,395 exact SNVs have aggregate localization fields but no deterministically linked technical-replicate measurements; WT versus shScramble remains a cross-condition control, so no standard error or measurement weighting will be invented.
- Froze exactly two representation families, five candidate architectures, controlled mechanism interactions, nested grids, oracle and near-oracle definitions, robustness criteria, negative controls, uncertainty signals and numerical GO/CONDITIONAL GO/NO-GO rules before any new Phase 3 model comparison.
- Astrocyte outcomes were not inspected, analyzed, recorded or used. The Moffatt archive was not listed, opened, extracted or used.

### Pre-analysis Phase 3 protocol correction

Before any new representation score was computed, a cache-shape consistency check showed that the historical SpliceBERT construction appends the 590-dimensional v2 edit vector, not the 18-dimensional low-level metadata vector. The two mentions of “18-element edit vector” in the protocol were corrected to “590-element v2 edit vector.” Both SpliceBERT and 3UTRBERT therefore receive the same exact outcome-free edit block. Candidate families, targets, grids, metrics and gates were unchanged.
