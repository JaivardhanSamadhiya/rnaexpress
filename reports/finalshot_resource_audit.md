# RNAddress FinalShot resource audit

Audit frozen: 2026-09-02  
Starting commit: `f5bf28ee85a75c03ffc8f116dc5677a48aa01efd`  
Branch: `rnaddress-final-zero-shot`

## Audit-only decision

The exact 21-million-parameter Parnet model described in the August 2026 preprint is **not reproducibly available**. The official repositories expose code, a 223-track index, three older preliminary models, and one additional development-branch model, but none matches the architecture reported in the preprint. Parnet is therefore excluded; it will not be renamed, approximated, or retrained.

The official frozen RBPNet release is reproducibly usable as the one fallback explicitly allowed by FinalShot section 6. Its Zenodo archive passed its published MD5, every one of its 103 checkpoints has been independently SHA-256 inventoried, and a CPU parent/single-nucleotide-mutant inference smoke test passed. Its limitations are material: all checkpoints are human HepG2 models; only 12 of the 26 prespecified localization-related human RBP symbols are covered; TARDBP, ELAVL, MBNL, PUM, FMR1, FXR1, and IGF2BP2 are absent; and mouse use is cross-species sequence inference, not a validated mouse model.

No localization performance model was trained, selected, or evaluated during this audit. No N-zip outcome was accessed. No protected Astrocyte sequence identity or outcome was accessed. The protected loader remains byte-identical at SHA-256 `78fd563f4e51866bc6d0e18aac9bfbbedf20ad0986e6bd087caf9b0b11901a78`.

## Resource decision matrix

| Resource | Exact audited version | Weights reproducible? | Mouse / variant status | FinalShot role |
|---|---|---:|---|---|
| Parnet / PanRBPNet | bioRxiv v1; code `2f0570c`; paper repo `0f3dd29` | **No for the preprint model** | Paper supports sequence variant deltas; exact released paper model absent | Excluded |
| RBPNet | Genome Biology 2023; code `8ee000d`; 103-model Zenodo archive | **Yes** | Human HepG2 training; arbitrary ACGT sequence inference works; variants supported; mouse biology unvalidated | Frozen output-space fallback |
| DeepLocRNA | Bioinformatics 2024; tag/commit `5e426b2` | Yes | Separate human/mouse checkpoints; broad compartments; parent/mutant scores technically possible | Precedent only |
| BRIDGE | Nature Communications 2026; code `b5d8865`; Figshare v6 | Yes in principle, but 18.45 GB model bundle not acquired | Human, six cell lines, 101-nt windows; requires modalities absent here | Methodology only |
| Spatial NT-seq / GSE249405 | Nature Neuroscience 2026; GEO public 2026-06-12 | No sequence-to-stability checkpoint | Mouse brain turnover observations, not mutant scoring | Excluded from modeling |
| RNALocate v3 | NAR 2025 | No versioned predictor code/checkpoint found | Human/mouse observations and broad localization prediction; no neurite/soma target | Excluded |
| MAVE-NN | Genome Biology 2022; audited repo `95b5ff4`; release 1.1.4 commit `d4c9f37` | Method package, not an RNAddress checkpoint | Species-agnostic methodology | Measurement-process design only |
| Perturbation-response decomposition | bioRxiv 2026; code `a152147` | Method code only | Unrelated Perturb-seq setting | Response-alignment rationale only |

## 1. Parnet / PanRBPNet

### Publication and training data

The primary source is [Moyon et al., bioRxiv 2026.08.08.743506v1](https://www.biorxiv.org/content/10.64898/2026.08.08.743506v1), DOI `10.64898/2026.08.08.743506`, posted 2026-08-13. It is a preprint, is not peer reviewed, and is distributed under CC BY 4.0.

The paper reports 223 ENCODE eCLIP experiments spanning 150 unique human RBPs in HepG2 and K562. Coding and noncoding transcripts from GENCODE v48 were merged, tiled into 600-nt windows with 150-nt overlap, filtered for crosslink signal, and reduced to 700,114 tiles. Chromosomes 3, 8, and 15 were held out for test; chromosomes 2, 9, and 16 for validation; other autosomes were used for training.

The reported model is a 21-million-parameter network with a 128-filter, kernel-12 stem; nine 128-filter, kernel-6 residual blocks; and 223 experiment heads using kernel-20 transposed convolutions. Each head represents a target profile, matched-control profile, total profile, and mixing coefficient. The output is a 600-position probability distribution. The paper computes mutation effects from differences in reference versus alternate RBP-binding probabilities.

The published training archive is Zenodo record `14176118`, `encode.filtered.5.hfds.tar.gz`, 4,951,300,341 bytes, published MD5 `7b7336ee812998349adb4faaca3f20ce`, CC BY 4.0. It is training data, not a checkpoint.

### Code, versions, licenses, and model files

The paper points to [marsico-lab/parnet](https://github.com/marsico-lab/parnet-marsico-lab) and [marsico-lab/parnet--paper](https://github.com/marsico-lab/parnet--paper). The former resolves to the `mhorlacher/parnet` history.

- Package tag `0.5.0` and default-branch commit: `2f0570cf47d8bb927415a71f853a97eb7e94005c`.
- Package metadata versions disagree: `pyproject.toml` says `0.0.1`, while importing the pinned source says `0.1.1`.
- Package license: Apache-2.0; local license SHA-256 `d96ebeda1e4282750cf14b98eced9e599a61d167529123f67fecb5bbc6f02db1`.
- Paper repository commit: `0f3dd29a9e3a3add7db175555721cbf001372199`.
- Paper repository license: Apache-2.0; local license SHA-256 `729b7a084f9144a52de1053a58425b323ac80614bb142b9ba7a0d925192ad5e9`.
- The paper repository says it is under construction and that the model “will live” in the package repository.
- The 223-track RBP/cell index is present and hashes to `d5d2190124c6502652363faaf7d007828904aae96926c7ca46d43efe311c0ab5`.

The default branch contains three preliminary serialized models:

| File | Bytes | SHA-256 |
|---|---:|---|
| `NewRBPNet_7M_Penalty-0.0_20250107.pt` | 30,213,074 | `ff28efcf544998ac5b74b94a7b4504f101998572bf5683d6000c4aec2b97b25d` |
| `NewRBPNet_7M_Penalty-10.0_20250107.pt` | 30,213,074 | `cdb8168de7328bc51a53995281f190ff8c2c60b20df3f797d7c59330b9d77532` |
| `RBPNet_7M_20241126.pt` | 29,917,908 | `ca22ca53bf964234d77387672a11b0ae7bd52ec1919732553b9c6faad7c14000` |

At tag `0.5.0`, the first preliminary model tested cannot deserialize because its serialized `NewAdditiveMix` class was removed from the pinned package. A development-branch commit, `5aabae3181199c69ac70525a20f7cbf4feaec45b`, adds `0.5.0_RBPNet-11M.pt` (47,059,137 bytes; SHA-256 `2620a1c9b838fd28fcefb3c8cc695fa7a4889fb18a67c21694c097248aa64869`). Under that exact development source it loads on CPU and emits finite target/control/total profiles and 223 mixing coefficients for a 600-nt sequence.

That executable checkpoint is **not the preprint model**. Direct introspection gives 11,736,799 parameters, 14 residual blocks, 512 channels, kernel-3 residual convolutions, and pointwise 1×1 output projections. These values contradict the paper’s 21 million parameters, nine 128-channel kernel-6 blocks, and kernel-20 transposed heads. The checkpoint was committed in August 2025, one year before the preprint, with no model card, training run identifier, benchmark linkage, or paper-checkpoint declaration.

No paper-matching checkpoint exists in the three official repositories’ releases, GitHub Actions artifacts, reachable branches, or tags. Searches of Hugging Face and Zenodo found no Parnet model artifact. Therefore the exact checkpoint version and hash requested by the protocol are **unavailable**, not unknown through lack of effort.

### Parnet decision

Parnet is excluded. The executable development artifact proves the code can produce 223-channel profiles, but does not establish that those profiles are the published Parnet model. Substituting it would import unvalidated weights under the paper’s name. Retraining 223 eCLIP tasks is prohibited and was not attempted.

## 2. Frozen RBPNet fallback

The primary source is [Horlacher et al., Genome Biology 2023](https://genomebiology.biomedcentral.com/articles/10.1186/s13059-023-03015-7), DOI `10.1186/s13059-023-03015-7`, a peer-reviewed article. The official code repository is [mhorlacher/rbpnet](https://github.com/mhorlacher/rbpnet), pinned at `8ee000dcdb897e0eeed6a46a855604299e914ca7`; package version `0.10.0`; MIT license; license SHA-256 `03445952ebacd32b96bcf85ab38938ac4aaf070b0ae34b8dc03e1f2ad97475f8`.

RBPNet was trained as separate sequence-to-signal models for 103 ENCODE HepG2 eCLIP datasets / human RBPs. Training windows are 300 nt, while fully convolutional inference accepts arbitrary lengths. Each frozen model returns a nucleotide-resolution protein-specific target profile, control profile, observed/total profile, and sequence-level mixing coefficient. The official implementation includes variant-impact scoring.

The official Zenodo record `10185223` supplies `RBPNet_models.zip`:

- bytes: 836,278,121;
- published and locally reproduced MD5: `e88fb57483ba9a3d81b842cc5aa140fb`;
- local SHA-256: `dc182e51d7b3ffe046ec7de56ab7e98a9ec0bd2f789d8e6bd61168b3718c355d`;
- extracted checkpoints: 103, totaling 1,133,681,984 bytes;
- every checkpoint’s path, size, task, cell line, and SHA-256 is frozen in `results/finalshot/rbpnet_checkpoint_manifest.csv`.

### Reproducible inference smoke test

An isolated CPU runtime used Python 3.11.9, TensorFlow 2.15.1, TensorFlow Probability 0.23.0, RBPNet 0.10.0 source, and `igrads` commit `a19c5e2aaa323d001389f9e6a6d2d3cfd05001d2`. `QKI_HepG2.model.h5` loaded without compilation. For a fixed 300-nt reference and one-base mutant it returned:

- input shape `[batch, length, 4]`;
- four named outputs with shapes `[2,300]`, `[2,300]`, `[2,300]`, and `[2,1]`;
- finite values throughout;
- target-profile sums `1.0` and `0.9999998807907104`;
- target-profile mutant-minus-parent L1 difference `0.08078941702842712`.

This is an audit smoke test, not a localization result.

### Mouse applicability

RBPNet has no species token and accepts mouse A/C/G/T sequences technically. That does **not** make it mouse-trained or establish calibrated mouse binding. A 2026-09-02 snapshot of the [Mouse Genome Informatics human–mouse homology report](https://www.informatics.jax.org/downloads/reports/HOM_MouseHumanSequence.rpt) was pinned at SHA-256 `3d4bc89e71e57e10adf0139ba033786cb02e2e24e8d49cf0c357d1c2924afa0a`. Of the 103 RBPNet human symbols, 99 have one-to-one mouse mappings, four have non-one-to-one mappings, and one (`TROVE2`) was missing from that report. The exact rows are in `results/finalshot/rbp_orthology_mgi_2026-09-02.csv`.

FinalShot may therefore use RBPNet only as a frozen, human-trained sequence prior with an explicit cross-species limitation. Non-one-to-one and missing mappings cannot be used for trans-expression conditioning without a prespecified rule.

## 3. Localization-RBP coverage

The official Parnet index declares 223 experiment channels / 150 unique RBPs, but those channels are unavailable because the paper checkpoint is unavailable. RBPNet’s usable fallback has 103 HepG2 channels. Prespecified coverage is:

| Family | Symbols present in usable RBPNet | Symbols absent |
|---|---|---|
| ELAVL/Hu | none | ELAVL1, ELAVL2, ELAVL3, ELAVL4 |
| MBNL | none | MBNL1, MBNL2, MBNL3 |
| TDP-43 | none | TARDBP |
| SFPQ | SFPQ | none |
| FMRP/FXR | FXR2 | FMR1, FXR1 |
| IGF2BP | IGF2BP1, IGF2BP3 | IGF2BP2 |
| PUM | none | PUM1, PUM2 |
| Other audited regulators | QKI, STAU2, FUS, HNRNPK, PTBP1, TIA1, TIAL1, RBFOX2 | STAU1 |

No missing output is imputed or fabricated. The full channel-level table, including declared but unusable Parnet cells and cross-species caveats, is `results/finalshot/rbp_coverage.csv`.

The absence of TARDBP makes the proposed TDP-43 channel-specific sanity test impossible under the fallback. TDP can still test whether other RBP-state deltas add value among its known motif edits, but success cannot be described as direct recovery of TDP-43 binding.

## 4. DeepLocRNA

The primary source is [Wang et al., Bioinformatics 2024](https://academic.oup.com/bioinformatics/article/40/2/btae065/7601323), DOI `10.1093/bioinformatics/btae065`, peer reviewed. The official repository is [TerminatorJ/DeepLocRNA](https://github.com/TerminatorJ/DeepLocRNA), release `0.0.2`, exact commit `5e426b2de872e8c3b269a9e7efb6f6894648ef8f`. The release and repository have provenance inconsistencies: the repository’s `setup.py` reports `0.0.4`, no root `LICENSE` file is present, and package metadata declares MIT.

Available checkpoints are:

- human: 73,910,613 bytes, SHA-256 `4809a61002ef1399eda39b701eb3eb26786c841b518f15b158aecf41effd3213`;
- mouse: 73,910,421 bytes, SHA-256 `f656f6fdf3ee9d0d0248b186b5f4686b154ebed4500105d891e2f2de5b2bf72b`;
- bundled PanRBPNet encoder: 33,188,471 bytes, SHA-256 `c08e2ef0d9e05bdc7dff86be42eac402bc9e42e3a8e62d450da057008db0b8e1`.

Inputs are padded/truncated to 8,000 nt and tagged by RNA type. The code supports mRNA, miRNA, lncRNA, and snoRNA and separate human/mouse operation. Its nine broad output labels are nucleus, exosome, cytosol, cytoplasm, ribosome, membrane, endoplasmic reticulum, microvesicle, and mitochondrion; label availability varies by RNA type and species. It has no neurite-versus-soma head and no assay context.

All five bundled training FASTAs were parsed. Exact full-sequence overlap with the certified Mikl, TDP, and Moffatt parent-plus-mutant sequence sets is zero in all 15 source/file comparisons. Counts and results are frozen in `results/finalshot/external_sequence_overlap.csv`. Exact sequence nonoverlap does not resolve possible gene/study overlap in a heterogeneous localization database, so the model is not promoted into the primary feature family. It remains precedent that RBP-binding pretraining can support localization prediction.

## 5. BRIDGE

The primary source is [BRIDGE, Nature Communications 2026](https://www.nature.com/articles/s41467-026-73086-0), DOI `10.1038/s41467-026-73086-0`, peer reviewed. The official [wangyb97/BRIDGE](https://github.com/wangyb97/BRIDGE) code is pinned at `b5d886557e58f896c975ab290ad77a38df629658`, MIT license, license SHA-256 `726971fb79a15ddec27cac40bbebb1d48fe842385228308677852eebb39b37a`.

The Figshare release is DOI `10.6084/m9.figshare.29819843.v6`, version 6, CC BY 4.0. It covers 261 human RNA–RBP datasets across K562, HepG2, HEK293, HEK293T, HeLa, and H9, representing 172 RBPs. It combines sequence, predicted/measured RNA structure, motif priors, biochemical profiles, RBP identity, and cell context. Inputs are fixed 101-nt windows, and reference-versus-mutant scoring is supported.

Published files include a 18,449,357,955-byte model archive plus dataset, motif, variant, RBPformer, and reproducibility bundles. The released checksum list names some `.zip` files where the current Figshare files are `.rar`, a packaging inconsistency requiring care.

BRIDGE is not directly usable here. It is human-cell-line-specific, expects matched modalities unavailable for the certified RNAddress sequences/contexts, has no validated mouse mode, and its model bundle alone is 18.45 GB. Forced zero-filled adaptation would not reproduce the published input distribution. Its mutant-minus-reference RBP-impact construction informs feature design only.

## 6. Spatial NT-seq / GSE249405

The primary source is [Spatial mapping of RNA turnover kinetics in the mouse brain, Nature Neuroscience 2026](https://www.nature.com/articles/s41593-026-02420-y), DOI `10.1038/s41593-026-02420-y`. [GSE249405](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE249405) is a mouse SuperSeries made public 2026-06-12, combining scNT-seq2 (`GSE249398`) and spatial NT-seq (`GSE249403`), 38 samples, roughly 6.7 GB.

The associated [spatialNT-seq](https://github.com/wulabupenn/spatialNT-seq) repository is pinned at `1401d941559d84c4be9a3241bb72839434f44e04` and contains only a README: no license, processing implementation, sequence model, checkpoint, or mutant scorer. [RNAkinetoScope](https://github.com/hongjie7/RNAkinetoScope), pinned at `b5cd23a475e9fa9d988514b0ea65694e08b90594`, estimates kinetics from new/total counts; it is not a sequence-to-stability model and has no pretrained variant checkpoint. Its metadata says MIT, but the repository has no license file.

GSE249405 is therefore excluded from FinalShot feature generation. Training a new sequence model from cell-type turnover observations would be a new, weakly identified project, not reuse of a released prior. No astrocyte-specific sample, coefficient, sequence, or statistic from this series was opened or computed.

## 7. RNALocate v3

The primary source is [RNALocate v3.0, Nucleic Acids Research 2025](https://academic.oup.com/nar/article/53/D1/D284/7822296), DOI `10.1093/nar/gkae872`, peer reviewed; the paper is CC BY-NC 4.0. It reports 1,258,724 experimentally validated entries across 242 species, 26 RNA types, and 177 subcellular localizations, plus prediction records. Its sequence predictor covers seven RNA types and 11 broad compartments with inputs up to 8,192 bases.

No versioned official predictor repository, model checkpoint, model hash, or reproducible study-exclusion interface was found. The paper also identifies the absence of cell-line/state/expression information as a limitation. RNALocate is excluded because it adds broad forward-localization labels rather than neurite/soma intervention deltas, while study-level overlap with the development assays cannot be resolved from a pinned model artifact.

## 8. MAVE-NN methodology

The primary source is [Tareen et al., Genome Biology 2022](https://genomebiology.biomedcentral.com/articles/10.1186/s13059-022-02661-7), DOI `10.1186/s13059-022-02661-7`, peer reviewed. [jbkinney/mavenn](https://github.com/jbkinney/mavenn) was audited at `95b5ff4913b961ac172fbc23c22be986f9f671d7`; release 1.1.4 resolves to `d4c9f3759c2ef0dbb1046feabe0d5062c14b0ad3`; MIT license SHA-256 `b7807958cd87ee9a5ef35c358289c3d7065e8d2fa7990fa736efe436c68e6882`.

MAVE-NN contributes only the separation of a latent genotype-to-phenotype map from a measurement process. It supplies no RNA-localization checkpoint or labels and therefore has no sequence/study leakage into RNAddress. Any FinalShot implementation must use low-capacity, training-fold-only monotone source heads and must ablate them against direct regression.

## 9. Perturbation-response decomposition

The audited source is [Molina and Zhang, bioRxiv 2026.07.24.740459v1](https://www.biorxiv.org/content/10.64898/2026.07.24.740459v1), DOI `10.64898/2026.07.24.740459`, a non-peer-reviewed CC BY 4.0 preprint. The [implementation](https://github.com/xinyizhanglab/perturbation-decomposition) is pinned at `a15214780619736d393f40240e56ba992fd416a3`. Its README says MIT, but no license file is present.

Its CRISPRi/Perturb-seq data and models are unrelated to RNA localization. It is methodology-only evidence for decomposing global, perturbation-specific, context-specific, and interaction response components and for aligning priors to the response component. No data or weights are transferred.

## Decontamination and overlap conclusions

1. **Mikl/TDP/Moffatt outcomes:** Parnet, RBPNet, and BRIDGE were trained on CLIP/RBP-binding targets, not localization intervention outcomes. Their label spaces therefore do not duplicate RNAddress localization labels. Transcript sequence overlap with generic human eCLIP tiles may exist, but it does not supply target localization outcomes and is an allowed RBP prior. Parnet is excluded regardless.
2. **DeepLocRNA:** exact full-sequence overlap across all five released training FASTAs and all certified development parent/mutant sequences is zero. Possible study/gene overlap remains unresolved, so the model is not used.
3. **RNALocate:** study/accession overlap cannot be made reproducible from a pinned predictor artifact; excluded.
4. **Protected Astrocyte study:** exact Astrocyte sequence overlap was intentionally not tested because sequence identities are sealed. No audited resource explicitly names the protected study accession as training data. Resources with unresolved heterogeneous localization corpora are excluded. GSE249405 is a distinct public study and its astrocyte component was not accessed.
5. **N-zip:** no N-zip sequence or outcome influenced any decision in this audit.

## Computational feasibility

- Parnet paper model: infeasible because exact weights are unavailable; retraining prohibited.
- Preliminary Parnet development model: CPU inference feasible but scientifically ineligible because it is not the reported model.
- RBPNet: feasible on CPU. Full caching across 62,758 interventions × 103 models is substantial but tractable through exact-sequence deduplication, batched inference, deterministic windowing, and checkpoint-by-checkpoint caching. Each cache key must include sequence SHA-256, checkpoint SHA-256, crop/window rule, output track, and software versions.
- DeepLocRNA: checkpoint files are local, but the dependency stack is older and the output target is inapplicable; no runtime effort is justified.
- BRIDGE: technically large and input-incompatible; no 18.45 GB download is justified.
- GSE249405/RNALocate: no reproducible sequence-to-mutant checkpoint; excluded.

## Stop-rule interpretation and authorization boundary

Sections 6 and 49 create a literal tension. Section 6 says unavailable Parnet weights require stopping **Parnet as a candidate** and explicitly permits a frozen RBPNet fallback; section 49 says to stop if “Parnet outputs cannot be reproduced.” This audit resolves them prospectively as follows:

- failure to run an identified, matching Parnet checkpoint would stop FinalShot;
- nonrelease of the paper checkpoint invokes section 6: exclude Parnet and permit only the frozen RBPNet fallback;
- the executable but architecture-mismatched preliminary Parnet model cannot be used to evade either rule;
- no localization evaluation may begin until a separate FinalShot protocol commits the exact RBPNet summaries, windowing, eligible channels, mouse limitations, folds, candidate models, controls, and gates.

Under that resolution, the resource gate is **conditional pass for protocol freezing**, not evidence for GO. The only permitted mechanistic representation is frozen RBPNet output space. Parnet embeddings, DeepLocRNA scores, BRIDGE predictions, RNALocate pretraining, and GSE249405-derived stability are excluded from the primary FinalShot run.

## Machine-readable artifacts

- `results/finalshot/resource_audit_manifest.json`
- `results/finalshot/rbpnet_checkpoint_manifest.csv`
- `results/finalshot/rbp_coverage.csv`
- `results/finalshot/rbp_orthology_mgi_2026-09-02.csv`
- `results/finalshot/external_sequence_overlap.csv`

This report is the audit checkpoint only. It does not authorize access to Astrocyte, does not spend any prospective validation set, and does not establish that the original zero-shot RNAddress hypothesis survives.
