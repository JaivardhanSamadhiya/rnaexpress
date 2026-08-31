# RNAddress v4 Phase A final verdict

## Decision

**GO — STRONG DEVELOPMENT FOUNDATION.**

Phase A reconstructed a provenance-complete, leakage-grouped development foundation with 62,758 certified interventions, 248 case-folded gene labels, 10,406 independent parent contexts, 93,397 finite long-form assay outcomes, seven physical intervention classes, and explicit uncertainty/missingness semantics. The conclusion is driven by independent biological contexts and exact construct mapping, not raw row count.

The strength is asymmetric by edit budget. Development evidence is strong for small, motif, regional, and large interventions and for shortlist selection. Exact-SNV supervision remains sparse at 19 interventions. Therefore the authorized v4 claim remains a mechanism-aware, minimum-budget RNA-localization intervention ranking framework—not a universal exact-SNV compiler.

No v4 model was trained, tuned, ranked, or selected in Phase A. N-zip outcomes were not used. Historical models were not rerun. Astrocyte outcomes remained untouched.

## Required return

1. **Phase A decision:** **GO — STRONG DEVELOPMENT FOUNDATION**, with mandatory assay-specific heads, direction-aware evaluation, parent-grouped splits, and no exact-SNV competence claim before prospective testing.

2. **Certified Mikl intervention-pair count:** **11,900** exact-sequence, semantically validated parent-mutant pairs.

3. **Certified Mikl gene count:** **224**.

4. **Certified Mikl independent parent-context count:** **5,830** exact parent contexts. The group key binds source gene, 3′UTR position, and exact 150-nt parent sequence.

5. **Mikl replicate/uncertainty status:** Three paired biological soma/neurite replicates are available in each of CAD and Neuro-2a. Every certified pair has a finite standard error derived from the three raw-count mutant-minus-parent replicate deltas with pseudocount 0.5. The three deltas are retained explicitly. The author-processed point effect and reconstructed raw uncertainty remain distinct.

6. **Mikl increase/decrease effect balance:** CAD has **4,555 increases, 7,308 decreases, and 37 exact zeros**. Neuro-2a has **4,443 increases, 7,428 decreases, and 29 exact zeros**. Both directions are learnable in scale, but disruption/decrease is the majority.

7. **Certified TDP pair/gene count:** **4,566 pairs across 16 genes**, with 4,566 exact parent contexts. TDP has 1,899 increases and 2,667 decreases. Four biological replicates exist in EV3, but pair-level processed Figure 4E uncertainty is explicitly unavailable. TDP is post-lock development data, not validation.

8. **Moffatt parent-element count:** **10 biological labels/contexts and eight unique exact parent sequences**. `cdc42`/`cdc42bpg` and `trp53`/`trp53inp2` are exact-sequence pairs and require sequence-equivalence sensitivity grouping.

9. **Moffatt intervention count:** **46,292** certified interventions from 47,955 source outcome rows.

10. **Moffatt intervention classes:** 9,462 sufficiency background replacements; 3,328 necessity deletions with inactive padding; 14,235 random substitutions; 10,539 regional shuffles; and 8,728 SHAPE structure perturbations.

11. **Moffatt replicate structure:** Exactly five assay families × two reporters × two compartments × four biological replicates = **80 processed samples**. No sample has duplicate oligo keys. Raw paired-ratio diagnostics with at least two replicates exist for 46,186 GFP and 44,535 Firefly interventions. Finite author outcomes exist for 44,248 GFP and 20,783 Firefly interventions. Raw-ratio uncertainty is diagnostic, not uncertainty on the WT-normalized author effect.

12. **Whether Moffatt was successfully converted to development data:** **Yes.** The outcome-blind protocol was committed first; the sealed archive then matched its frozen SHA-256; the irreversible development unseal was logged and committed; and only afterward were the 80 predeclared files opened. Moffatt is permanently development data and cannot be reused as independent validation.

13. **Total unique genes across development:** **248 case-folded source gene labels**. This is a transparent label union, not an assertion that duplicated aliases or sequence-identical labels are biologically independent.

14. **Total independent parent contexts:** **10,406** under the primary biological-parent keys: 5,830 Mikl + 4,566 TDP + 10 Moffatt. Exact-sequence-equivalence and gene-held-out analyses are required sensitivities.

15. **Exact-SNV development count:** **19**: 13 Mikl and six Moffatt. The six Moffatt SNVs come from one parent context. This is insufficient for a universal exact-SNV claim.

16. **Small-edit development count:** **15,993** interventions with operation-aware cost 2–5.

17. **Motif-edit development count:** **14,719** interventions with operation-aware cost 6–12.

18. **Large-edit development count:** **14,386** interventions with cost at least 100. An additional **17,641 regional edits** have cost 13–99. Continuous cost remains primary; tiers are descriptive.

19. **Cross-assay pooling recommendation:** Do **not** pool numerical outcomes into one target. Share sequence and edit representations, then retain cell-line, reporter, assay-family, normalization, and uncertainty semantics in separate heads. Any later cross-assay utility requires development-only calibration and ablation.

20. **Whether shared representation plus assay-specific heads is justified:** **Yes.** Exact parent/intervention sequences and edit operations are structurally shared, while effect scales and directions differ. The minimum defensible heads are Mikl CAD, Mikl Neuro-2a, TDP CAD, and Moffatt family × reporter. Arora's 7,360 forward 260-nt constructs can support auxiliary representation heads only.

21. **Whether increase and decrease should be modeled separately:** **Yes at the task/output level.** Use a sign classifier plus direction-conditional magnitude, or separate increase/decrease utilities within each assay head. A symmetric absolute-effect loss is not sufficient. Separate physical models are optional; separate direction objectives and metrics are mandatory.

22. **Whether minimum-edit-budget modeling is empirically supported:** **Yes for small through large budgets.** There are tens of thousands of interventions across cost strata and complementary candidate-set structures. Exact-SNV-only budget modeling is not yet empirically supported. Future optimization must use continuous operation-aware cost and compare realized effect/cost regret within held-out parents.

23. **Whether decision-focused learning remains feasible and novel:** **Yes, plausibly.** Candidate sets, costs, effects, direction, and grouping now exist. The literature supports predict-then-optimize, listwise ranking, best-arm/top-k identification, and calibrated selective risk. The targeted audit found no existing RNA-localization system combining exact parent-mutant operations, mechanism-aware edit cost, assay-specific heads, parent-grouped regret, and a sealed prospective benchmark. This is a defensible integration novelty claim, not a claim that the component algorithms are new.

24. **Any new integrity problem:** Four material caveats were found and contained. Moffatt has 1,658 outcome IDs absent from the sequence dictionary, 35 malformed 297-nt `N`-containing shuffle records, and five operation mismatches; none entered certification. Moffatt sufficiency code documents accidental omission of explicit WT oligos and control-based normalization. TDP pair-level uncertainty is missing and EV5 stability remains quarantined because of 10,935 duplicate sample/oligo keys. Exact-SNV development coverage is only 19. Mikl's earlier full-198-nt edit representation was biologically wrong and was replaced by the correct 150-nt test insert. None of these caveats destroys the multi-assay development gate because exclusions and semantics are explicit.

25. **Tests passed:** **55 unique tests passed**: 49 tests in the main batch excluding `test_v3_nested.py`, plus six ViennaRNA-dependent nested tests in a fresh process. The 10 new Phase A tests are included in the 49. A one-process full collection reproduces the known Windows ViennaRNA DLL initialization collision; isolated execution passes all affected tests. `git diff --check` also passes.

26. **Files created:** Required reports are `v4_phaseA_protocol.md`, `v4_mikl_source_truth_audit.md`, `v4_tdp_schema_audit.md`, `v4_moffatt_preunseal_protocol.md`, `v4_moffatt_source_truth_audit.md`, `v4_cross_assay_compatibility.md`, `v4_intervention_taxonomy.md`, `v4_decision_focused_literature_audit.md`, and this verdict. The chain-of-custody report `v4_moffatt_unseal_log.md`, reconstruction script `src/audit/reconstruct_v4_phaseA.py`, and test `tests/test_v4_phaseA_reconstruction.py` were also created. Machine artifacts under `results/v4_phaseA/` include per-source intervention tables, the common long-form outcome table, exclusion audit, edit distribution, sample manifest, pre-unseal audit, unseal log, summary, and complete source/output manifest.

27. **Git commits:** `bdbd9f1fbf30ea0094ea7bf7f029c4f828ec82ed` froze Phase A and the Moffatt pre-unseal protocol; `e5cec4985cdc841673b95f5e9b63b5662b5ffb9d` logged the Moffatt development unseal; `acfa2b432c1c5a6e45d4a3042a10406c74d24eff` committed the reconstruction code, machine truth layer, source audits, literature audit, and tests. The frozen starting point is `850d9a4df5d109d0aad587f9fdba86b465f99bbd`.

28. **Whether Astrocyte remains untouched:** **Yes.** No Astrocyte outcome file was opened, enumerated through the Phase A script, transformed, modeled, or used to define costs, architecture, thresholds, or verdict. The protected Astrocyte loader SHA-256 remains `78fd563f4e51866bc6d0e18aac9bfbbedf20ad0986e6bd087caf9b0b11901a78`.

29. **Whether the foundation justifies a new modeling phase:** **Yes.** Phase B is justified if it begins with a frozen grouped protocol, assay-specific heads, direction-aware objectives, operation-cost conditioning, nested parent/gene holdouts, and explicit uncertainty handling. It must compare simple baselines before decision-focused objectives and must not use Astrocyte for architecture selection.

30. **Whether RNAddress still has a credible path to a PV-Care-level entry:** **Yes, but it has not reached that level yet.** The credible path is now stronger than the failed N-zip path: build and preregister a leakage-safe multi-assay model on this development foundation; demonstrate held-parent shortlist regret, calibration, direction fidelity, and edit-budget efficiency; freeze the complete pipeline; and only then run the untouched in-vivo Astrocyte exact-SNV benchmark once. A positive prospective result would support the strongest claim. A negative exact-SNV result must narrow the product to the empirically supported motif-scale/minimum-budget shortlist claim rather than be optimized away.

## Stop rule

Phase A stops here. No RNAddress v4 model has been trained, and no further development action is authorized by this report.
