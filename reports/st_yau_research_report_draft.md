# COVER PAGE

**Student Name:** [YOUR FULL NAME]

**School:** [YOUR SCHOOL NAME]

**Province / State and Country:** [YOUR STATE OR PROVINCE], [YOUR COUNTRY]

**Instructor / Mentor:** [INSTRUCTOR OR MENTOR NAME AND TITLE]

**Report Title:** Measurement Limits and Composition Dominance in Zero-Shot RNA Intervention Selection: A Pre-Registered Computational Evaluation Framework

**Submission Category:** Computer Science — Computational Award

**Date:** September 2026

---

# Measurement Limits and Composition Dominance in Zero-Shot RNA Intervention Selection: A Pre-Registered Computational Evaluation Framework

**Author:** [YOUR FULL NAME]

**Affiliation:** [YOUR SCHOOL NAME], [CITY], [STATE/PROVINCE], [COUNTRY]

---

## Abstract

Subcellular RNA localization is controlled in part by *cis*-regulatory sequence elements in 3′ untranslated regions (3′UTRs), often called zipcodes. Massively parallel reporter assays (MPRAs) now measure localization for tens of thousands of sequence variants, raising a natural computational question: can a model trained without seeing a biological parent or context rank which RNA edits will improve localization—*zero-shot intervention selection*?

This report presents **RNAddress**, a five-stage, pre-registered computational framework for answering that question rigorously. Using three published neuronal and cell-line MPRA benchmarks totaling 62,665 candidate interventions across 215 genes, we evaluate mechanism-aware feature representations (RBP binding, language-model embeddings, RNA structure, processing signals), nested cross-validation, and eleven null controls.

We obtain three principal results. First, **within-parent intervention ranking is unmeasurable** on current benchmarks: outcome reliability is only 0.239 because differencing near-identical sequences amplifies assay noise. Second, **absolute localization and edit direction are predictable**: unseen variants within a known 3′UTR reach auROC 0.950, and edit direction generalizes across 166 unseen genes at auROC 0.705. Third, **the recoverable signal is bulk AU composition, not a higher-order zipcode grammar**, and **assay sources disagree on the sign of the AU effect**, preventing universal transfer of any intervention rule.

These findings establish measurable criteria—reliability, composition controls, and cross-source sign consistency—that any future zero-shot RNA intervention selector must satisfy. Source code, frozen protocols, and reproducible evidence records are provided in a public repository.

**Keywords:** RNA localization; 3′UTR; massively parallel reporter assay; zero-shot learning; intervention selection; pre-registration; computational biology; reliability analysis; zipcode; AU-rich elements

---

## Table of Contents

1. Introduction
2. Background and Related Work
3. Research Question and Hypotheses
4. Materials and Data Sources
5. Methods and Algorithm Implementation
   - 5.1 Problem Formulation
   - 5.2 Feature Representations
   - 5.3 Evaluation Framework and Gates
   - 5.4 Reliability and Ceiling Analysis
   - 5.5 Software Architecture and Reproducibility
6. Experimental Design: Five Evaluation Eras
   - 6.1 Era 1 — FinalShot Baseline
   - 6.2 Era 2 — Mechanism-v2 Nested Evaluation
   - 6.3 Era 3 — Mechanism-v3 Grammar and Capacity Probes
   - 6.4 Era 4 — Mechanism-v4 Sequence-Level Reframing
   - 6.5 Era 5 — Mechanism-v5 Cross-Gene and Cross-Source Transfer
7. Results
   - 7.1 Intervention Ranking Fails Due to Measurement Noise
   - 7.2 Absolute Localization Is Learnable Within Context
   - 7.3 Edit Direction Generalizes Across Genes but Is Composition-Dominated
   - 7.4 Cross-Source Transfer Fails Due to Sign Instability
   - 7.5 Summary of Gate Outcomes Across All Eras
8. Discussion
9. Conclusion
10. Future Work
11. Bibliography
12. Acknowledgments

---

## 1. Introduction

Messenger RNA (mRNA) localization to specific subcellular compartments—such as neurites in neurons—is essential for spatial control of gene expression. Short sequence motifs in 3′UTRs can act as zipcodes that direct localization. With the advent of massively parallel reporter assays (MPRAs), researchers can now test thousands to millions of sequence variants in a single experiment, producing datasets rich enough to train machine learning models.

A compelling but untested computational goal is **zero-shot RNA intervention selection**: given a reference 3′UTR and a set of candidate edits, predict which edit will most improve localization *without* having observed that exact biological parent during training. If feasible, such a system—conceptually an "RNAddress"—could guide RNA therapeutic design and synthetic biology.

However, claiming that such a system works requires more than training a model and reporting high accuracy. It requires:

1. **A pre-specified estimand** (what exactly is being predicted),
2. **Rigorous cross-validation** that respects biological grouping,
3. **Null controls** that distinguish real sequence grammar from composition artifacts,
4. **Reliability analysis** separating signal from measurement noise, and
5. **Cross-context transfer tests** before claiming universality.

This report describes a computational research program that implements all five requirements across five sequentially frozen evaluation eras. The original product hypothesis—universal zero-shot RNAddress—is **not supported** on current public benchmarks. Instead, we identify **why** it fails: insufficient paired-measurement reliability, dominance of AU composition over mechanistic features, and inconsistent sign of composition effects across assay sources.

This negative-but-mechanistic result is itself a contribution to computational biology: it defines measurable prerequisites for any future intervention selector and provides reproducible open-source infrastructure for testing them.

---

## 2. Background and Related Work

### 2.1 RNA Localization and Zipcodes

Neuronal mRNAs are enriched in dendrites and axons through active transport mediated by RNA-binding proteins (RBPs) recognizing zipcode motifs. Classic examples include the β-actin zipcode and AU-rich elements. Mendonsa et al. (2023) developed N-zip, combining neurite/soma fractionation with MPRA to identify zipcodes at scale in primary cortical neurons, reporting let-7 binding sites and (AU)n repeats as de novo zipcodes.

### 2.2 MPRA-Based Localization Benchmarks

von Kügelgen et al. (2022) performed subcellular fractionation MPRA on ~50,000 3′UTR reporter sequences in CAD and Neuro-2a cell lines (GEO: GSE173098). They trained gradient-boosted classifiers using 4-mer counts (auROC 0.83) or 218 RBP motif scores (auROC 0.81) to predict neurite versus soma enrichment—demonstrating that **sequence-level localization prediction is feasible**, with simple k-mers outperforming RBP features.

Additional datasets in our certified benchmark include deep mutagenesis screens (Moffatt et al., GSE334718) and TDP-43–related localization reporters (GSE288185), providing diverse assay contexts.

### 2.3 Computational Prediction of RNA Properties

Recent tools apply deep learning to RNA: RBPNet for RBP binding (Hingerl et al., 2022), 3UTRBERT for sequence embeddings (Ji et al., 2021), structure predictors, and genomic language models. These raise the hypothesis that **mechanism-aware features** might outperform k-mers for intervention selection. Our work tests that hypothesis directly with pre-registered null controls.

### 2.4 Zero-Shot Learning in Computational Biology

Zero-shot prediction—generalizing to unseen biological contexts—is standard in protein structure (AlphaFold) but far harder for functional assays where measurement noise and context dependence dominate. Our framework adapts zero-shot evaluation from machine learning to paired intervention data with explicit reliability accounting.

### 2.5 Gap Addressed by This Work

Prior MPRA studies ask: *"Does this sequence localize?"* We ask the harder question: *"Which edit to this parent sequence is best?"* and *"Does a rule learned in one assay transfer to another?"* No prior work, to our knowledge, pre-registers and systematically falsifies universal zero-shot intervention selection across mechanism-aware representations with composition nulls and cross-source sign tests.

---

## 3. Research Question and Hypotheses

### 3.1 Primary Research Question

**Can mechanism-aware sequence features enable zero-shot selection of RNA edits that improve subcellular localization, generalizing to unseen biological parents and assay contexts?**

### 3.2 Operational Estimands Tested

We tested four progressively refined estimands:

| Estimand | Description |
|---|---|
| E1: Paired intervention ranking | Rank candidate edits within a parent by improvement over reference |
| E2: Absolute sequence localization | Predict localization of unseen variant sequences |
| E3: Cross-gene edit direction | Predict sign of edit effect for genes not seen in training |
| E4: Cross-source finite difference | Train absolute model in source A; score f(mutant)−f(parent) in source B |

### 3.3 Hypotheses

**H1 (Mechanism):** Combined RBP, language-model, structure, and processing features outperform k-mer composition nulls for intervention selection.

**H2 (Zero-shot):** Models generalize across genes and assay sources without parent-specific training.

**H3 (Measurement):** Paired difference outcomes have lower reliability than absolute per-sequence outcomes, limiting E1.

**H4 (Composition):** AU-richness mediates most predictable localization signal, consistent with published (AU)n zipcode biology.

Each hypothesis was mapped to pre-registered gates with fixed numeric thresholds committed before scoring.

---

## 4. Materials and Data Sources

### 4.1 Certified Development Benchmark

All experiments use a hash-pinned candidate table (`model_candidate_rows.csv.gz`, SHA-256 verified at load time) containing **93,208 rows** and **62,665 interventions** across three sources:

| Source | Accession | Sequences | Genes | Parent contexts | Sequence length |
|---|---|---:|---:|---:|---|
| Mikl (neuronal MPRA) | GSE173098 | 11,808 | 189 | 5,759 | 150 nt |
| Moffatt (deep mutagenesis) | GSE334718 | 46,291 | 10 | 8 | 260 nt |
| TDP-43 reporters | GSE288185 | 4,566 | 16 | 4,566 | 260 nt |

Outcomes are log2 neurite/soma enrichment or author-normalized variants thereof, with replicate-derived uncertainty where available.

### 4.2 Grouping Structure

Candidates are grouped into **211 connected components** (all-allele, 95% global Levenshtein clustering) spanning **213 biological units**, with **445 decision sets** used for paired ranking evaluations.

### 4.3 Feature Resources

Mechanism-aware features include **606 outcome-free mechanism columns** used in Eras 1–3:

- **Geometry** (28): edit descriptors, positions, spans
- **RBPNet signed binding** (412): predicted RBP affinity changes
- **3UTRBERT pooled delta** (128): language-model embedding differences
- **Structure delta** (18): predicted secondary structure changes
- **Processing delta** (8): cleavage/polyadenylation signals
- **Motif delta** (8): known motif presence changes
- **Trans-aligned** (4): transport-related alignment features

Ceiling analyses in Era 3 additionally include **540 random k-mer projection columns**, for **1,146 total** in the leaky-ceiling matrix. All features are computed outcome-free from sequence alone.

### 4.4 Data Integrity Constraints

Two holdout datasets were **never accessed** during development, per pre-specified sealing rules:

- N-zip saturation mutagenesis outcomes (Nat. Neurosci. 2023)
- Astrocyte in vivo MPRA holdout

This preserves the option of a one-time external confirmation in future work but prevents data leakage in the current evaluation.

---

## 5. Methods and Algorithm Implementation

### 5.1 Problem Formulation

For each candidate intervention *i* with parent sequence *p* and mutant sequence *m*, we observe localization effect *yᵢ* (continuous) and uncertainty *σᵢ*. Features **xᵢ** are computed from (*p*, *m*) without using *yᵢ*.

**Paired ranking (E1):** Within each decision set *S*, rank candidates by predicted score; compare to rank by observed *yᵢ* using normalized regret and normalized rank.

**Classification (E2, E3):** Label = significant neurite enrichment if *yᵢ* > 0 and *yᵢ/σᵢ* ≥ 1.96.

**Finite difference (E4):** Train regressor *f* on absolute *y*; predict edit effect as *f*(*m*) − *f*(*p*).

### 5.2 Feature Representations

**Mechanism stack (Eras 1–3):** Full 1,146-dimensional feature vector described in §4.3.

**K-mer features (Eras 4–5):** Length-invariant k-mer frequencies for k ∈ {1,2,3,4,5}, totaling 1,364 dimensions for absolute models; **delta k-mer frequencies** (mutant minus parent) for edit-direction models.

**Composition control:** AU fraction change Δ(AU) = AU(*m*) − AU(*p*), a single-feature baseline testing the published (AU)n zipcode hypothesis.

**Random k-mer projection null:** 84 random linear projections of delta k-mer space, seeded—reproducing the v2 finding that random features can match mechanism stacks.

### 5.3 Evaluation Framework and Gates

We implement **nested cross-validation**: 5 outer folds × 3 inner folds; 48 frozen model recipes (8 families × 6 variants); 720 inner-only fits verified by content hash before any outer score.

**Primary metrics (paired):**

- Normalized rank gain vs. random expected rank
- Normalized regret gain
- Good@3 and Good@5 (fraction of decision sets where true best appears in top-k)

**Primary metrics (classification/regression):**

- Area under ROC curve (auROC)
- Spearman correlation ρ
- Worst-fold performance (stress test)

**Aggregation:** Mean within source/component/direction, then equal mean across source×direction contexts.

**Uncertainty:** Paired connected-component bootstrap, 10,000 replicates, seed 20260909.

**Pre-registered gates (examples):**

- g1: rank_gain ≥ 0.020 AND regret_gain ≥ 0.010
- g3: block removal Holm-corrected significance
- a1: cross-gene auROC ≥ 0.650
- a3: beat AU-delta by ≥ 0.030 auROC

Every gate threshold is committed in version-controlled JSON **before** any outer score is computed. Write-once evidence files prevent post-hoc modification.

### 5.4 Reliability and Ceiling Analysis

We define **outcome reliability** as:

\[
\text{Reliability} = \frac{\mathrm{Var}(y)}{\mathrm{Var}(y) + \mathbb{E}[\sigma^2]}
\]

computed over unique sequences. This separates biological signal variance from measurement noise variance.

We also compute **leaky ceilings**: train nonlinear models (HistGradientBoostingRegressor) with all features on held-out folds to estimate the maximum achievable paired rank gain if representation—not noise—were the bottleneck.

### 5.5 Software Architecture and Reproducibility

The pipeline is implemented in Python 3 with modular packages:

- `src/mechanism_v2/` — nested CV, 720 inner fits, 11 null controls
- `src/mechanism_v3/` — grammar arms, capacity ceiling, nonlinear probe
- `src/mechanism_v4/` — sequence-level absolute localization
- `src/mechanism_v5/` — cross-gene edit direction, cross-source finite difference

**Fail-closed I/O:** Loaders verify SHA-256 hashes of input tables; writes outside namespace directories raise PermissionError; evidence records use write-once semantics.

**Testing:** 113 (v2) + 11 (v4) + 19 (v5) = 143 automated tests; legacy tests excluded to prevent loading sealed data.

**Repository:** [https://github.com/JaivardhanSamadhiya/rnaexpress](https://github.com/JaivardhanSamadhiya/rnaexpress) (branch `rnaddress-mechanism-v4`, commits through `e2e19df`).

---

## 6. Experimental Design: Five Evaluation Eras

Each era addresses a distinct failure mode discovered by the prior era. Designs are frozen and committed before scoring.

### 6.1 Era 1 — FinalShot Baseline

Initial zero-shot RNAddress evaluation with mechanism-aware features and paired ranking. **Verdict: NO-GO.** Established that the historical negative result must not be reversed or reinterpreted.

### 6.2 Era 2 — Mechanism-v2 Nested Evaluation

Full implementation: 720 inner fits, 9 score vectors, controls N0–N10 (geometry, edit descriptors, random k-mer projection, bijections, block removals with Holm correction), transfer evaluation, bootstrap uncertainty.

**Key results:**

- Primary rank gain +0.0250; regret gain +0.0252
- Random k-mer null **+0.0286** — beats mechanism stack
- Best block removal p = 0.035; Holm threshold 0.247 — no block significant
- Bootstrap 95% CI for regret gain includes zero
- **Verdict: NO-GO** (failed g2, g4, g5, g7, g9, g10)

### 6.3 Era 3 — Mechanism-v3 Grammar and Capacity Probes

Tests outcome-free zipcode grammar and pre-registered nonlinear arm (HistGradientBoostingRegressor).

**Diagnostics:**

- Within-decision reliability: **0.239**
- Leaky nonlinear ceiling: +0.0218 rank gain (gate requires 0.020 — margin 0.0018)
- Grammar informative for only 3.6% of rows (tie-breaking artifact)

**Verdict: NO-GO** on all arms.

### 6.4 Era 4 — Mechanism-v4 Sequence-Level Reframing

Changes estimand from paired ranking to **absolute per-sequence localization** on Moffatt (reliability 0.8818).

**Results (primary seed):**

| Estimand | auROC | Spearman ρ |
|---|---:|---:|
| T1: Within-parent design | **0.9503** | **+0.799** |
| T1: Composition control (k=1,2) | 0.9306 | +0.753 |
| T2: Cross-gene zero-shot | 0.6980 | +0.273 |
| T2: Composition control | **0.7529** | +0.351 |
| Shuffled-label null | 0.5006 | +0.009 |

T1 passes absolute bars; fails composition gate (+0.0197 < +0.030). T2 fails; rich features transfer **worse** than composition.

**Verdict: NO-GO.**

### 6.5 Era 5 — Mechanism-v5 Cross-Gene and Cross-Source Transfer

Two previously untried arms on complementary sources:

**Arm A:** Delta k-mer logistic regression; Mikl confident subset; 1,342 sequences, 166 genes; grouped by frozen biological fold.

**Arm B:** Ridge absolute model trained on Moffatt (46,291 sequences); finite difference scored on Mikl and TDP-43.

**Verdict: NO-GO** — but Arm A achieves first cross-gene generalization at real breadth.

---

## 7. Results

### 7.1 Intervention Ranking Fails Due to Measurement Noise

Paired within-decision outcome reliability is **0.239**, meaning ~76% of observed variance is measurement noise. By contrast, absolute per-sequence reliability on Moffatt is **0.8818**.

| Reliability context | Value |
|---|---:|
| Paired within-decision (v3) | 0.239 |
| Sequence-level, Moffatt | 0.8818 |
| Sequence-level, Mikl | 0.4527 |

**Interpretation:** Differencing two nearly identical sequences (mutant minus parent) cancels biological signal while compounding assay noise. Estimand E1 (paired intervention ranking) is therefore **unmeasurable** on current benchmarks regardless of model sophistication.

The leaky all-feature nonlinear ceiling (+0.0218 rank gain) barely exceeds the pre-registered gate (0.020), confirming that representation—not model class—is the bottleneck.

### 7.2 Absolute Localization Is Learnable Within Context

Mechanism-v4 demonstrates that **predicting absolute localization of unseen variants within a known 3′UTR context is strongly learnable**:

- auROC = **0.9503** (gate: ≥ 0.80) ✓
- Spearman ρ = **+0.799** (gate: ≥ 0.50) ✓
- Stable across 3 seeds (0.9503 / 0.9506 / 0.9504) and 5 folds (0.948–0.953)
- Shuffled-label null = 0.5006

This exceeds the published Mikl baseline (auROC 0.81–0.83) and represents the project's strongest **positive** result.

However, a 20-dimensional mononucleotide+dinucleotide baseline already achieves auROC **0.9306**. The full 1,364-dimensional k-mer model adds only **+0.0197**, failing the +0.030 composition gate. The composition baseline captures **~96%** of the primary model's lift above chance (0.9306 vs. 0.9503 primary, vs. 0.5006 shuffled null), so higher-order grammar contributes little.

### 7.3 Edit Direction Generalizes Across Genes but Is Composition-Dominated

Mechanism-v5 Arm A is the first evaluation of **cross-gene edit-direction transfer** at real parent breadth (166 genes):

| Metric | Primary model | AU-delta control | Random projection | Shuffled null |
|---|---:|---:|---:|---:|
| Mean auROC | **0.7051** | 0.6942 | **0.7094** | 0.5126 |
| Worst-fold auROC | **0.6423** | 0.6395 | 0.6571 | 0.4532 |
| Seed SD | 0.0000 | — | — | — |

Per-fold auROC: 0.698 / 0.689 / 0.755 / 0.741 / 0.642.

**Positive finding:** Edit direction generalizes across unseen genes at auROC 0.705, passing absolute gates a1 and a2.

**Limitation:** AU fraction change alone achieves 0.6942 (+0.0109 margin). A random projection of the same 84-dimensional delta space achieves **0.7094**, beating the real features. Gates a3 and a6 fail.

This is the **third independent reproduction** that composition nulls match or beat mechanism-aware features (v2 N4, v4 g2, v5 a3/a6).

### 7.4 Cross-Source Transfer Fails Due to Sign Instability

Mechanism-v5 Arm B tests the RNAddress construction: train absolute localization on Moffatt, predict f(mutant)−f(parent) on Mikl.

| Metric | Value | Gate |
|---|---:|---|
| Spearman ρ (Mikl) | +0.0298 | ≥ 0.100 ✗ |
| p-value | 0.0012 | < 0.001 ✗ |
| Confident-subset auROC | 0.5407 | ≥ 0.600 ✗ |
| AU-delta Spearman (Mikl) | **−0.1044** | — |

The Moffatt-trained model does not transfer edit-direction information to Mikl. Critically, **Mikl's own AU-delta correlation is negative (−0.1044)**, opposite to the published expectation that adding (AU)n repeats induces neurite localization (Mendonsa et al., 2023).

**Interpretation:** A universal zero-shot intervention selector requires a **sign-stable rule** across contexts. These assay sources do not provide one. Arm A succeeds on Mikl because a model **fit to Mikl** learns Mikl's sign; a rule **fit to Moffatt** does not carry over.

### 7.5 Summary of Gate Outcomes Across All Eras

| Era | Estimand | Key positive | Key limit | Verdict |
|---|---|---|---|---|
| FinalShot | Paired ranking | — | Historical NO-GO preserved | NO-GO |
| v2 | Paired ranking + nulls | Passes g1, g3, g6, g8 | Random k-mer beats primary | NO-GO |
| v3 | Grammar + nonlinear | Diagnostics clarify ceiling | Reliability 0.239 | NO-GO |
| v4 | Absolute localization | auROC 0.950 within-parent | Composition-dominated; T2 fails | NO-GO |
| v5 | Cross-gene + cross-source | auROC 0.705 cross-gene | AU-only; sign unstable | NO-GO |

**Universal zero-shot RNAddress is not supported.** Partial positives (within-context prediction, cross-gene edit direction) are real but composition-limited and non-transferable.

---

## 8. Discussion

### 8.1 Scientific Contribution

This work makes four contributions to computational biology and machine learning for genomics:

1. **A reproducible evaluation framework** for zero-shot RNA intervention selection with pre-registered gates, null controls, and write-once evidence—applicable to future MPRA benchmarks.

2. **A reliability metric** demonstrating that estimand choice (paired vs. absolute) determines feasibility before any modeling effort.

3. **Empirical proof that mechanism-aware features do not outperform composition nulls** for neuronal localization MPRAs, replicated across three independent experimental designs.

4. **Discovery of cross-assay sign instability** for AU-composition effects, explaining why universal transfer fails even when within-source prediction succeeds.

### 8.2 Relation to Published Literature

von Kügelgen et al. (2022) reported auROC 0.83 with 4-mers vs. 0.81 with RBP motifs—presaging our finding that simple composition features capture most signal. Mendonsa et al. (2023) identified (AU)n as a zipcode, consistent with our composition dominance—but our cross-source analysis shows the **sign** of AU effects is not consistent across assays, limiting universal application.

### 8.3 Why Higher-Capacity Models Failed

Mechanism-v4 showed 1,364 k-mer features transfer **0.055 auROC worse** than 20 composition features across genes. Mechanism-v5 pre-registered low-capacity models based on that finding, but they still failed to beat AU-delta. The pre-registered prediction that capacity was the issue was **wrong**: composition *is* the signal, so no capacity level can extract nonexistent higher-order grammar.

### 8.4 Limitations

1. **No wet-lab validation.** All results are computational re-analyses of published data.
2. **Moffatt breadth.** Only 10 genes limit cross-gene tests in v4; v5 addresses this with Mikl (166 genes) but with fewer confident labels (1,342).
3. **Sealed holdouts.** N-zip and Astrocyte data were not used; external confirmation remains open.
4. **Prior exposure.** Moffatt outcomes contributed to v2/v3 paired metrics; v4/v5 use new estimands but not pristine data.

### 8.5 Implications for RNA Therapeutic Design

Practitioners should not assume mechanism-aware models generalize zipcode rules across assays. Before deploying an intervention selector:

- Measure **outcome reliability** for the target estimand,
- Compare against **composition nulls**,
- Test **sign consistency** across biological contexts,
- Only then invest in complex feature engineering.

---

## 9. Conclusion

We asked whether zero-shot RNA intervention selection—predicting the best edit to improve localization for unseen biological parents—is achievable with mechanism-aware computational features. Across five pre-registered evaluation eras, 720 nested model fits, eleven null controls, and 143 automated tests, the answer is **no for universal zero-shot selection on current public benchmarks**, for measurable and reproducible reasons:

1. Paired intervention ranking is **unmeasurable** (reliability 0.239).
2. Absolute localization and edit direction **are predictable** (auROC up to 0.95 and 0.71).
3. Predictive signal is **AU composition**, not recoverable zipcode grammar.
4. Composition effect **sign is unstable across assay sources**, blocking universal transfer.

These results define necessary conditions—reliability, composition control, sign consistency—for any future RNAddress system. The open-source framework provided here enables rigorous testing as better-replicated MPRA benchmarks become available.

---

## 10. Future Work

1. **SEERS benchmark** (~2M synthetic 3′UTRs, nuclear/cytoplasmic readout): test whether higher replication resolves reliability limits (different biology).
2. **Wet-lab validation** of AU-delta predictions on designed editors (requires laboratory access).
3. **One-time holdout confirmation** on sealed Astrocyte data under a new pre-holdout freeze.
4. **Extension to RNA foundation models** (e.g., RNA-FM, gLM variant effect predictors) with the same null-control discipline.

---

## 11. Bibliography

Chekulaeva, M. (2024). Mechanistic insights into the basis of widespread RNA localization. *Nature Cell Biology*, 26(7), 1037–1046.

Fazal, F. M., et al. (2019). Atlas of subcellular RNA localization revealed by APEX-seq. *Cell*, 178(2), 473–490.

Mas-Ponte, D., et al. (2017). LncATLAS: a database of subcellular localization of long noncoding RNAs. *RNA*, 23(7), 1080–1087.

Mendonsa, S., von Kügelgen, N., Dantsuji, S., Ron, M., Breimann, L., Baranovskii, A., et al. (2023). Massively parallel identification of mRNA localization elements in primary cortical neurons. *Nature Neuroscience*, 26(3), 394–405.

Reilly, S. K., et al. (2021). Genome-wide functional screen of 3′UTR variants uncovers causal variants for human disease and evolution. *Cell*, 184(20), 5247–5260.

Lubelsky, Y., & Ulitsky, I. (2018). Sequences enriched in Alu repeats drive nuclear localization of long RNAs in human cells. *Nature*, 555(7694), 107–111. https://doi.org/10.1038/nature25757

Moffatt, K. C., et al. (2026). Robust mammalian RNA localization elements are complex and multipartite. *bioRxiv*. https://doi.org/10.64898/2026.06.09.731215

[Verify TDP-43 author list from PMC12864922 before submitting.] (2025). TDP-43 directly inhibits mRNA accumulation in neurites through modulation of mRNA stability. *Cell Reports* [confirm volume/pages from PMC12864922]. PMC12864922; GEO GSE288185.

von Kügelgen, N., et al. (2022). A massively parallel reporter assay reveals focused and broadly encoded RNA localization signals in neurons. *Nucleic Acids Research*, 50(12), 6876–6893. https://doi.org/10.1093/nar/gkac045

Wang, D., et al. (2021). RNALocate v2.0: an updated resource for RNA subcellular localization with increased coverage and annotation. *Nucleic Acids Research*, 50(D1), D001–D009.

Hingerl, L., et al. (2022). A sequence-based global map of regulatory activity for deciphering human genetics. *Nature Genetics*, 54(4), 440–449. https://doi.org/10.1038/s41588-022-01048-2

Ji, Y., et al. (2021). DNABERT: pre-trained bidirectional encoder representations from transformers model for DNA-language in genome. *Bioinformatics*, 37(15), 2112–2120. [Note: 3UTRBERT builds on similar BERT-for-RNA approaches; cite the specific 3UTRBERT preprint you used if available.]

Xue, J. R., et al. (2025). A systematic delineation of 3′UTR regulatory elements and their contextual associations (SEERS). *bioRxiv*. https://doi.org/10.1101/2025.06.09.658412

Zhang, T., et al. (2016). RNALocate: a resource for RNA subcellular localizations. *Nucleic Acids Research*, 45(D1), D135–D138. https://doi.org/10.1093/nar/gkw728

**Software and data:**

GitHub repository: JaivardhanSamadhiya/rnaexpress, branch `rnaddress-mechanism-v4`.

GEO accessions: GSE173098, GSE334718, GSE288185.

---

## 12. Acknowledgments

### 12.1 Author Contributions

**[YOUR FULL NAME]** — Sole author [OR: describe team roles if applicable]:

- Conceived the research question (zero-shot RNA intervention selection / RNAddress)
- Designed the five-era pre-registered evaluation framework and gate criteria
- Directed algorithm implementation across Mechanism-v2 through Mechanism-v5
- Performed diagnostic analyses (reliability decomposition, variance partitioning, sign-instability analysis)
- Interpreted results and wrote this research report
- Maintained the public Git repository with reproducible evidence records

[If team project, add each member:]

**[TEAM MEMBER 2 NAME]** — [Specific contributions: e.g., feature engineering, testing, figures, literature review]

**[TEAM MEMBER 3 NAME]** — [Specific contributions]

### 12.2 External Assistance

**[INSTRUCTOR/MENTOR NAME]** — [Describe role: e.g., guidance on experimental design, feedback on report drafts, school laboratory support. Adjust to truth.]

**Published dataset authors** — von Kügelgen et al. (GSE173098), Moffatt et al. (GSE334718), and TDP-43 study authors (GSE288185) generated the underlying MPRA data analyzed computationally in this work. No affiliation or endorsement is implied.

### 12.3 AI Tool Usage Disclosure

*(Required by St. Yau academic integrity policy.)*

| AI Tool | Version / Platform | Stages of Use | Purpose | Frequency / Timing |
|---|---|---|---|---|
| **Cursor IDE with Composer AI agent** | Cursor, 2026 | Research design, algorithm implementation, debugging, report drafting, literature search | Code generation for Python evaluation pipeline (`src/mechanism_v2` through `src/mechanism_v5`); automated test writing; diagnostic script execution; drafting and revising this research report; web search for related datasets and competition guidelines | Used extensively throughout the project (2025–September 2026), including during report preparation September 2026 |
| **[Other AI tools if used, e.g., ChatGPT, Claude]** | [Version] | [Stages] | [Purpose] | [Timing] |

**Declaration:** AI tools were used as programming and writing assistants. All research questions, hypotheses, pre-registered gate thresholds, scientific interpretations, and final conclusions were reviewed and approved by the author(s). AI-generated code was validated through 143 automated unit tests and manual inspection of evidence records. Chat logs and repository commit history are available as supporting materials under "Other Materials" upon request.

**Supporting materials submitted separately:**

- Git commit history (public repository)
- AI conversation transcripts [attach exported Cursor/agent logs]
- Executable test suite output (`results/mechanism_v*/tests.xml`)

---

## APPENDIX A — Suggested Figures for Final Submission

*(Include as numbered figures in the body when formatting the final PDF.)*

**Figure 1.** Outcome reliability comparison: paired within-decision (0.239) vs. absolute sequence-level (0.8818 Moffatt, 0.4527 Mikl).

**Figure 2.** Mechanism-v4 within-parent absolute localization: auROC 0.950 (primary) vs. 0.931 (composition control) vs. 0.501 (shuffled null).

**Figure 3.** Mechanism-v5 cross-gene edit direction: auROC 0.705 (primary) vs. 0.694 (AU-delta) vs. 0.709 (random projection) across 166 genes.

**Figure 4.** Cross-source sign instability: AU-delta Spearman on Mikl (−0.104) vs. Moffatt-trained transfer Spearman (+0.030).

**Figure 5.** Five-era evaluation timeline with estimand, key metric, and verdict for each era.

---

## APPENDIX B — Guideline Compliance Audit (verified September 2026)

| St. Yau requirement | Status | Notes |
|---|---|---|
| Cover page (name, school, location, instructor, title) | ⚠ Placeholders | Fill before PDF export |
| Title, Author, Abstract, Keywords, TOC, Body | ✓ | Present |
| Bibliography on separate page | ⚠ Formatting | Start `\newpage` or page break before §11 in Word/LaTeX |
| Acknowledgments with member contributions | ⚠ Placeholders | Remove team rows if solo project |
| AI usage disclosure with tool names, stages, purpose | ✓ Template | Complete table; attach chat logs |
| CS disciplinary relevance | ✓ | Algorithm + computational biology |
| Theoretical/practical significance | ✓ | Defines limits of zero-shot intervention selection |
| Original question + clear working process | ✓ | Five frozen eras documented |
| Algorithm implementation details | ✓ | §5 + repository |
| Detailed experiment results | ✓ | §6–7 with numeric evidence |
| Source code / executable proof | ⚠ Submit separately | Link GitHub + test XML in "Other Materials" |
| Teamwork (if team) | N/A or ⚠ | State solo or fill team roles |
| Academic norms / citations for non-original work | ⚠ Mostly ✓ | See citation fixes in Appendix C |
| Video (advised) | Optional | 5–10 min defense walkthrough recommended |

**Category:** Computer Science — Computational Award is **correct** for this project.

---

## APPENDIX C — Citation and Number Corrections Applied

1. **Segal et al. 2018** was incorrect; SIRLOIN/NucLib is **Lubelsky & Ulitsky (2018), *Nature***.
2. **Moffatt GSE334718** now cited (bioRxiv 2026, DOI 10.64898/2026.06.09.731215).
3. **TDP-43 GSE288185** entry added with PMC12864922 — **verify full author list** from the paper before submitting.
4. **Feature dimensions:** 606 mechanism columns + 540 random k-mer (ceiling) = 1,146 total.
5. **"93%" composition claim** corrected to **~96%** of lift above chance (more accurate arithmetic).

---

## APPENDIX D — Formatting Checklist Before Submission

- [ ] Replace all `[BRACKETED PLACEHOLDERS]` with your information
- [ ] Rewrite in your own words (required by you; recommended by competition)
- [ ] Verify page limit for St. Yau Computational Award category
- [ ] Export AI chat logs for "Other Materials"
- [ ] Include link to GitHub repository in submission
- [ ] Optional: 5–10 minute oral defense video walking through Figures 1–4
- [ ] Confirm category: **Computer Science — Computational Award** ✓ (appropriate for computational biology / bioinformatics with algorithm implementation and rigorous experiments)

---

*End of draft report. Total length: suitable for expansion or trimming to competition page limits.*
