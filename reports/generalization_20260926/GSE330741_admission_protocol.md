# GSE330741 admission: metadata-only decision

26 September 2026. This is a new user-authorized cross-assay study, separate from all historical RNAddress gates and immutable SRLE results at `4bd5154`. The current instruction authorizes GSE330741 outcome access only after a new committed protocol and prediction freeze. It does not reopen N-zip, TDP EV5 or any other protected resource, and does not erase previous negative results. No mutation-level outcome has been read during this admission phase.

## Exposure classification: PARTIALLY EXPOSED

`data/frozen/external_manifest.json`, frozen at **2026-08-26T11:52:44.760703Z**, records **three result-sheet rows printed during schema discovery** before that freeze. The archived Phase A–E report and reconstruction code also show programmatic loading of the full result worksheet to check row matching and nonmissing labels; outcome values were not exported into the feature-only table. A later historical test loaded the worksheet, as disclosed in the v3 finalization report. The three printed row identities/values are not established in the surviving exposure record; they are not recovered by reopening outcomes here. This cannot be called never-seen data.

The August 26 original internal freeze and failed gate state Astrocyte outcomes were not used in fitting or gate decisions. August 27 commit `4370e38` added fail-closed source-workbook access. Subsequent v2–v5/FinalShot/research records state no Astrocyte outcome use for model/feature/hyperparameter development. September 23 and 24 scope records document unsolicited published aggregate search excerpts, not deliberate mutation-level evaluation. These records support no *documented* outcome-driven model selection; they do not prove perfect ignorance or rule out undocumented influence. Known metadata informed the choice of external endpoint and parent grouping, which is explicitly disclosed.

This admission inspected the source methods and static R code only. A targeted QC-sentence extraction inadvertently returned a **tiling-library aggregate CDF significance sentence**; it is not used for any model decision. No mutation value, outcome heatmap or quantitative mutation result was opened. GSE330741 remains **partially exposed, outcome-blinded from the new freeze onward**, not an untouched confirmatory set. Any successful result must retain that qualification. If evidence of target-outcome-driven model decisions is discovered, the pristine external-confirmation branch stops; no relabeling can restore it.

## Source identity and access

Official study: [GEO GSE330741](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE330741), *In Vivo Massively Parallel Reporter Assay Reveals Sequence Determinants of mRNA Localization in Astrocytes*. Author methods are available in [PMC13142395](https://pmc.ncbi.nlm.nih.gov/articles/PMC13142395/), DOI `10.1101/2026.04.27.721172`; the [author repository](https://github.com/Dougherty-Lab/astrocyte_sn-mpra) was previously pinned to `94651f5ffc19d818c194bc4f56d3e5f2459349cc`. These are public resources requiring no payment. Existing verified copies are reused, with no new raw-sequencing download or expenditure.

The official GEO series was updated September 8, 2026 to remove unrelated GSM9822133–GSM9822156 samples included by mistake. Its current inventory has 139 samples. The historical 163-member archive remains byte-identical and is not overwritten. The mutation analysis uses only the 106 predeclared GSM973... `fraction_number[a|b].txt.gz` lane files; no removed GSM982... resource enters this study. Current web metadata, cached article methods, sample filenames and source processing code are corroborating sources; mutation measurements remain sealed until the freeze.

Exact source hashes are in `results/generalization_20260926/metadata_receipt.json`. The official supplementary workbook is SHA-256 **1d17c0631fc962b762dddf3f27f76494dadf882f28a0154b5af76dbedd57c3f6**. The historical raw-count archive is **88c883f41530b485ccacd98b276e90c8955138e64d7d02babf1a7738bee25f1f**. Only archive filenames were listed during admission; no member data were read.

## Parent and mutation structure

The certified outcome-free design contains **4,553 exact SNVs**, eight 190-nt reference inserts, 1,520 positions, 1,513 positions with all three alternate bases and seven with two. Parent, reference/alternate base, mutation coordinates and exactly one changed nucleotide are verified from the previously frozen sequence-only artifact. All missing alternatives remain missing. Parent IDs describe original tile groups, not necessarily the exact start/end of the final 190-nt consensus; exact UTR coordinates and sequences are exported separately.

| Parent ID | Gene/transcript label | Exact parent UTR span | SNVs | Admission |
| --- | --- | --- | --- | --- |
| slc1a2.1_2621_2681 | Slc1a2 / Glt1a | 2621–2810 | 569 | Author poor-cloning exclusion |
| slc1a2.1_3281_3381 | Slc1a2 / Glt1a | 3301–3490 | 570 | Eligible |
| slc1a2.1_3641_3721 | Slc1a2 / Glt1a | 3641–3830 | 570 | Eligible |
| slc1a2.1_3781_3841 | Slc1a2 / Glt1a | 3781–3970 | 570 | Eligible |
| slc1a2.1_4181_4281 | Slc1a2 / Glt1a | 4201–4390 | 570 | Eligible |
| sparc_1041_1121 | Sparc | 1051–1240 | 570 | Eligible |
| sparc_661_761 | Sparc | 681–870 | 568 | Eligible |
| sparc_901_981 | Sparc | 911–1100 | 566 | Eligible |

The authors explicitly exclude Glt1a 2621–2681 because it cloned poorly. That exclusion is recorded **before mutation outcome access** and is the only predetermined parent exclusion. The remaining design has **3,984 SNPs, seven parents, five nonoverlapping parent components and only two genes**. Two parent pairs overlap by 50 UTR nucleotides. Accordingly, leave-parent-out training also purges overlapping same-gene parents. Clustering uses these five overlap components, with a two-gene sensitivity reported descriptively. These are not seven independent genes or thousands of independent experiments. The historical ≥20-biological-group breadth requirement is not met; this resource supports at most a bounded, qualified cross-assay test.

Biological source is mouse astrocytes in vivo. Reporter context is a GFAP-driven tdTomato reporter carrying the 3′UTR insert in AAV9. Methods identify a pool of three cortices as a biological replicate. Full assay/reporter context differs substantially from the human HBB SRLE nuclear/cytoplasmic system. UTR-relative coordinates are verified; exact chromosome coordinates and complete transcript accession versions are not reconstructed and remain explicitly unresolved.

## Replicate and endpoint definitions

Mutation sample filenames establish 16 cortical-input and 16 synaptoneurosome-input biological replicate labels, nine cortical-TRAP, nine SN-TRAP and three AAV DNA samples, each sequenced on two technical lanes. Technical lanes are summed; they are not biological replicates. Author static QC excludes replicate 16 throughout, SN-input replicate 10 and SN-TRAP replicates 3/4. Localization therefore has **15 cortical-input and 14 SN-input samples, with 14 matched labels** before per-variant missingness. The 3-cortex pool is the biological sampling unit; pedigree/litter independence is not fully recoverable from filenames.

The GEO processing definition is log2(normalized SN input / normalized cortex input), positive for greater synaptoneurosomal enrichment. Author code specifies **log2(CPM+1)**, followed by subtraction of the within-parent-group mutation-library median separately for fraction and replicate. A per-element mixed model `normalized_log2 ~ fraction + (1|replicate)` estimates SN input minus cortex input; `lmer`'s REML fit supplies the coefficient. The summary column is `snin_ctxin_logFC`, traced through `normalized_localization_results.csv` into the comprehensive table.

Critically, this published “Δ localization” is **mutation-group-centered**, not automatically mutant minus exact WT. This study's edit target is explicitly `snin_ctxin_logFC(mutant) − snin_ctxin_logFC(exact matched 190-nt WT)`. Positive means the SNP increases relative SN/cortex enrichment versus its own WT; negative means it decreases that enrichment. Replicate paired effects subtract the corresponding WT fraction contrast; the shared group median cancels within each pair. Published mixed-model effects and simple paired-replicate means are compared but never presumed identical. No FDR or outcome-magnitude filter is permitted.

The assay measures SN/cortex enrichment, not SRLE nuclear retention, RNA stability or local translation. Equal log bases do not establish equal physical calibration. Rank-based Test A is therefore primary, with magnitude metrics explicitly diagnostic.

## Admission decision

**QUALIFIES WITH LIMITATIONS for a new frozen, partially exposed, bounded cross-assay test and grouped method study. NOT UNTOUCHED.** Exact SNV lineage and the localization endpoint are established from methods/design; outcome mapping, finite WT values and replicate completeness must pass the frozen reveal-stage checks. Fewer than five admitted parents, four overlap components, 100 candidates in any admitted parent, unresolved WT/variant mappings or target semantics stop the affected branch rather than triggering a new choice of endpoint, parent set or metric. No third-system pristine validation opportunity exists in already-developed GSE334718; its status is documented separately.
