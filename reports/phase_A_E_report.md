# RNAddress Phase A–E gate report

Date: 2026-08-26. No model has been developed or fit. Counts below come from physically downloaded files, not paper approximations. Full provenance is in `data/manifests/acquisition_manifest.csv`; dataset capabilities are in `reports/data_matrix.csv`.

## 1. Novelty verdict

**Exact defensible claim:** RNAddress targets a target-conditioned computational operation—starting RNA + requested localization direction + protected properties → ranked minimal cis-sequence edits—evaluated by revealing measured interventions on parent-held-out landscapes and a lab-independent in-vivo assay.

The strongest capability collision is [CRISPR-TO](https://pmc.ncbi.nlm.nih.gov/articles/PMC12882822/), which redirects endogenous RNA with dCas13 and localization/motor proteins. The strongest cis-sequence collision is [designed nuclear-speckle localization logic](https://pmc.ncbi.nlm.nih.gov/articles/PMC12962856/). Direct experimental-map collisions are N-zip, astrocyte SN-MPRA, SRLE-seq and mutREL-seq. Forward-prediction collisions include RNA-GPS, DM3Loc, DeepLocRNA and RNALoc-LM. None found performs the complete target-conditioned minimal cis-edit operation with comparable intervention evaluation.

Patent threats include artificial cis zipcodes ([US5641675](https://patents.google.com/patent/US5641675A/en)), CRISPR-TO-style spatial manipulation ([WO2025096250A1](https://patents.google.com/patent/WO2025096250A1/en)), trans-splicing localization domains ([WO2023215761A1](https://patents.google.com/patent/WO2023215761A1/en)) and RNA-targeting/zipcode manipulation ([US20250101393A1](https://patents.google.com/patent/US20250101393A1/en)). These prohibit broad “first to engineer RNA localization” language. The search is not a legal freedom-to-operate opinion.

- Novelty: **8.0/10**.
- PV-Care-style capability novelty potential: **8.3/10**, not yet earned empirically.
- Novelty decision: **GO**. The stop-rule collision was not found.

The complete hostile audit, variable-renaming result and forbidden claims are in `reports/novelty_audit.md`.

## 2. Data verdict

### Mikl / GSE173098

- Paper: [A massively parallel reporter assay reveals focused and broadly encoded RNA localization signals in neurons](https://pmc.ncbi.nlm.nih.gov/articles/PMC9561380/), DOI `10.1093/nar/gkac806`; accession [GSE173098](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE173098).
- Downloaded: `GSE173098_RNAloc_MPRA_counts.csv.gz` (2,327,697 bytes; SHA256 `809e4d3f286edd3373ebf2dfb3b93a658179a83eac85007a04ad381612f44d99`) and `gkac806_supplemental_files.zip` (16,116,656 bytes; SHA256 `20254fcc65b10b81370e3a2f3903ec72153f303aebc3de50888d95f1a76b90df`). The nested archive and Tables S1–S19 were extracted.
- Exact counts: 47,989 raw count rows; 47,347 analyzed constructs in Table S2. Subsets include 13,753 `wt scanning 50` and 12,909 `mut scanning 50` constructs.
- Parent/mutant reconstruction: 11,926 safe multi-base motif-replacement pairs, 6,104 distinct parent sequences, all 198 nt. There are zero SNV pairs. Excluded: 213 ambiguous-parent and 770 missing-parent mutant rows.
- Localization: `logFC(neurite/soma) - CAD` and `logFC(neurite/soma) - Neuro-2a`, with associated p-values and replicate read counts.
- Protected properties: ActD stability at 4 h and 24 h with p-values. Missing: matched translation, ribosome occupancy and a direct expression effect.
- Requirement: nearest-sequence parent matching within gene/3'UTR-position, equal-length checks and exclusion of ties/missing keys. Suitable as broad development/pretraining evidence, not as a minimal-SNV ground truth.

### N-zip / E-MTAB-10902, E-MTAB-11572, E-MTAB-11575

- Paper: [Massively parallel identification of mRNA localization elements in primary cortical neurons](https://pmc.ncbi.nlm.nih.gov/articles/PMC9991926/), DOI `10.1038/s41593-022-01243-x`.
- Downloaded: complete supplementary archive and workbooks; central workbook `41593_2022_1243_MOESM2_ESM.xlsx` (7,203,866 bytes; SHA256 `15560b562c86c3d8fea8611154c4b0504a9528051b6038c19ff96bb47cd9fec9`); BioStudies API, IDF and SDRF metadata for all three accessions. Example SDRF SHA256: `553a395eda9f892cd0372cfd500ea0487546bcd3fdc29213324149cc77b2372e`.
- Exact counts: 4,813 initial-library tiles; 6,266 mutagenesis constructs: 20 WT, 4,695 single-base, 783 2-nt, 313 5-nt, 179 10-nt, 106 deletions, 102 targeted mutations and 68 scrambles.
- Truth-safe central set: 4,395 exhaustive SNVs on 15 parents totaling 1,465 nt; lengths 85, 90 or 100 nt. Every retained position has all three non-reference alleles and a primary label.
- Localization: parent/mutant `Mean_log2ratio_NeuriteSoma_WT` and adjusted p-value; mutant shAgo2, shHbs1l and shScramble neurite/soma fields are also present.
- Protected properties: perturbation-context localization is available, but no directly construct-matched expression, stability, translation or ribosome-occupancy field is safe to claim for the central SNVs.
- Missing/requirement: the outcome sheet omits source tile ID. Two sequence-distinct `Cflar_2` parents share the remaining identity, so all 300 SNVs from that identity are quarantined rather than assigned by row occurrence. Design/outcome key-multisets, exact one-base differences, references, alternatives and three-allele coverage were verified.

### Astrocyte SN-MPRA / GSE330741

- Paper: [In Vivo Massively Parallel Reporter Assay Reveals Sequence Determinants of mRNA Localization in Astrocytes](https://pubmed.ncbi.nlm.nih.gov/42094343/), DOI `10.1101/2026.04.27.721172`; accession GSE330741.
- Downloaded: complete `GSE330741_RAW.tar` containing 163 public count files (5,304,320 bytes; SHA256 `88c883f41530b485ccacd98b276e90c8955138e64d7d02babf1a7738bee25f1f`); `media-1.xlsx` (5,579,342 bytes; SHA256 `1d17c0631fc962b762dddf3f27f76494dadf882f28a0154b5af76dbedd57c3f6`); complete article supplement and public analysis repository.
- Exact counts: 4,769 library constructs, seven controls, eight biological parent groups, 209 WT-type constructs in those groups, and eight selected 190-nt mutagenesis parents. Reconstructed 4,553 SNVs over 1,520 positions; 1,513 positions have all three alternatives and seven positions have two, so seven of 4,560 saturation substitutions are absent.
- All 4,553 SNVs have complete localization (`snin_ctxin_logFC`), ribosome occupancy (`ctxtrap_ctxin_logFC`) and local translation (`paptrap_ctxtrap_logFC`) result rows. Expression can be derived from the available RNA/DNA replicate counts, but S8 has no single explicit expression-effect column. Stability is missing.
- Parent/edit mapping: exact full-sequence parent match plus one-difference, position, reference and alternative verification. Feature-only frozen artifact has eight exact parents and all 4,553 mutant sequences without outcomes.
- Quarantine: workbook, raw archive, feature artifact and audit are SHA-locked in `data/frozen/external_manifest.json`. Three result rows were inadvertently printed during schema discovery before freezing. No distribution, ranking, threshold or model result was viewed. This is outcome-blinded from freeze onward but not perfectly never-seen.

### SRLE-seq / HRA016642

- Paper: [High-throughput Screening of Sequence Elements Associated with RNA Localization](https://pmc.ncbi.nlm.nih.gov/articles/PMC13191086/), DOI `10.1093/csbj/csaf107`; accession [HRA016642](https://ngdc.cncb.ac.cn/gsa-human/browse/HRA016642).
- Downloaded: complete source-table archive `csbj.0107.f1.zip` (5,407,225 bytes; SHA256 `96f78de5943d4903a3c1e8edcdb490315db3172c1909d61538fc17a58f384b69`), Tables S1–S8, public code/model repository, HRA index and checksum list for 60 FASTQs (`md5sum.txt`, SHA256 `5020ececf7d0d55b763542664b46ac5fb1bdb6579782da4ef72fdb14521461e7`). The very large FASTQs were deferred because processed source tables fully satisfy Phase E.
- Exact usable screen: 4,096 unique 6-mers in Table S5, each with p-value, fold change, BaseMean, nuclear-retention score and nuclear/cytoplasmic category.
- Parent/mutants: one fixed reporter backbone with all `4^6` inserted motifs; not minimal edits on multiple natural parents. BaseMean is an abundance proxy, not a validated stability or translation endpoint.
- Role: secondary validation that the inverse *framework* can rank a different localization axis. It cannot support biological transfer of the neurite model or unseen-parent claims.

### Arora / GSE183192 (optional)

- Paper: [High-throughput identification of RNA localization elements in neuronal cells](https://pmc.ncbi.nlm.nih.gov/articles/PMC9561290/), DOI `10.1093/nar/gkac763`; accession GSE183192.
- Downloaded/extracted: `gkac763_supplemental_files.zip` (15,190,198 bytes; SHA256 `5c2ef29d3890ce9370e3c77c6ef03f8ebaf0c7077f6cae4a430cf7c9327f15a9`), two sequence/result text files, Tables S1–S8 and supplement PDF.
- Exact processed main tables: 7,360 260-nt constructs in each of Tables S1–S4; paper design approximately 8,100. This is a tiled forward localization dataset with replicates, not an explicit parent/edit landscape. Use only for optional forward pretraining.

## 3. Intervention-pair verdict

- **N-zip:** **4,395** exact `(parent, one-base edit, mutant, parent outcome, mutant outcome)` tuples across 15 parents. Complete three-allele saturation for every retained base. The unsafe 300 are excluded.
- **Mikl:** **11,926** exact equal-length parent/motif-replacement/outcome tuples across 6,104 distinct parents. All are multi-nucleotide; none is an SNV. Parent and mutant CAD/Neuro-2a localization plus 4 h/24 h stability are available.
- **Astrocyte:** **4,553** exact SNV tuples across eight parents, with complete localization, ribosome-occupancy and local-translation labels; seven possible substitutions are absent. Outcomes remain sealed.

Reconstruction code rejects rather than guesses ambiguous mappings. Its three integrity tests pass.

## 4. Ground-truth verdict

# YES

For each held-out N-zip or astrocyte parent, a system can enumerate actual assayed SNVs, receive a requested increase/decrease, commit a ranking without labels, and then reveal the mutant's real experimental measurement. This is retrospective experimental intervention validation, not a prospective wet-lab experiment. The strongest claim is ranking/selecting among assayed interventions; unassayed edits require an explicit out-of-support warning.

## 5. External validation verdict

Astrocyte SN-MPRA is independent enough to be meaningful and materially harder than a same-study test:

- **Lab:** Dougherty Lab versus the N-zip Mendonsa/Chekulaeva/Ulitsky collaboration.
- **Context:** adult mouse astrocytes in living brain after AAV delivery versus cultured mouse primary cortical neurons.
- **Assay:** synaptoneurosome/cortex input with astrocyte TRAP and PAP-TRAP versus neurite/soma fractionation MPRA.
- **Targets:** eight Glt1/Slc1a2 and Sparc regions versus 15 retained N-zip parents; exact gene and parent-sequence overlap are both zero.
- **Contamination risk:** both are mouse neural 3'UTR reporter assays and can share localization motifs, vector effects and study citations. The external paper's schema and three result rows were seen. These facts reduce, but do not erase, independence; parent-level separation and no post-reveal tuning are mandatory.

Verdict: **meaningful lab-independent in-vivo external validation, with limited parent diversity and a disclosed minor quarantine deviation.**

## 6. Baseline feasibility

All required baselines are implementable with the acquired data:

- random rankings per parent/direction;
- motif creation/disruption heuristics fit only on development parents;
- nearest-parent/window retrieval with abstention;
- regularized k-mer/structure-delta linear models and gradient boosting;
- a forward localization model followed by exhaustive scoring of all `3L` SNVs.

The candidate spaces are only 255–570 SNVs per parent, so exhaustive search is trivial. The proposed model must differ substantively from forward-model-plus-search or the algorithmic contribution fails.

## 7. Compute feasibility

Observed machine: Intel i7-1165G7, four cores/eight threads, 15.7 GiB RAM, no detected NVIDIA GPU, approximately 1.55 TiB free on `D:`. Current workspace is 0.191 GiB.

- Processed-data pipeline: under 1 GiB disk; 4–8 GiB RAM; minutes for reconstruction and baselines.
- Feature extraction/folding cache: approximately 1–5 GiB disk; 8–12 GiB RAM; hours on CPU.
- Classical/nested parent-level experiments: approximately 1–6 CPU-hours per full sweep depending on folds/bootstraps.
- Compact neural models: feasible through cloud/borrowed GPU in roughly 2–12 GPU-hours per selected run; local CPU fallback may take 8–72 hours and must be tightly budgeted.
- Full HRA FASTQs: checksum list has 60 large files and the archive is expected to require tens of GiB; raw reprocessing is unnecessary for the current scientific claim and is off the critical path.

No giant language model is justified at this sample/parent count.

## 8. Deadline feasibility

There are 20 calendar days from August 26 to September 15, 2026. A complete, defensible core is feasible only with strict scope control; global-gold-level polish is a stretch rather than a promise.

Critical path:

1. Aug 27–30: immutable splits, feature cache, five baselines and leakage tests.
2. Aug 31–Sep 4: compact intervention-aware models, parent-level nested validation and ablations.
3. Sep 5: lock model, environment, thresholds and internal predictions.
4. Sep 6–7: reveal internal and then external outcomes once; compute parent-bootstrap uncertainty and protected-property results.
5. Sep 8–10: hostile review, sensitivity analyses and claim deletion.
6. Sep 11–15: paper, reproducible package and interactive demonstration.

Hard kill criteria by Sep 4: no improvement over forward-search/retrieval, unstable parent-level confidence intervals, or no transferable external ranking. If triggered, narrow the claim to a benchmark/negative result rather than manufacturing success.

## 9. PV-Care ceiling

| Dimension | Current Phase A–E | Ceiling if later gates pass |
|---|---:|---:|
| Conceptual novelty | 8.0 | 8.5 |
| Algorithmic opportunity | 6.0 | 8.0 |
| Evidence strength | 5.5 | 9.0 |
| Biological significance | 8.0 | 9.0 |
| Demonstrability | 4.0 | 8.5 |
| Global-gold ceiling | 4.5 | 8.5 |

RNAddress is **not PV-Care-level now**: there is no selected algorithm, locked result, working user-facing inverse-design system, prospective experiment or user study. Its ceiling is credible because it can combine a clear requested-input-to-action capability with measured counterfactual reveals and a genuinely different in-vivo assay. It will reach that ceiling only if the algorithm beats strong baselines across unseen parents, the external test transfers, constraints are demonstrated, and the system is reproducible and usable. PV-Care's integrated EEG/hardware/user-validation evidence remains the comparison standard, not a rhetorical label.

# GO

All major Phase A–E gates pass: no stop-rule novelty collision was found; exact measured interventions exist; truth-safe N-zip and near-saturation astrocyte tuples reconstruct; the independent assay is physically acquired and frozen; SRLE-seq is correctly limited to a secondary role; baselines and compute are feasible. Modeling may proceed under `reports/validation_architecture.md`.

This GO does not assert that RNAddress works. It authorizes the empirical attempt and preserves explicit failure gates.
