# RNAddress FinalShot — required final return

DRAFT — COMPUTATIONAL RELEASE INCOMPLETE

Scientific conclusion: **NO-GO — END ZERO-SHOT RNADDRESS**. This is not a claim that RNA localization cannot be engineered; it is a rejection of this tested universal zero-shot path under its own standards.

Novelty and primary-source comparisons: [fresh literature audit](finalshot_novelty_audit.md). Protocol fidelity: [integrity review](finalshot_integrity_review.md).

## Gate overview

| Gate | Status | Reason |
| --- | --- | --- |
| A | Pass numerically | Overall rank and regret thresholds met |
| B | Fail | 54.46% of units improve; requires 55% |
| C | Qualified / not certified | Recorded pass omits contradictory per-gene cap |
| D | Pass numerically | Leave-source threshold met |
| E | Fail | Cell and reporter transfer fail |
| F | Fail | Small-edit bridge and 6–10 nt harm limit fail |
| G | Fail | Identity and delta controls retain gains |
| H | Fail | Trans context adds insufficient crossed-cell benefit |
| I | Not applicable | Stability was excluded before evaluation |
| J | Fail | Two source-direction tasks exceed harm limit |
| K | Repeated-smoke/seed conditions met | Cross-run sparse-model archive equality remains limited |
| L | Not certified | Protocol/implementation discrepancies disclosed |

## 1. FinalShot verdict

NO-GO — END ZERO-SHOT RNADDRESS. Release preparation remains incomplete: Complete remaining M3 cell-context outer folds, validate archives, and summarize the control.

## 2. Exact resource-audit findings

Parnet paper-matching weights were unavailable at freeze. RBPNet was the explicitly allowed reproducible fallback. BRIDGE and DeepLocRNA were not used as predictors; no stability model passed audit. Exact versions, hashes, licenses, coverage, and exclusions are in finalshot_resource_audit.md and the resource manifests.

## 3. Was Parnet reproducibly usable?

No: the executable development checkpoint did not match the preprint architecture. This is not evidence that RBPNet is the same model.

## 4. Exact Parnet version/checkpoint/hash

No paper-matching checkpoint/version/hash is available from the frozen audit. Package 0.5.0 commit 2f0570cf47d8bb927415a71f853a97eb7e94005c; executable but excluded development artifact 0.5.0_RBPNet-11M.pt, SHA-256 2620a1c9b838fd28fcefb3c8cc695fa7a4889fb18a67c21694c097248aa64869. It has 11,736,799 parameters, not the paper-reported 21 million.

## 5. Parnet RBP count represented

Zero modeled Parnet channels. The preprint reports 150 unique human RBPs across 223 experiments. The actual fallback comprises 103 RBPNet HepG2 checkpoint groups and 927 summaries.

## 6. Localization-RBP coverage

RBPNet covers 12 of 26 prespecified localization-related human symbols. TARDBP, ELAVL, MBNL, PUM, FMR1, FXR1, and IGF2BP2 are absent. Mouse inference is cross-species, not a validated mouse binding model; see rbp_coverage.csv.

## 7. BRIDGE usability

Methodology-only; its human-cell modalities and input requirements were incompatible with this frozen dataset. No zero-filled surrogate or new representation was introduced.

## 8. External cell-context datasets

GSE67828: equal-compartment averages of soma/neurite replicate medians of log1p(FPKM), CAD and N2A; 98 mapped RBP channels. No localization intervention outcomes supplied the expression proxy.

## 9. Stability prior

None. Excluded prospectively after the resource audit.

## 10. GSE249405 contribution

Resource assessment and biological context only; no derived feature, coefficient, target, or mutant score.

## 11. Strongest geometry baseline

Frozen M0: 28 geometry/class/tier features, training-fold StandardScaler, weighted Ridge alpha=100, shared within-decision-set rank target. It is the fixed comparator, not a retrospectively chosen weak baseline.

## 12. 3UTRBERT result

Matched Ridge R1 versus geometry: rank ContextValue +0.033165, regret ContextValue +0.031141. Frozen encoder and cache; not a successful universal compiler by itself.

## 13. Parnet output-space result

Not evaluated. Actual RBPNet matched-Ridge fallback: rank ContextValue +0.043792, regret ContextValue +0.025140. Do not label these Parnet results.

## 14. Parnet hidden-embedding result

Not evaluated; excluded representation.

## 15. Selected architecture

Primary nested family choices in outer folds 0–4: M1, M2, M3, M1, M1. M1 adds RBP summaries to geometry; M2 adds expression interactions; M3 fits a shared sparse latent score and assay heads. These are evaluated choices, not an endorsed final deployment model.

## 16. Latent measurement-process result

M3 versus M2 on leave-source transfers improves mean rank by +0.033135 and regret by +0.022382, but harms regret by >0.020 in both TDP direction tasks. Gate J fails; M3 is not retained as a validated measurement solution.

## 17. Overall rank

0.625327563, equal-source/direction average of held-biological-unit predictions.

## 18. Overall regret

0.404538309, equal-source/direction average of held-biological-unit predictions.

## 19. Rank ContextValue over geometry

+0.042294418.

## 20. Regret ContextValue over geometry

+0.040094443; positive denotes reduced regret.

## 21. GoodSelection@3

0.234115961; gain over M0 +0.064792769.

## 22. GoodSelection@5

0.276664462; gain over M0 +0.027645503.

## 23. Biological-unit improvement fraction

0.544600939 (54.46%), below the frozen 55% threshold; 213 units, both directions averaged per unit.

## 24. Median biological-unit ContextValue

Regret +0.009947504.

## 25. Leave-best-one-out

Equal-source mean regret ContextValue +0.039030961.

## 26. Bootstrap interval

Paired biological-unit bootstrap, 10,000 draws within source, both directions preserved: 95% interval [0.0067933295626856965, 0.07385565670470746]. Not a row bootstrap.

## 27. Mikl matched mechanism

Implemented uncapped analysis: +0.015818 rank, +0.017845 regret; 120 held genes. Its recorded Gate C pass is qualified: the written two-per-gene cap was omitted and conflicts with the minimum-four within-gene subset rule. Literal protocol compliance and RBP-specific mechanism are not established.

## 28. TDP mechanism

All TDP rows carry the TDP-43 UG-rich motif label, but no TARDBP channel exists. Exact-geometry descriptive audit: 300 usable rows, 150 two-candidate comparisons in six parents. This September 9 diagnostic is not a newly frozen success gate. Geometry predictions tie within these pairs; favorable performance in one direction is not a separately validated biological discovery. No direct TDP-43 binding claim is supported.

| dataset | requested_direction | biological_units_full | decision_sets_full | rank_context_value | regret_context_value |
| --- | --- | --- | --- | --- | --- |
| tdp43_gse288185 | decrease | 6 | 150 | -0.023422 | -0.023422 |
| tdp43_gse288185 | increase | 6 | 150 | 0.155516 | 0.155516 |

## 29. Moffatt held-parent result

Eight biological parents, held together regardless of row count.

| requested_direction | rank_context_value | regret_context_value |
| --- | --- | --- |
| decrease | 0.068097 | 0.040377 |
| increase | 0.059429 | 0.011508 |

## 30. CAD→N2A

Nested-selected transfer versus geometry:

| requested_direction | rank_context_value | regret_context_value |
| --- | --- | --- |
| decrease | -0.013807 | -0.016571 |
| increase | -0.027009 | 0.003060 |

## 31. N2A→CAD

Nested-selected transfer versus geometry:

| requested_direction | rank_context_value | regret_context_value |
| --- | --- | --- |
| decrease | 0.018859 | 0.009575 |
| increase | 0.003236 | -0.001242 |

## 32. Firefly→GFP

Nested-selected transfer versus geometry:

| requested_direction | rank_context_value | regret_context_value |
| --- | --- | --- |
| decrease | 0.047598 | -0.003895 |
| increase | -0.097193 | -0.121567 |

## 33. GFP→Firefly

Nested-selected transfer versus geometry:

| requested_direction | rank_context_value | regret_context_value |
| --- | --- | --- |
| decrease | 0.030802 | 0.028517 |
| increase | 0.039215 | 0.009322 |

## 34. Leave Mikl out

Nested-selected transfer versus geometry:

| requested_direction | rank_context_value | regret_context_value |
| --- | --- | --- |
| decrease | 0.060532 | 0.036293 |
| increase | 0.029719 | 0.026046 |

## 35. Leave TDP out

Nested-selected transfer versus geometry:

| requested_direction | rank_context_value | regret_context_value |
| --- | --- | --- |
| decrease | 0.047114 | 0.062200 |
| increase | 0.028844 | 0.007882 |

## 36. Leave Moffatt out

Nested-selected transfer versus geometry:

| requested_direction | rank_context_value | regret_context_value |
| --- | --- | --- |
| decrease | 0.169413 | 0.117874 |
| increase | 0.228164 | 0.164995 |

## 37. 2–5 nt

Rank ContextValue +0.002950873; regret ContextValue +0.012901875; 26830 candidate rows and 209 evaluable units. Frozen band boundaries were not changed.

## 38. 6–10 nt

Rank ContextValue -0.023229295; regret ContextValue -0.030535199; 22444 candidate rows and 207 evaluable units. Frozen band boundaries were not changed.

## 39. 2–10 nt

Rank ContextValue -0.021293141; regret ContextValue -0.005722600; 49274 candidate rows and 213 evaluable units. Frozen band boundaries were not changed.

## 40. Exact-SNV descriptive result

Rank ContextValue -0.050000000; regret ContextValue -0.038976234; 38 candidate rows and 2 evaluable units. Descriptive only; cannot pass the small-edit gate.

## 41. RBP-permutation control

Retained rank gain 107.97%, regret gain 78.84%; control still meets both Gate A thresholds. Necessity fails.

## 42. Delta-RBP shuffle control

Retained rank gain 130.13%, regret gain 100.28%; control still meets both Gate A thresholds. Necessity fails. The delta donor construction cycles unequal-size units and is not a bijective row shuffle.

## 43. Cell-context-shuffle control

PENDING; no partial result is treated as final.

## 44. Parent-binding ablation

Knockout gain: rank +0.056341363, regret +0.035829318. Rank improves and roughly 89.36% of regret gain survives; aggregate necessity is not established.

## 45. Trans-interaction ablation

Gate H fails. M3 minus trans-knockout crossed-cell gain: rank +0.003888, regret +0.001199; insufficient for the frozen thresholds. Trans context is not supported for retention.

## 46. Stability ablation

Not applicable: no stability block was admitted. Gate I is neither pass nor fail.

## 47. Measurement-head ablation

Head randomization worsens pooled MSE 1.232723→1.789378 and Spearman 0.317235→0.068879. Equal-head MSE worsens but Spearman improves 0.155036→0.204898. Pre-head scores are unchanged by head reassignment. The added pooled-plus-macro conjunction was not an original frozen criterion; report the mixed evidence.

## 48. Evidence against edit-size shortcuts

Not established sufficiently for the compiler claim. Delta-RBP edit-size R-squared is 0.652844 in Moffatt and 0.864634 in TDP; Mikl is -0.341258. Matched Mikl estimates have a protocol qualification and identity/delta necessity fails. Predictive gain alone is not mechanistic evidence.

## 49. Direction-specific performance

| direction | within_source_rank_gain | within_source_regret_gain | leave_source_regret_gain | small_2_10_regret_gain | unit_improvement_fraction | direction_mean_conditions_met |
| --- | --- | --- | --- | --- | --- | --- |
| increase | 0.037033 | 0.025758 | 0.066308 | 0.002759 | 0.511737 | False |
| decrease | 0.047556 | 0.054430 | 0.072122 | -0.014204 | 0.469484 | False |

These are equal-source descriptive means and the explicit unit-improvement fraction. Mechanism failures preclude claiming a validated directional compiler even if a mean-based condition were favorable.

## 50. Source robustness

Leave-source Gate D passes: 6/6 positive regret tasks, mean rank +0.093964, regret +0.069215; largest source share of positive regret 68.11%. Cell/reporter Gate E fails: 1/4 and 2/4 tasks respectively improve both metrics, and their mean regret gains are negative. Full task tables remain archived.

## 51. Seed stability

M3 equal-source rank SD 0.009394 and regret SD 0.004400; all three seeds agree that Gate J fails. M0–M2 repeated outer-fold-0 fits agree exactly in the tested runtime. Sparse-model archive reproduction differs at ~1e-6–1e-5, so do not claim cross-run archive equality at 1e-8.

## 52. Integrity deviations

See finalshot_integrity_review.md: Mikl cap contradiction/omission, selection tie-order ambiguity, non-bijective delta donors, head-control aggregation ambiguity, and sparse-model numerical reproduction limits. Gate L is not certified as an unqualified pass. Original outputs and protocol text were preserved.

## 53. Tests passed

{'tests': 36, 'failures': 0, 'errors': 0, 'skipped': 0}; recorded in submission_tests.xml. Software tests are not substitutes for scientific protocol fidelity.

## 54. Files created

Required reports: finalshot_resource_audit.md, finalshot_protocol.md, finalshot_rbp_representation.md, finalshot_trans_context.md, finalshot_stability_prior.md, finalshot_latent_measurement_model.md, finalshot_mikl_matched_mechanism.md, finalshot_transfer_results.md, finalshot_small_edit_results.md, finalshot_controls.md, finalshot_novelty_audit.md, finalshot_final_verdict.md. Supplemental integrity/shortcut reports and machine-readable predictions, metrics, coefficients, and audits are under reports/ and results/finalshot/.

## 55. Commits

Key earlier checkpoints: 30c89a3 (protocol freeze), cbfc964 (completed RBP reconstruction). Recent checkpoint history at report generation (the report commit itself follows this snapshot):

```text
5910dd7 Complete parent-binding knockout models
f4e002e Evaluate FinalShot measurement-head randomization
11fbd42 Add resume-safe remaining control orchestration
9043d7f Evaluate FinalShot trans-context gate
21a4243 Add resume-safe trans-control orchestration
17bcc33 Add frozen crossed-cell trans-context control
72a1add Evaluate FinalShot RBP necessity controls
69e8830 Complete M3 delta-RBP controls
71b2a60 Complete M3 RBP identity controls
43fa387 Add checkpointed M3 control runner
cdff394 Complete direct delta-RBP controls
766332c Complete direct RBP identity controls
49ea3c9 Implement frozen FinalShot feature controls
ba3e0d5 Complete FinalShot transfer gates
6338696 Add leave-TDP M3 transfer
```

## 56. Astrocyte status

Sealed. No Astrocyte data and no N-zip outcomes were accessed in this work. No holdout opening is authorized by this report.

## 57. Is Phase C justified?

No. FULL GO requirements fail, and integrity qualifications remain.

## 58. Does original zero-shot RNAddress survive?

Not under the frozen evidentiary standards. Favorable average prediction scores do not meet distributed, transfer, small-edit, and mechanism requirements together.

## 59. Must the next hypothesis be RNAddress-Adapt?

If research continues, the protocol points to the separately defined few-shot active-design hypothesis RNAddress-Adapt, not another zero-shot cycle. No Adapt experiment is started or claimed validated here.

## 60. PV-CARE-level path for the original project?

No evidence-backed path to that success claim is established by this FinalShot. A transparent benchmark and negative-mechanism result may still be a useful research submission, but its acceptance, importance, or equivalence to PV-CARE is not guaranteed. Do not rename a failed universal compiler as a validated one.
