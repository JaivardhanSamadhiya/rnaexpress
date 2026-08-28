# RNAddress v3 Phase 2: mechanistic diagnosis of heterogeneous TDP-43 transfer

**Analysis class:** POST-LOCK DEVELOPMENT / DIAGNOSTIC

**Prespecified protocol commit:** `a38e13c`

**Random seed:** `20260828`

**Clustered bootstrap replicates:** 2,000

**Decision:** **GO**

## Executive verdict

The heterogeneous TDP-43 result is best explained by a combination of **objective/task mismatch** and **gene-specific mechanistic coupling**, not by a single generic distribution shift.

The strongest finding is the regret paradox. Frozen RNAddress v2.6 generally produced a better aggregate directional rank percentile than forward LightGBM (0.674923 versus 0.619682), yet worse normalized regret (0.376574 versus 0.293838), because its within-gene percentile objective did not reliably identify the extreme-effect edit. Across the eight gene-by-direction decisions in the four former lock genes, RNAddress placed the experimental oracle in its top five zero times. Its largest regret failure was the Fam160b2 decrease direction: normalized regret 0.7845 versus 0.0342 for forward LightGBM. The forward model selected an effect of -4.021 versus the -4.175 oracle, while RNAddress selected only -0.643. The extreme Fam160b2 interventions are not ordinary point-like edits: they complement many motif occurrences and alter tens to more than one hundred bases. This means that learning only relative percentile is insufficient for extreme-effect selection, and the TDP intervention task itself differs materially from the future exact-SNV design task.

The second finding is that the reported TDP-43 mechanism is real but is not coupled equally across genes. Intact-reporter RBNS binding tracks localization across all 16 genes (Spearman rho=0.3947), CLIP-supported interventions have much larger localization effects than motifs without CLIP (median absolute effect 0.1444 versus 0.0655), and source motif accessibility tracks localization effect (rho=-0.2716 overall; -0.4396 in the four former lock genes). However, motif-mutation localization and stability effects are clearly coupled only in Diras1 among the four historical lock genes (rho=0.2745, clustered-bootstrap 95% interval 0.1295 to 0.4099). Fam160b2, Lars2 and Synj2bp have near-zero intervention-level localization/stability correlations. Lars2 is especially informative: 96.5% of its reporters are CLIP-supported, yet its intact RBNS/localization relationship is negative (rho=-0.1712), its mutation-induced stability/localization relationship is null (rho=-0.0152), and RNAddress loses. Occupancy evidence is therefore important but not sufficient.

The third finding is negative and constraining: simple OOD distance cannot explain the failures. Lars2 is the least OOD former lock gene by every prespecified outside-support fraction (0% outside the development 95th-percentile threshold for contextual cosine, contextual Euclidean and mechanism distance), yet it has the worst custom rank percentile (0.4405). Fam160b2 is partly OOD, so support may contribute to that gene, but OOD cannot be the general causal account. Frozen-model disagreement is a weak-to-moderate aggregate warning signal (rho=0.2203 with RNAddress absolute rank error), but it is inconsistent by gene and would not, alone, have prevented the high-regret recommendations.

### Ranked explanations

1. **Strongly supported — percentile/magnitude objective mismatch plus intervention-task mismatch.** RNAddress misses extreme-effect edits despite acceptable broader ranking. The most extreme TDP edits are multi-base, multi-motif complement interventions, unlike the exact-SNV flagship task.
2. **Strongly supported — mechanism is conditional rather than motif-intrinsic.** Binding, CLIP occupancy and motif-local accessibility identify biological effect, but their relationship to localization changes substantially by gene and after motif disruption.
3. **Moderately supported — local regulatory context and accessibility are useful mechanistic axes.** Motif-local accessibility is informative; generic whole/intervention structure changes are weak.
4. **Moderately supported — uncertainty should combine multiple support signals.** Aggregate model disagreement tracks error, but disagreement and OOD are not reliable standalone gates.
5. **Weak / not supported — simple sequence-domain OOD as the main cause.** It may contribute to Fam160b2 but is contradicted by Lars2.
6. **Not supported — simple motif multiplicity or residual canonical-motif redundancy as the main cause.** Diras1 and Synj2bp have more multiple-motif reporters than the failed genes, and all canonical occurrences represented in the intervention definition were edited.

## Scientific and data status

The historical TDP-43 gate remains failed and is not reinterpreted. Every analysis here uses the TDP outcomes only as post-lock development/diagnostic information. No Phase 2 result is untouched validation.

The source audit established exact sequence-level identity for every one of the 4,566 historical parent/mutant pairs. The EV8 source sequences contain 20-nt handles on both ends; after deterministic handle removal, all 4,566 parents and all 4,566 mutants exactly equal the historical reconstruction. No historical pairing error was found, so the required stop condition was not triggered.

The master table uses deterministic ID, construct-label, or exact-sequence joins only. No table was paired by row order. Its mechanistic coverage is:

| Mechanistic record | Exact usable pairs | Treatment |
|---|---:|---|
| Historical localization intervention | 4,566 | Preserved without replacement |
| Frozen former-lock predictions | 1,006 | Used as committed; no refitting |
| Processed SLAM stability intervention | 3,117 finite pairs | Exact parent/mutant linkage |
| RBNS intervention | 3,600 pairs | Exact parent/mutant linkage |
| Reporter-level CLIP | 4,566 parents | Exact natural reporter ID |
| Source motif accessibility | 4,260 parents | Exact reporter/motif mapping |
| Independently computed Vienna accessibility | 4,566 pairs | Edit/motif-local summaries |

The raw EV5 SLAM reconstruction was quarantined. It contains 10,935 duplicated `sample+oligo` keys under `WT_t0_1`, has no `WT_t0_3` label, and GEO metadata lists only WT t0 Rep1 and Rep2. The analysis therefore uses the publisher's processed Figure 6C stability source, which has 3,600 exact parent/mutant pairs. Seventy-one processed pairs contain an infinite log value caused by a zero ratio and are treated as missing, without clipping or pseudocount invention, leaving 3,117 finite paired intervention deltas.

The source and linkage inventory, hashes, row counts, ambiguities and exclusions are documented in `reports/v3_tdp_source_data_audit.md` and `reports/v3_tdp_source_data_audit.json`.

## Frozen performance and the anti-concentration failure

The historical aggregate values are unchanged:

| Model | Directional rank percentile | Normalized regret | Spearman |
|---|---:|---:|---:|
| RNAddress v2.6 | 0.674923 | 0.376574 | 0.292211 |
| Forward LightGBM | 0.619682 | 0.293838 | 0.294999 |
| Motif/accessibility Ridge | 0.544052 | 0.374199 | 0.321641 |

The gene-level result shows why the aggregate is unstable:

| Gene | n | RNAddress rank | Forward rank | Gain | RNAddress regret | Forward regret | RNAddress Spearman |
|---|---:|---:|---:|---:|---:|---:|---:|
| Diras1 | 278 | 0.9531 | 0.8357 | +0.1173 | 0.0739 | 0.0433 | 0.6037 |
| Synj2bp | 397 | 0.6225 | 0.3207 | +0.3018 | 0.4712 | 0.5888 | 0.0364 |
| Fam160b2 | 246 | 0.6837 | 0.7449 | -0.0612 | 0.4360 | 0.0669 | 0.6979 |
| Lars2 | 85 | 0.4405 | 0.5774 | -0.1369 | 0.5252 | 0.4763 | -0.1692 |

Diras1 is a genuine RNAddress transfer success by broad ranking. Synj2bp is not comparably convincing: RNAddress's own effect correlation is nearly zero and regret remains 0.4712; the large custom-minus-forward rank gain mostly reflects forward LightGBM collapsing to 0.3207. Treating Synj2bp as an unqualified mechanistic success would overstate the evidence.

Fam160b2 is the clearest regret paradox. RNAddress correlates strongly with the full measured ranking (rho=0.6979) yet selects a poor extreme decrease. Lars2 is a more complete transfer failure: negative full-gene Spearman, below-median directional rank, and high regret.

## Stability mediation

The experimental motif-mutation effect has only a modest pooled relationship with the stability effect:

| Scope | n | Spearman rho | Clustered-bootstrap 95% interval | Pearson | Theil-Sen slope |
|---|---:|---:|---:|---:|---:|
| All 16 genes | 3,117 | 0.0947 | 0.0105 to 0.1998 | 0.1168 | 0.0378 |
| Four former lock genes | 641 | 0.0765 | -0.0464 to 0.2515 | 0.0552 | 0.0307 |
| Diras1 | 181 | 0.2745 | 0.1295 to 0.4099 | 0.2330 | 0.1188 |
| Fam160b2 | 133 | 0.0072 | -0.1675 to 0.1968 | -0.0637 | 0.0023 |
| Lars2 | 75 | -0.0152 | -0.2520 to 0.2125 | -0.0045 | -0.0081 |
| Synj2bp | 252 | -0.0574 | -0.1912 to 0.0690 | -0.0649 | -0.0163 |

The construct-level KO-minus-WT relationship is stronger for parent reporters than motif-mutant reporters across all genes (rho=0.1692 versus 0.0628), consistent with motif disruption weakening coupling. In the four former lock genes it is 0.1347 for parents and 0.0464 for mutants. Diras1 again has the clearest relationship (parent rho=0.2717; mutant rho=0.1692); Fam160b2, Lars2 and Synj2bp are near zero.

Descriptive regressions support heterogeneity rather than a universal mediator. Stability alone explains R-squared=0.0137. Adding gene raises R-squared to 0.3361 and reduces the stability coefficient from 0.0978 to 0.0566. Adding prespecified mechanism terms raises R-squared to 0.4871 and reduces the stability coefficient to 0.0235. These models are descriptive; no formal causal mediation claim is made because the assumptions are not defensible from the processed measurements and incomplete finite-pair coverage.

**Conclusion:** stability is biologically relevant, especially in Diras1, but it is not a universal explanation for RNAddress success or failure. V3 may use stability as an auxiliary mechanistic target where reporter-matched data exist; it should not assume stability mediation for every gene or require stability at inference.

## Binding, CLIP occupancy, motif architecture and accessibility

### Binding

For intact parents, RBNS binding is associated with localization across all 16 genes (rho=0.3947, n=3,921) and the former lock genes (rho=0.3102, n=833). After motif mutation, the association drops to rho=0.1229 overall and 0.0581 in the former lock genes. The intervention binding delta has only rho=0.1088 overall and 0.0796 in the former lock genes.

Within former lock genes, parent RBNS/localization rho is 0.3147 for Diras1, 0.2950 for Fam160b2, -0.1712 for Lars2 and 0.3081 for Synj2bp. Mutation-induced binding/localization rho is 0.1972 for Diras1, 0.0231 for Fam160b2, 0.1642 for Lars2 and -0.0043 for Synj2bp. Binding is therefore a meaningful mechanistic axis, but its intervention consequence depends on context.

### CLIP occupancy

Across all 4,566 interventions, CLIP-supported motifs have median localization delta -0.1146 and median absolute effect 0.1444, compared with -0.0031 and 0.0655 without CLIP. RNAddress's median rank advantage over forward is -0.0253 in the CLIP-supported group versus +0.0076 without CLIP, indicating that the occupied, larger-effect regime is where the custom model tends to lose relative ground.

The result is highly gene-specific:

* Fam160b2 CLIP-supported reporters have median delta -1.9766 and median absolute effect 1.9766, versus -0.0281 and 0.1051 without CLIP. RNAddress advantage is -0.0816 in the CLIP stratum.
* Diras1 CLIP-supported reporters have median delta -0.2217 and absolute effect 0.2229, versus +0.0089 and 0.0684 without CLIP.
* Lars2 is 96.5% CLIP-supported, yet the CLIP-supported median effect is only -0.0027 and its stability and binding couplings are weak. CLIP evidence alone is not enough.
* Synj2bp has only 17.4% CLIP-supported reporters and a comparatively weak CLIP effect separation.

This supports explicit motif-by-occupancy-by-context interactions, not a binary CLIP or motif-count feature used in isolation.

### Motif multiplicity and residual motifs

Multiple edited motifs produce larger pooled effects than a single motif (median absolute effect 0.0902 versus 0.0640), but multiplicity does not separate transfer wins from losses. Diras1 and Synj2bp have multiple-motif fractions of 81.3% and 70.5%, respectively, compared with 45.1% for Fam160b2 and 49.4% for Lars2. Thus the proposed simple/nonlocal redundancy explanation is contradicted at gene level.

All reconstructed interventions complement every canonical occurrence represented by the study's motif definition, so the remaining-unedited-canonical-motif fraction is zero in all 4,566 rows. Residual canonical-motif redundancy cannot be tested from this design and must not be claimed as an explanation.

### Motif-local structure

Source-provided motif accessibility and independently computed exact-matched Vienna motif accessibility have rho=0.6384 across 4,070 reporters, a useful sanity check without treating the two estimators as identical.

Source parent motif accessibility is associated with localization effect in the expected direction: rho=-0.2716 across all genes and -0.4396 in the former lock genes, meaning that more accessible motifs tend to yield a more negative mutant-minus-parent localization effect. Exact-matched Vienna motif accessibility gives rho=-0.2049 overall and -0.3581 in the former lock genes.

In contrast, generic mutant-parent structural deltas are weak: edit-centered accessibility delta rho=0.0496 with localization, and local Vienna deltas at radii 5, 10 and 20 nt are approximately -0.018, -0.039 and -0.081 overall and near zero in the former lock genes. Local parent motif accessibility is useful biology; adding broad global structure summaries everywhere is not supported.

## Regret paradox and extreme-effect coverage

The per-direction decomposition directly supports hypotheses A through D from the protocol:

* RNAddress oracle ranks average 34 for Diras1, 94 for Fam160b2, 45 for Lars2 and 185.5 for Synj2bp.
* RNAddress top-five oracle coverage is 0/8 directions. Forward LightGBM captures the Diras1 decrease oracle in its top three/top five and places it rank 2.
* For Fam160b2 decrease, RNAddress normalized regret is 0.7845 and the oracle is rank 47; forward regret is 0.0342 and the oracle is rank 25, while its selected edit is itself nearly oracle-sized.
* For Diras1 decrease, RNAddress regret is 0.1023 and oracle rank 20; forward regret is 0.0091 and oracle rank 2.
* In the descriptive top-5%-effect analysis, the mean absolute percentile error averaged over the eight directions is 0.3188 for RNAddress and 0.3100 for forward, while the selected top-1 falls in that tail in 1/8 directions for RNAddress versus 2/8 for forward.

The extreme Fam160b2 oracle changes 88 bases across 68 canonical motif hits; other extreme Fam160b2 interventions alter roughly 72 to 145 bases and 56 to 113 motif hits. The strongest Diras1 decreases alter about 45 bases across 19 motifs. Lars2 and Synj2bp extreme effects are much smaller and generally involve 5 to 7 changed bases. Across former-lock interventions, edited-base count and motifs destroyed correlate with localization delta at approximately rho=-0.435 and -0.427.

RNAddress does not simply fail every large edit; rather, it compresses and fails to resolve the very top of a high-effect cluster. This is exactly the regime normalized top-1 regret punishes and percentile-only training does not represent directly.

**Conclusion:** magnitude-aware learning is justified. V3 should learn effect magnitude jointly with directional within-parent/gene ranking and should evaluate calibration in the extreme tail. This must be developed without redefining the failed historical gate.

## Distribution support and post-lock leave-one-gene-out trust diagnosis

Outcome-free support was computed against the 12 historical development genes using training-only standardization and nearest-development contextual and mechanistic distances. The development 95th-percentile outside-support thresholds are 0.4097 for contextual cosine distance, 75.915 for contextual Euclidean distance and 1.6019 for mechanism distance.

| Gene | Median cosine distance | Outside cosine | Outside Euclidean | Median mechanism distance | Outside mechanism |
|---|---:|---:|---:|---:|---:|
| Diras1 | 0.2928 | 0.36% | 14.03% | 0.5927 | 1.08% |
| Fam160b2 | 0.2806 | 10.98% | 18.70% | 0.6295 | 23.98% |
| Lars2 | 0.2765 | 0% | 0% | 0.4831 | 0% |
| Synj2bp | 0.2798 | 2.27% | 0% | 0.4292 | 0% |

Fam160b2 is partly outside development support, so support distance may be one contributor. Lars2 is the decisive counterexample: it is the best-supported former lock gene yet RNAddress performs worst. Synj2bp is also well supported but has weak custom effect correlation despite beating an even worse comparator.

With only four former-lock gene outcomes, fitting a gene-level trust classifier would be statistically indefensible. The explicitly post-lock leave-one-gene-out diagnostic therefore asks whether prespecified outcome-free support signals rank failure consistently; they do not. A future abstention system needs richer training contexts and combined uncertainty/mechanism support, not a threshold learned from these four labels.

## Frozen-model disagreement

Across 1,006 former-lock interventions, the standard deviation of frozen model percentiles has rho=0.2203 with RNAddress absolute rank error. The lowest disagreement quartile has median/mean absolute error 0.1347/0.2007, while the highest quartile has 0.2692/0.3246. This is useful aggregate evidence for uncertainty research.

The relationship is not stable by gene: rho=0.3539 for Diras1, 0.1493 for Fam160b2, -0.1482 for Lars2 and 0.0058 for Synj2bp. Selected-edit disagreement also fails to identify all bad recommendations: the Fam160b2 decrease recommendation has disagreement 0.0950 despite regret 0.7845, and the Lars2 decrease recommendation has disagreement 0.0292 despite regret 0.5535. Conversely, Synj2bp decrease has high disagreement 0.4258 and high regret 0.5679.

**Conclusion:** calibrated uncertainty/abstention is justified as a development direction, but a frozen-model-disagreement threshold by itself is not justified and was not optimized.

## Four gene-level failure profiles

### Fam160b2

**Evidence-supported:** RNAddress has good whole-gene Spearman (0.6979) but loses directional rank to forward by 0.0612 and has a much worse regret (0.4360 versus 0.0669). Stability coupling is null (rho=0.0072). CLIP support identifies an extreme-effect subpopulation: median effect -1.9766 when CLIP-supported. Fam160b2 is partially OOD, with 24.0% outside mechanism support. Its decrease oracle is a huge multi-motif edit, and RNAddress misses its magnitude.

**Plausible but unproven:** partial context shift may compound a percentile objective that cannot distinguish extreme occupied multi-motif interventions. The data do not establish which unmeasured cofactor creates the extreme response.

### Lars2

**Evidence-supported:** RNAddress loses by 0.1369, has Spearman -0.1692 and regret 0.5252. Lars2 is not OOD by any prespecified outside-support fraction. It is almost universally CLIP-supported (96.5%), yet parent RBNS/localization rho is -0.1712 and localization/stability rho is -0.0152. Disagreement is not predictive of error within Lars2.

**Plausible but unproven:** the measured canonical TDP axes do not capture the functional determinant in Lars2, or the effect range is too weak/noisy for learned ranking. The evidence rules out claiming that occupancy alone defines a transferable mechanism.

### Diras1

**Evidence-supported:** RNAddress is a real broad-ranking success (rank 0.9531, Spearman 0.6037) and is the only former-lock gene with clear localization/stability coupling (rho=0.2745). It also shows binding and CLIP effect separation. It is mostly in support. However, forward LightGBM finds the extreme decrease much more accurately, so even this success exposes the magnitude weakness.

**Plausible but unproven:** RNAddress transfers because Diras1 follows the stability-coupled sequence/context mechanism represented in development data. Four-gene evidence is insufficient to claim this as a general rule.

### Synj2bp

**Evidence-supported:** custom-minus-forward rank gain is +0.3018, but RNAddress Spearman is only 0.0364 and regret is 0.4712. Stability coupling is absent and CLIP prevalence is low. It is well inside support. Model disagreement is unrelated to intervention error within this gene.

**Plausible but unproven:** the apparent win is mainly comparator failure rather than strong mechanistic transfer. It should not be used as evidence that RNAddress solved Synj2bp biology.

## What v3 should change

1. **Use a dual learning objective.** Learn calibrated effect magnitude together with within-group directional ranking. Preserve ranking because it helped on Diras1, but explicitly penalize failure to identify extreme useful effects.
2. **Represent mechanism conditionally.** Use motif identity/count together with occupancy or binding priors and motif-local accessibility, with interactions rather than additive binary flags.
3. **Keep structure local and regulatory.** Prioritize accessibility at the relevant motif/edit neighborhood; do not inflate the model with generic whole-sequence folding summaries unsupported by this diagnosis.
4. **Treat stability as an auxiliary mechanistic signal, not a universal mediator.** Multi-task or auxiliary supervision is justified only where reporter-matched stability exists; inference must tolerate its absence.
5. **Separate intervention regimes.** Multi-base motif-complement interventions and exact-SNV design should be tagged or modeled as distinct tasks. TDP extreme-effect magnitude cannot be assumed to calibrate SNV effect magnitude.
6. **Develop calibrated selective prediction from multiple signals.** Combine predictive uncertainty, model/representation support and mechanism support. Validate abstention prospectively in later development; do not adopt a Phase 2 threshold.

## What v3 should not change

* Do not build v3 primarily as an OOD detector; Lars2 falsifies that as a general explanation.
* Do not use model disagreement alone as a trust gate; it misses high-regret Fam160b2 and Lars2 choices.
* Do not use motif count or CLIP overlap alone as a mechanism model; Lars2 has near-universal CLIP support and still fails.
* Do not assume universal stability mediation; three of four former-lock genes have near-zero intervention coupling.
* Do not add generic global structure summaries merely because source motif accessibility matters.
* Do not interpret Synj2bp's comparator win as strong custom-model mechanistic success.
* Do not call any subsequent TDP performance independent validation.

## Implications for the flagship claim

The failure is a combination of **fixable model misspecification**, **mechanism conditionality**, **insufficient independent contexts**, and **task mismatch**.

The objective misspecification is actionable: percentile ranking should be coupled to magnitude. The mechanism misspecification is also actionable: motif occupancy/binding and local accessibility need explicit interactions. However, four historical lock genes are too few to establish a reliable gene-level trust rule, and the multi-base TDP complement assay is not the same intervention regime as exact SNVs. Therefore Phase 2 supports model development but not a claim that the flagship selective-SNV hypothesis is already confirmed.

## Decision

**GO.** There is a concrete evidence-supported v3 direction: magnitude-aware, mechanism-conditional, locally structure-aware learning with multi-signal uncertainty, while explicitly separating multi-base motif interventions from the SNV task. The recommendation is narrower than “add every feature”: OOD-only gating, generic structure, CLIP-only logic and universal stability mediation are rejected.

## Reproducibility and protected-data statement

The deterministic analysis entry point is `python -m src.analysis.diagnose_tdp43_v3`. Exact package versions, source hashes, output hashes, exclusions, seed and protected-data flags are in `results/v3_phase2/analysis_manifest.json`. Machine-readable conclusions are in `results/v3_phase2/phase2_verdict.json`.

Astrocyte outcomes were not inspected, analyzed, recorded, or used for v3 development; an inherited test previously loaded the complete worksheet programmatically, and this deviation was disclosed before v3 model development.

The Moffatt `GSE334718_RAW.tar` archive was not listed, opened, extracted or used in Phase 2. Phase 2 ends here; no representation benchmark, predictive model training, Astrocyte prediction, or Phase 3 work was performed.
