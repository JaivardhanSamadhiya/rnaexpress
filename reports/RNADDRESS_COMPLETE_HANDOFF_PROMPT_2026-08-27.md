# RNAddress complete project handoff prompt

Copy everything in this document into a new ChatGPT/Codex conversation when transferring the project. Treat it as context and operating instructions, not as permission to weaken any scientific gate.

---

## Your role

You are taking over RNAddress as its computational research engineer, bioinformatics researcher, statistician, algorithm designer, software engineer, literature reviewer, skeptical peer reviewer, and reproducibility lead. Work autonomously and persistently, but preserve scientific integrity. Search deeply for alternative public data and legitimate methods when blocked. Never invent unavailable data, tune against a revealed lock and call it validation, silently change a frozen gate, or open a sealed outcome merely to keep the project moving.

The governing principle is **truth over desired result**. A rigorous NO-GO is preferable to a polished but incremental or invalid project. Strong baselines, intervention-level ground truth, parent/gene-held-out testing, external validation, reproducibility, and honest failure reporting take priority over model complexity or UI work.

## Project identity and goal

- Name: **RNAddress — A Computational Compiler for Sequence-Level RNA Localization**.
- Repository: `D:\rnaexpress`.
- Current branch: `rnaddress-v2-rescue`.
- Latest scientific-results commit: `cf98954` (`record failed TDP-43 locked gate`).
- Handoff date: 2026-08-27.
- Competition deadline in the original specification: 2026-09-15.
- Target: determine whether RNAddress can credibly approach the 2025 PV-Care project’s overall level for the 2026 S.-T. Yau High School Science Award, Computer Science category.
- Constraint: completely remote/computational; no required wet-lab work; central data and ground truth must be publicly available or legitimately reconstructable.

RNAddress addresses the inverse problem:

> Given an existing RNA regulatory sequence, a requested localization change, an edit budget, and protected molecular-property constraints, rank the smallest sequence interventions predicted to redirect localization.

The intended flagship task is one-nucleotide editing of a held-out RNA parent: enumerate every assayed SNV, rank candidates separately for increasing and decreasing localization, and compare the recommendation with experimentally measured outcomes. Forward localization prediction is supporting infrastructure and a mandatory baseline, not the central contribution.

The strongest desired claim would have been that RNAddress translates a requested RNA-localization change into minimal cis-sequence edits, beats strong forward-model exhaustive search on unseen parents, and transfers to an independent in-vivo astrocyte assay while preserving expression/translation-related properties. **That claim has not been earned.**

## Novelty position

The defensible novelty is the biological operation and validation framework: target-conditioned minimal cis-sequence intervention under constraints, evaluated against measured intervention landscapes. Do not claim that RNAddress is the first system to engineer localization, the first RNA-localization predictor, or the first use of ML in RNA design.

Important collisions:

- CRISPR-TO and PULR can reposition RNA through trans-acting systems, but do not solve minimal cis-sequence rewriting.
- Artificial zipcodes and synthetic localization elements predate RNAddress.
- N-zip, mutREL-seq, Mikl, the TDP-43 MPRA, SRLE-seq, and Astrocyte SN-MPRA experimentally map localization elements/interventions but do not provide the complete requested-destination-to-minimal-edit compiler.
- RNA-GPS, DM3Loc, DeepLocRNA, RNALoc-LM and similar systems solve forward localization prediction.
- Designed nuclear-speckle localization logic is the closest sequence-engineering collision but is not a general held-out minimal-edit intervention system.
- Patents cover artificial zipcodes and trans-acting localization systems, so broad “first” language is prohibited.

The Phase A–E hostile audit assigned novelty 8.0/10 and potential PV-Care-style capability novelty 8.3/10, conditional on empirical success. No stop-rule collision was found. See `reports/novelty_audit.md` and `reports/phase_A_E_report.md`.

## Public datasets and exact reconstructed ground truth

### 1. N-zip primary cortical-neuron mutagenesis

- Study: *Massively parallel identification of mRNA localization elements in primary cortical neurons*.
- Accessions: E-MTAB-10902, E-MTAB-11572, E-MTAB-11575.
- Central workbook: `41593_2022_1243_MOESM2_ESM.xlsx`.
- Workbook SHA-256: `15560b562c86c3d8fea8611154c4b0504a9528051b6038c19ff96bb47cd9fec9`.
- Initial library: 4,813 tiles.
- Mutagenesis library: 6,266 constructs comprising 20 WT, 4,695 SNVs, 783 two-nucleotide windows, 313 five-nucleotide windows, 179 ten-nucleotide windows, 106 deletions, 102 targeted mutations and 68 scrambles.
- Sixteen designed parents have exhaustive three-alternative SNV coverage, but two sequence-distinct `Cflar_2` parents share the outcome table’s remaining identity because the source tile ID is omitted.
- The project quarantined all 300 ambiguous `Cflar_2` SNVs rather than assigning them by row order.
- Truth-safe benchmark: **4,395 exact SNVs across 15 parents**, spanning 1,465 positions, with all three alternate alleles at every retained position. Parent lengths are 85, 90 or 100 nt.
- Outcome: WT and mutant primary-neuron neurite/soma localization log2 ratio.
- No safe construct-matched expression, stability, translation or ribosome-occupancy property is available for the central SNV task.
- Main processed source: `data/processed/nzip_snv_intervention_pairs.csv.gz`.

This was the primary single-nucleotide intervention benchmark. Its original 12-development/3-lock split has been spent. All 15 parents are now development data only.

### 2. Mikl neuronal MPRA / GSE173098

- Study: *A massively parallel reporter assay reveals focused and broadly encoded RNA localization signals in neurons*.
- 47,989 raw count rows and 47,347 analyzed constructs.
- Truth-safe motif-replacement reconstruction: **11,926 equal-length multi-base intervention pairs across 6,104 parent sequences**, all 198 nt.
- Excluded 213 ambiguous-parent and 770 missing-parent mutant rows.
- Outcomes: CAD and Neuro-2a neurite/soma localization; ActD stability at 4 h and 24 h.
- These are multi-base motif replacements, not SNVs, and cannot be treated as homogeneous with N-zip.
- Main processed source: `data/processed/mikl_motif_replacement_pairs.csv.gz`.

For v2.4/v2.5 external pretraining, a stricter natural-tile cohort was constructed. The exact paper cohort with >500 reads in both CAD and N2A and deduplication contains 36,731 rows. Global exclusion of every N-zip gene leaves **35,428 sequences from 304 genes**, with zero exact N-zip 31-mer overlap. A smaller v2.4 natural-tile cohort contains 13,309 rows after global N-zip-gene exclusion and also has no exact 31-mer overlap.

### 3. Arora/Taliaferro neuronal MPRA / GSE183192

- Study: *High-throughput identification of RNA localization elements in neuronal cells*.
- Source contains 7,374 labeled FASTA records plus 750 unlabeled 260-nt controls.
- 7,360 result IDs map one-to-one to labeled 260-nt inserts.
- **7,115 constructs** have complete measurements in all four assay heads.
- Supplementary table mapping verified from the source PDF: S1 GFP/CAD, S2 firefly/CAD, S3 GFP/N2A, S4 firefly/N2A.
- There is zero gene overlap, complete-parent containment, or exact shared 31-mer with N-zip.
- This is suitable for forward representation/pretraining, not explicit minimal-edit validation.
- Primary source PDF retained at `data/raw/arora_gse183192/supplementary/files/Supplement_NAR_Revision.pdf`.

### 4. TDP-43 neurite/soma MPRA

- Study: *TDP-43 directly inhibits mRNA accumulation in neurites through modulation of mRNA stability*.
- Natural reporter windows are 260 nt from 16 mouse genes.
- Every oligo containing canonical TDP-43 motifs `GTGTG`, `TGTGT` or `GTATG` has a companion construct complementing all covered motif bases.
- Reconstruction used the public design code, Gencode vM17, mm10 sequence and source workbook.
- Recovered 7,389 natural oligo identifiers and **4,566 exact parent/mutant/effect tuples across 16 genes**.
- All 4,566 mutation ranges exactly match ranges encoded in published identifiers; no design mismatch required quarantine.
- These are multi-base motif-complement interventions, not SNVs.
- Full processed source: `data/processed/tdp43_motif_intervention_pairs.csv.gz`.
- Development source: `data/processed/tdp43_v2_development_pairs.csv.gz`.
- Outcome-free locked features: `data/frozen/tdp43_v2_locked_features.csv.gz`.
- Locked outcomes: `data/frozen/outcomes/tdp43_v2_locked_outcomes.csv.gz`.

Before v2 fitting, genes were divided into construct-count quartiles; one gene per quartile was selected outcome-blindly by SHA-256 of `rnaddress-v2-lock-2026-08-26|gene_id`.

- Development: 3,560 interventions from 12 genes.
- Lock: 1,006 interventions from Fam160b2 (246), Lars2 (85), Diras1 (278) and Synj2bp (397).
- Development SHA-256: `a150d5f665a11522ff89c29f2739ace206dad8521cc023385596de3f99bc9ac8`.
- Locked-feature SHA-256: `2678052892e47459363130f645d784287fb418931bec3c677d9bcee92420ae53`.
- Locked-outcome SHA-256: `69842a7174e81d3d6adf87a075c66817ce5c2cb59f0bb58bb627eecf741d7a2e`.

The TDP-43 lock has now been spent and failed its complete gate. It may be used only for explicitly post-lock development/diagnosis in a future cycle; it can never again be called untouched confirmation.

### 5. Astrocyte SN-MPRA / GSE330741

- Study: *In Vivo Massively Parallel Reporter Assay Reveals Sequence Determinants of mRNA Localization in Astrocytes*.
- Lab/context: Dougherty Lab, AAV-delivered reporters in adult mouse astrocytes in living brain.
- Library: 4,769 constructs, seven controls, eight biological parent groups, 209 WT-type constructs, and eight selected 190-nt mutagenesis parents.
- Reconstructed external benchmark: **4,553 exact SNVs across eight parents and 1,520 positions**. Of these positions, 1,513 have all three alternate alleles and seven have two, so seven of 4,560 possible substitutions are absent.
- Every SNV has localization (`snin_ctxin_logFC`), ribosome occupancy (`ctxtrap_ctxin_logFC`) and local translation (`paptrap_ctxtrap_logFC`). Expression can be derived from RNA/DNA replicate counts; there is no explicit S8 expression-effect field. Stability is absent.
- There is zero exact parent or gene overlap with N-zip.
- Outcome-free features and complete outcomes were separately frozen.
- Three result rows were accidentally printed during initial schema discovery before quarantine. No aggregate distribution, ranking, threshold or model result was viewed. This must remain disclosed; the benchmark is outcome-blinded after freeze but not perfectly never-seen.

**Current non-negotiable status: all Astrocyte outcome fields remain sealed and must not be read.** The frozen v2 protocol required the TDP-43 gate to pass before Astrocyte prediction/reveal. It did not pass. No Astrocyte prediction freeze or outcome reveal is authorized under v2.

### 6. SRLE-seq / HRA016642

- All 4,096 six-mers in a fixed reporter backbone are available for nuclear retention/export analysis.
- This is a fixed-backbone gain-of-function motif screen, not unseen-parent minimal-edit transfer.
- It can provide secondary framework evidence only and cannot replace the failed parent-held-out external validation.

## Evaluation formulation and metrics

For every held-out parent/gene, rankings are evaluated separately for requested increase and requested decrease. For direction sign `s` in `{+1,-1}`, measured utility is `s * delta_localization` and predicted utility is `s * predicted_effect`. The top predicted candidate is compared with all experimentally assayed candidates.

Primary metric: selected experimental rank percentile, averaged over increase/decrease within parent/gene and then macro-averaged across parent/gene units. Random expectation is exactly 0.5.

Other metrics:

- normalized regret: distance from experimentally best utility divided by the observed utility range;
- raw regret;
- within-parent/gene Spearman correlation;
- Success@1/3/5 and Precision@1/3/5 where a development-only threshold exists;
- exact random expectations;
- parent/gene-level bootstrap differences, never treating individual variants as independent units.

The fixed development threshold for the original N-zip binary metrics was 0.6758642587586807 log2 localization units. Continuous rank percentile and regret are primary because positive/negative effects are asymmetric.

Mandatory comparators include random, substitution means, motif heuristics, retrieval/local models, metadata and GC shortcuts, and a strong absolute forward model followed by exhaustive intervention scoring. A custom inverse method is not useful merely because it beats chance; it must beat the strongest generic forward-search and shortcut baselines across multiple held-out groups.

## Original v1 development and lock

The original preregistration retained 12 N-zip development parents and three untouched locked parents.

### Development

Across 3,540 development SNVs, strict outer leave-one-parent-out results were:

- linear pairwise ranker: rank percentile 0.636, normalized regret 0.452, Spearman 0.186;
- retrieval: 0.561, 0.492, 0.127;
- forward ExtraTrees exhaustive search: 0.521, 0.490, 0.135;
- joint N-zip+Mikl: 0.572;
- motif delta: 0.471;
- Mikl-only transfer: 0.456.

The pairwise model’s gain intervals crossed zero and Success@K did not dominate retrieval, so development was promising rather than confirmatory.

### Frozen lock

- Locked rows: 855 SNVs from Cdc42_2, Ndufa2 and Cflar_1.
- Freeze commit: `46a78dec1a4f654c6b0ea3bcbcf11d301bd8e046`.
- Frozen prediction SHA-256: `3b1fb0d494052fa6001615c3cbc257ff627e3464454457c846ab6cb153d37ad8`.
- Frozen model SHA-256: `fbe9a46c6f8ca722382a6f35d2b0804d4e2ef47f49d869609ff70e1a17f5d337`.

Locked result:

- pairwise ranker: rank percentile 0.566, normalized regret 0.480, Spearman 0.049;
- forward ExtraTrees: 0.624, 0.421, 0.094;
- retrieval: 0.279;
- exact random: 0.500.

The original internal gate **failed** because the custom pairwise ranker lost to forward exhaustive search. This result is permanent.

### Root defect

The v1 pairwise learner was linear on differences of intervention features. Unchanged parent features cancel exactly when comparing two edits from the same parent. The model could learn substitution, position and local-context rules but could not learn that the same edit should act differently in different parent contexts. This motivated explicit parent-by-edit interactions in v2.

The post-lock descriptive 15-parent audit found pairwise 0.622, forward 0.542, metadata 0.612, GC 0.594 and shuffled-edit 0.528, but this cannot rescue the original failed lock. The original frozen scorecard was 53/100 and NO-GO for PV-Care comparability.

## V2 rescue architecture and chronology

All 15 N-zip parents became development-only after the original lock was spent. A new independent TDP-43 gene lock was created before v2 fitting. Astrocyte outcomes remained sealed.

### Initial factorized context models

The core corrective form was:

`score(parent, edit) = additive(edit) + parent_embedding' * W * edit_embedding + residual(parent, edit)`.

A fixed-center factorized ranker scored 0.662 versus metadata 0.612 and forward LightGBM 0.560, while shuffled edit scored 0.509. However, the fully nested grouped-selection version scored only 0.588 and failed. The favorable fixed seed was not accepted as confirmatory.

Additional prespecified attempts:

- ViennaRNA structure-augmented factorized ranker: 0.539; generic MFE/ensemble/accessibility summaries hurt selection and were dropped from the main N-zip model.
- TDP-43 development multitask auxiliary ranker: 0.504; negative transfer and dropped.
- v2.1 seven-seed ensemble: 0.575; individual seeds ranged 0.551–0.662, demonstrating optimization instability. Failed absolute, forward-margin, metadata-margin and robustness checks.
- v2.2 SpliceBERT contextual-delta Ridge: 0.616730, normalized regret 0.4362, Spearman 0.1944. It passed forward and parent-robustness checks but failed the 0.630 absolute threshold and achieved only +0.004 over metadata instead of +0.020.
- v2.3 extreme-contrast SpliceBERT Ridge: 0.581; rejected.
- v2.4 external-localization PCA stack: 0.562; rejected.
- v2.5 calibrated Mikl XGBoost deltas: 0.620807; close but failed absolute threshold, metadata margin (+0.0084), and improvement in 9/15 parents.

### External source models

V2.4 trained decontaminated assay-specific SpliceBERT/Ridge heads:

- Mikl two-head held-gene macro Spearman 0.200311;
- Arora four-head held-gene macro Spearman 0.140394;
- both selected alpha 10,000;
- frozen in `data/frozen/v2_4_external_forward_heads.npz` and its JSON manifest.

V2.5 reconstructed the published Mikl 4-mer XGBoost formulation on 35,428 decontaminated sequences from 304 genes. Frozen settings: maximum depth 3, minimum child weight 1, learning rate 0.03, 500 trees. Gene-held-out auROC was 0.774603 for neurite and 0.732797 for soma, mean 0.753700.

- Neurite model SHA-256: `b7df2c9dd92110afd0a12cb0422c2b4d94bd9d2c5a1cac6920863304aa7f13558`.
- Soma model SHA-256: `9fc23ef557bf9913e694af37c41a37f2394d9b1f52d13f34acaed08fff069ed2a`.

Zero-shot Mikl probability deltas scored only 0.492 on N-zip, but calibrated deltas contained complementary development signal.

## V2.6 selected development method

V2.6 combined the two complementary, previously frozen feature routes in a strict nested stack called `nested_context_external_stack`.

### Contextual base

- Frozen N-zip feature matrix: 4,395 × 2,638.
- SHA-256: `eeaca4d2c7362877755e850a8bc08fa3e3088c64ffd69fadff72ef409c165e74`.
- Representation: official frozen `SpliceBERT.1024nt` mutant-minus-parent pooling of CLS delta, global nucleotide-mean delta, changed-nucleotide mean delta, and radius-10 changed-window mean delta (4 × 512 = 2,048), followed by the unchanged 590-dimensional v2 edit feature vector.
- StandardScaler fitted only on the training fold.
- Ridge alpha fixed to feature dimension 2,638.
- Target: empirical localization-effect percentile within parent.

### Low-dimensional block

- 18 metadata features: one-hot 16 reference→alternate substitution identities, relative edit position, and parent length divided by 100.
- Two frozen Mikl XGBoost probability deltas: mutant minus parent for neurite and soma classifiers.
- Total low-dimensional features: 20.

### Nested stacking

For every outer held-out N-zip parent, the contextual score for all meta-training rows was generated by inner leave-one-parent-out fits using only the other outer-training parents. The outer parent received a contextual score from a contextual Ridge fit on all outer-training parents. A StandardScaler + Ridge meta-model with alpha fixed at 21 consumed the 20 low-dimensional features plus the one contextual score. This prevented in-sample contextual predictions from leaking into meta-training.

### Frozen v2.6 gate

The candidate had to satisfy all of:

1. macro directional rank percentile ≥0.630;
2. gain over strongest forward-search baseline ≥0.030;
3. gain over metadata ≥0.020;
4. improvement over forward on at least 9/15 parents;
5. positive mean gain after removing the two most favorable parents;
6. shuffled edit identity ≤0.540;
7. full nested shuffled-label control ≤0.530.

### V2.6 results

- nested stack: rank percentile **0.635752**, normalized regret 0.427252, Spearman 0.199919;
- Mikl XGBoost calibrated: 0.620807;
- SpliceBERT percentile Ridge: 0.616730;
- metadata only: 0.612369;
- forward LightGBM: 0.560352;
- forward ExtraTrees: 0.541662;
- shuffled edit: 0.497102;
- full nested shuffled-label control: 0.507164.

The candidate gained +0.075400 over forward LightGBM and +0.023383 over metadata, improved at least 9/15 parents, and remained positive after removing the two most favorable parents. **All seven v2.6 development checks passed.**

Important interpretation: this is a strong nested development result across 15 already-development parents, not a new N-zip lock. The original three-parent failure remains historical fact. The higher 0.662 fixed-seed factorized result is not admissible as the selected method because its nested/seed-stability checks failed.

Relevant commits:

- `efa91d2`: freeze v2.6 nested stack gate;
- `9206939`: implement frozen v2.6 nested stack;
- `e5f055f`: record v2.6 pass and freeze TDP-43 prediction protocol.

## TDP-43 prediction freeze

The v2.6 pass authorized only the TDP-43 lock—not Astrocyte reveal. The architecture was refit without tuning on the 12 permitted TDP-43 development genes.

Because every TDP-43 intervention has its own 260-nt parent oligo, ranking and cross-fitting groups were `gene_id`. The target was empirical delta-localization percentile within development gene. Gene identity was never a feature.

The generalized metadata mapping for multi-base interventions was frozen as:

- 16 normalized reference→alternate substitution counts across all changed positions;
- mean changed-position fraction;
- sequence length divided by 100.

This mapping reproduces the N-zip 18-feature SNV vector exactly for a single-base edit.

The contextual component remained 2,638-dimensional and used strict leave-one-development-gene-out scores for meta-training. The final contextual and meta models were then fit on all 12 development genes to score the four locked genes.

Frozen comparators:

1. Same-assay absolute-sequence LightGBM trained on permitted TDP-43 parent and mutant localization values, prediction `f(mutant)-f(parent)`, with 300 trees, learning rate 0.03, 15 leaves, minimum child samples 30, L2 1, column fraction 0.7 and seed 20260826.
2. A 22-feature motif/accessibility Ridge with 12 fixed motif/composition deltas and 10 ViennaRNA 2.7.2 structure/accessibility values, alpha 22. No CLIP label or gene ID was used.

All 4,566 TDP-43 parent/mutant pairs received identical outcome-blind contextual processing. ViennaRNA folded 9,132 unique parent/mutant sequences. The complete 1,006-row lock prediction artifact, model parameters, LightGBM model, environment, code hashes and cache hashes were frozen before reveal.

- Pre-freeze code commit: `e5f055fbcd3dafc1afaf6971af87ba154ff2e761`.
- Prediction freeze commit: `c7f83fe`.
- Frozen prediction SHA-256: `96d6cba1e0da27c108f7962007a5d02971f13008cc35d22e4934dc7b093ab7e2`.
- Custom model SHA-256: `2aeabff816597da8ec6abb9989ceed9dee4ebb745505a007d5293ff6c29cbd6e`.
- Forward LightGBM SHA-256: `b526316507e85a082d71337af4ff4ec317e01fb0a3d909f1c899b1f97bcef2dd`.
- Motif/accessibility model SHA-256: `1e19fa8d8354d963e3ba8f5bccd6cbe4666f3652e6c256beb1a69381bf59154f`.
- Context cache SHA-256: `3600ea38fdced6de8ed913790b7342e2d8045439f6689f542aec71f4e5476c99`.
- Structure cache SHA-256: `b3e95c74e5a8e0d14b2b46525ac7d9be16b6bd603e6249379b9b0a253f087b54`.
- Environment hash: `0331cedade27b08290ab8b14a4415cd598e55035ea3b16f0d08986165df4ddd8`.
- Evaluator frozen at commit `3bd2fc9` before outcomes were read.

## TDP-43 locked result

The frozen gate required all of:

1. custom macro directional rank percentile >0.550;
2. positive gain over forward LightGBM;
3. positive gain over motif/accessibility Ridge;
4. positive within-gene Spearman for at least 3/4 locked genes;
5. positive custom-minus-strongest-comparator mean rank gain after removing the single most favorable locked gene, operationalizing the requirement that no single gene account for the entire aggregate advantage.

Aggregate result:

- nested contextual/external stack: rank percentile **0.674923**, normalized regret 0.376574, Spearman 0.292211;
- forward LightGBM: 0.619682, normalized regret 0.293838, Spearman 0.294999;
- motif/accessibility Ridge: 0.544052, normalized regret 0.374199, Spearman 0.321641.

The custom method beat forward by +0.055242 and motif/accessibility by +0.130871. It passed the absolute metric and both baseline comparisons. It also had positive Spearman in three genes:

- Fam160b2: +0.697883;
- Lars2: -0.169181;
- Diras1: +0.603747;
- Synj2bp: +0.036396.

Custom-minus-forward directional rank gains by gene were:

- Fam160b2: -0.061224;
- Lars2: -0.136905;
- Diras1: +0.117329;
- Synj2bp: +0.301768.

Removing the most favorable gene, Synj2bp, leaves mean gain approximately -0.0269. Therefore the fifth robustness check **failed**. The complete TDP-43 locked gate is a formal **FAIL**, despite passing four of five checks and showing a strong aggregate result.

The custom method’s normalized regret was also worse than forward LightGBM, and its macro Spearman was slightly below both comparators; these secondary weaknesses must not be hidden.

- Results commit: `cf98954`.
- Authoritative report: `reports/tdp43_v2_locked_gate_results.md`.
- Machine gate: `results/v2_tdp43_lock/tdp43_v2_lock_gate.json`.

## Current scientific verdict

RNAddress is **not currently PV-Care-comparable and does not have an earned global-gold claim**.

What is genuinely strong:

- a clear and potentially novel inverse biological operation;
- unusually careful public-data reconstruction and provenance;
- 4,395 exact exhaustive N-zip SNVs and 4,566 TDP-43 interventions;
- leakage-safe group-held-out evaluation;
- strong mandatory forward-search and shortcut baselines;
- an outcome-blind committed freeze with code/model/environment/data hashes;
- v2.6’s complete nested N-zip development-gate pass;
- a TDP-43 aggregate result of 0.6749 that beats both frozen comparators;
- honest control experiments and preserved failures.

What blocks the target claim:

- the original N-zip custom model lost to forward search on its untouched lock;
- all 15 N-zip parents are now development data;
- the TDP-43 lock failed its anti-concentration robustness check and is now spent;
- TDP-43 interventions are multi-base motif complements, not independent SNV validation;
- the only untouched independent SNV benchmark is Astrocyte SN-MPRA, but v2 does not authorize opening it;
- no external Astrocyte transfer, protected-property/Pareto result, end-to-end compiler, or user-facing demonstration has been validated;
- parent/gene-level sample sizes are small and heterogeneity is material;
- no new independent public intervention set has yet been found.

The original frozen scorecard was 53/100 after v1. V2 materially improves development and auxiliary aggregate evidence, but because its required validation gate failed and external reveal remains prohibited, do not invent a revised PV-Care-level score without a new frozen scoring exercise. The qualitative verdict remains NO-GO for the original competition claim.

## Outcome-lock rules from this point forward

1. **Do not read any Astrocyte outcome file or result column.** The current protocol does not authorize it.
2. Do not modify a model using the revealed TDP-43 lock and present a new result on those same four genes as validation. Any such analysis is explicitly post-lock development.
3. Do not reinterpret the TDP gate by weakening or removing the failed robustness rule.
4. Do not claim the original N-zip lock was rescued; it remains failed.
5. Do not call the v2.6 15-parent result independent confirmation; it is nested development evidence.
6. Do not merge SNV and multi-base intervention datasets as though they share one homogeneous task.
7. Do not build a polished “successful compiler” whose central claims exceed the evidence.
8. Do preserve all negative results and deviations.

## Latest external-data search

After the TDP failure, a new search for 2024–2026 RNA-localization MPRAs, saturation mutagenesis and public GEO resources found no clearly independent held-out localization-intervention landscape beyond the already-reserved datasets. GSE330741 is the Astrocyte SN-MPRA already in quarantine, not a new validation set. Known N-zip, Mikl, Arora, TDP-43 and SRLE-seq resources are already incorporated or correctly limited. Continue searching if useful, but do not relabel a forward-only or fixed-backbone dataset as independent minimal-edit validation.

## Legitimate next paths

### Path A: find a genuinely new independent validation set

Search recent literature, preprints, GEO, SRA, ENA, BioStudies, ArrayExpress, Zenodo, Dryad, Figshare, institutional repositories, GitHub and supplementary archives for a localization assay containing exact parent sequences, sequence interventions, mutant sequences and localization outcomes. A new lock must be selected and frozen before using any of its outcomes for model choice. Prefer multiple natural parents/genes, exhaustive or broad intervention coverage, and a lab/assay distinct from N-zip/TDP-43.

### Path B: prospectively obtain computationally public evidence

If a newly released dataset appears before the deadline, preregister and freeze the selected method before downloading/reading its outcomes where feasible. The current v2.6/TDP evidence can select the architecture, but no tuning may occur on the new lock.

### Path C: explicitly reposition the project

If no independent validation exists, RNAddress may become a rigorous benchmark/negative-result project about the difficulty and context specificity of RNA-localization intervention ranking. That could include reproducible reconstruction, leakage analysis, baseline dominance, editability heterogeneity and failure modes. This is scientifically useful but is not equivalent to the requested PV-Care-level compiler.

### Path D: new post-lock development cycle

The revealed TDP genes may be incorporated into clearly labeled post-lock development to study why Lars2/Fam160b2 differ from Diras1/Synj2bp. Candidate diagnostics include distribution shift, motif multiplicity, edited-base count, parent localization range, structural accessibility, CLIP overlap and model disagreement. However, any method developed this way requires another untouched validation set. Astrocyte outcomes cannot serve as an authorized v2 reveal; a new preregistration would need to justify any future use without falsely claiming the failed gate passed.

### Path E: update project-facing documentation

`README.md`, `PROJECT_LOG.md`, `reports/frozen_scorecard.md`, and `reports/pvcare_comparison.md` currently stop at the original v1 failure. They are historically accurate but operationally stale. Update them to include v2.6 and the TDP lock while preserving the older failure. Do not delete or rewrite history.

## Key files

Scientific governance and reports:

- `reports/novelty_audit.md`
- `reports/phase_A_E_report.md`
- `reports/preregistration.md`
- `reports/preregistration_deviations.md`
- `reports/locked_internal_results.md`
- `reports/hostile_internal_audit.md`
- `reports/frozen_scorecard.md`
- `reports/v2_rescue_preregistration.md`
- `reports/v2_preregistration_deviations.md`
- `reports/v2_data_and_literature_audit.md`
- `reports/v2_fixed_center_screen.md`
- `reports/v2_nested_development_results.md`
- `reports/v2_structure_screen.md`
- `reports/v2_tdp_aux_screen.md`
- `reports/v2_1_stability_results.md`
- `reports/v2_2_splicebert_results.md`
- `reports/v2_3_extreme_contrast_results.md`
- `reports/v2_4_external_forward_audit.md`
- `reports/v2_4_external_pretraining_results.md`
- `reports/v2_4_external_transfer_results.md`
- `reports/v2_5_mikl_xgboost_pretraining_results.md`
- `reports/v2_5_mikl_xgboost_transfer_results.md`
- `reports/v2_6_nested_context_external_stack_preregistration.md`
- `reports/v2_6_nested_context_external_stack_results.md`
- `reports/tdp43_v2_prediction_freeze_protocol.md`
- `reports/tdp43_v2_locked_gate_results.md`

Core current code:

- `src/analysis/run_v2_6_nested_context_external_stack.py`
- `src/analysis/freeze_tdp43_v2_predictions.py`
- `src/analysis/evaluate_tdp43_v2_lock.py`
- `src/modeling/splicebert_features.py`
- `src/modeling/v2_features.py`
- `src/modeling/v2_structure.py`
- `src/modeling/mikl_xgboost_heads.py`
- `src/modeling/v2_models.py`
- `src/modeling/metrics.py`

Frozen/result artifacts:

- `results/v2_6/nzip_nested_stack_predictions.csv.gz`
- `results/v2_6/nzip_nested_stack_metrics.csv`
- `results/v2_6/nzip_nested_stack_macro.csv`
- `results/v2_6/nzip_nested_stack_gate.json`
- `results/v2_tdp43_lock/tdp43_v2_frozen_predictions.csv.gz`
- `results/v2_tdp43_lock/tdp43_v2_custom_stack.npz`
- `results/v2_tdp43_lock/tdp43_v2_forward_lightgbm.txt`
- `results/v2_tdp43_lock/tdp43_v2_motif_accessibility_ridge.npz`
- `results/v2_tdp43_lock/environment_pip_freeze.txt`
- `results/v2_tdp43_lock/tdp43_v2_prediction_freeze_manifest.json`
- `results/v2_tdp43_lock/tdp43_v2_revealed_predictions.csv.gz`
- `results/v2_tdp43_lock/tdp43_v2_lock_gene_direction_metrics.csv`
- `results/v2_tdp43_lock/tdp43_v2_lock_macro.csv`
- `results/v2_tdp43_lock/tdp43_v2_lock_gate.json`

## Reproducibility and implementation notes

- Primary random seed: 20260826.
- Local machine observed: Intel i7-1165G7, 4 cores/8 threads, approximately 15.7 GiB RAM, no detected NVIDIA GPU.
- ViennaRNA version used: 2.7.2.
- SpliceBERT checkpoint hash is verified in code before inference.
- A Windows native-runtime collision requires ViennaRNA to import before scikit-learn/LightGBM in the combined TDP freeze process.
- TDP SpliceBERT processing uses a pair-batched implementation that is mathematically identical to the original pooling but avoids one model invocation per unique parent.
- Structure cache is keyed by exact sequence SHA-256.
- The test suite currently passes: **16 tests passed** on 2026-08-27.
- The worktree was clean before this handoff document was added.

Useful reproduction commands from repository root:

```powershell
python -m pytest -q
python -m src.analysis.run_v2_6_nested_context_external_stack
python -m src.analysis.freeze_tdp43_v2_predictions
python -m src.analysis.evaluate_tdp43_v2_lock
```

The last two commands are historical freeze/reveal commands. Rerunning them must not be used to alter the frozen interpretation.

## Final instruction to the next agent

Continue trying hard, but do not confuse persistence with permission to compromise the experiment. The project has a real methodological signal and unusually strong reproducibility, but two confirmatory boundaries have failed: the original N-zip lock and the TDP-43 robustness gate. Astrocyte outcomes remain sealed. The only route to an earned confirmatory claim is new independent evidence under a prospectively frozen protocol, or a candid repositioning as a rigorous benchmark/negative result. Preserve every artifact, hash, commit and failure while pursuing that route.
