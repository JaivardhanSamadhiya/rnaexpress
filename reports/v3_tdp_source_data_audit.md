# RNAddress v3 Phase 2 TDP-43 source-data audit

Audit date: 2026-08-28

Primary paper: Moffatt et al., *TDP-43 directly inhibits mRNA accumulation
in neurites through modulation of mRNA stability*, The EMBO Journal,
DOI 10.1038/s44318-025-00653-4, PMID 41398473, PMCID PMC12864922.

Public sequencing accession: GSE288185. Public figure-source accession:
BioStudies S-SCDT-10_1038-S44318-025-00653-4.

## Executive integrity result

No historical parent-mutant pairing error was found. Dataset EV8 provides an
independent FASTA record for every reporter. After removing the documented
20-nt cloning handle from each end, all 4,566 reconstructed parent inserts and
all 4,566 reconstructed mutant inserts match the published 260-nt sequences
exactly. Construct identifiers are unique and no row-order pairing is used.

The historical intervention table remains exactly 4,566 pairs across 16 genes.
The former validation split remains 3,560 development pairs and 1,006 pairs
across Fam160b2, Lars2, Diras1, and Synj2bp.

One non-pairing source defect was discovered in the raw SLAM-seq supplement.
Dataset EV5 contains 10,935 duplicate `sample + oligo` keys under the label
`WT_t0_1`, and there is no distinct `WT_t0_3` label. The GEO processed-file
listing likewise exposes WT t0 Rep1 and Rep2 but not Rep3, although the paper
describes SLAM-seq as triplicate. Raw EV5 stability reconstruction is therefore
quarantined. Phase 2 will use the authors' explicitly aggregated Figure 6C
reporter-level stability values, which have deterministic labels and no pairing
ambiguity.

## Complete public-source inventory

| Source | Rows | Identifier | Sequence | Localization | Stability | Binding | CLIP | Structure | Exact linkage to 4,566 pairs | Ambiguity / exclusion |
|---|---:|---|---|---|---|---|---|---|---|---|
| Dataset EV1, `44318_2025_653_MOESM2_ESM.xlsx` | 10,093 genes | `ensembl_gene_id` | no | endogenous CAD KO-WT | no | no | no | no | gene-level only | not intervention-level |
| Dataset EV2, `44318_2025_653_MOESM3_ESM.xlsx` | 10,057 genes | `ensembl_gene_id` | no | endogenous N2A KO-WT | no | no | no | no | gene-level only | not intervention-level |
| Dataset EV3, `44318_2025_653_MOESM4_ESM.xlsx` | 191,075 sample-oligo rows | `oligo` | no | MPRA UMI/read counts | no | no | no | no | all 4,566 by exact parent and mutant IDs | 0 / 0 |
| Dataset EV8, `44318_2025_653_MOESM9_ESM.txt` | 11,955 FASTA records | FASTA header | yes, 300 nt with handles | no | no | no | no | no | all 4,566 pairs; 9,132 exact insert matches | 0 / 0 |
| Dataset EV9, `44318_2025_653_MOESM10_ESM.txt` | 12,081 GFF records | `ID`, `oligo_id` | coordinates | no | no | no | no | no | all natural constructs by exact ID | 0 / 0 |
| Dataset EV4, `44318_2025_653_MOESM5_ESM.xlsx` | 9,937 oligos | `oligo` | no | no | no | RBNS raw and normalized counts | no | no | 3,600 pairs have both exact parent and mutant records | 0 / 966 pairs |
| Dataset EV5, `44318_2025_653_MOESM6_ESM.xlsx` | 133,144 rows | `sample + oligo` | no | no | T-to-C counts | no | no | no | raw reconstruction quarantined | 10,935 duplicate keys / all pairs |
| Figure 6C source, `paired_mut_clip_vs_stab_6c.tsv` | 7,200 rows | `name + oligotype` | no | no | aggregated KO-WT stability | no | yes | no | 3,600 pairs, explicit WT/mutant labels | 0 / 966 pairs; 3,117 have both finite values |
| Figure 4D source, `Fig4Dsource.txt` | 7,389 natural oligos | `oligo` | no | processed MPRA effect | no | no | reporter overlap | no | all 4,566 parents by exact ID | 0 / 0 |
| Figure 4E source, `Fig4Esource.txt` | 9,132 long rows | `oligo + name` | no | paired WT/mutant effects | no | no | reporter overlap | no | all 4,566 pairs by exact ID and label | 0 / 0 |
| Figure 4F source, `Fig4Fsource.txt` | 39,388 motif records | `oligo + kmerpos + motifid` | no | processed MPRA effect | no | no | reporter overlap | per-base pairing probability | 4,260 intervention parents | 0 / 306 pairs |
| Figure 5 source / Dataset EV4 | 9,937 oligos | exact `oligo` | no | joined processed effect | no | 5, 50, 500 nM R | yes | no | same 3,600 exact parent-mutant pairs | 0 / 966 pairs |
| Frozen v2.6 predictions and revealed outcomes | 1,006 pairs | `parent_id + mutant_id` | yes | intervention delta | no | no | yes | cached v2 summaries | all four historical lock genes | 0 / 3,560 development pairs |

The publisher's Figure 4F text has an unquoted newline inside the values
`No CLIP peak` and `Contains CLIP peak`. The deterministic parser repairs only
those two literal line breaks before CSV parsing. It does not infer or reorder
records. The resulting 39,388 motif records have complete declared columns.

## GEO inventory

The frozen GSE288185 public file listing contains 87 records including the RAW
archive. Reporter-matched processed files include:

- 16 MPRA files: soma/neurite x WT/KO x four replicates;
- 8 RBNS files: input/0 nM plus 5, 50, and 500 nM measurements;
- 14 SLAM-seq files: WT/KO, t0/t12, and controls;
- endogenous CAD and N2A fractionation quantifications;
- Q331K, mouse/human neuronal, and other study-level follow-up files.

The raw sequencing archive is not required for Phase 2 because the public
supplement provides exact construct-level counts and the authors' processed
mechanistic quantities. No source was paired by arbitrary row order.

## Deterministic linkage rules

1. Historical pair identity is the exact `parent_id` and `mutant_id`.
2. EV8 FASTA identity is the complete header; the reporter insert is bases
   21-280 of each 300-nt synthesis record.
3. MPRA and RBNS records use exact complete construct identifiers.
4. Figure 6C strips the gene-name and mutation suffix but retains the unique
   natural oligo ID. Each ID has exactly one row labeled `TDP-43 motif` and one
   row labeled `Mutant motif`; the historical design has exactly one companion
   mutant per natural construct.
5. CLIP is retained only as the source-provided reporter-level overlap flag.
   No unsupported base-level CLIP occupancy is manufactured.
6. Figure 4F motif positions are zero-based starts and are validated against
   the exact EV8 reporter sequence before use.
7. Missing RBNS or stability measurements remain missing. They are not imputed.

## Source hashes and reproducibility

The machine-readable audit at `reports/v3_tdp_source_data_audit.json` records
SHA-256 hashes for the full-text XML, EV1-EV9 supplements, Figure 4-6 source
archives, GSE288185 file listing, historical pair table, pairing audit, frozen
predictions, and formerly locked TDP outcomes.

Key hashes:

- historical 4,566-pair table:
  `39590d9609a4376d39b1e48886576fdad2ef10764bbebb0130ecd86e27ba8e6f`
- EV8 reporter FASTA:
  `ab8a412cba676cb76adf7029918c9fcd4f07e466af4b3682e9d2d2c2ef058365`
- EV4 RBNS workbook:
  `d6ba86784e741ec2aba5b07de3ed5ed31e0ce794cd453cf68a1b5cb9a2385305`
- EV5 SLAM-seq workbook:
  `6aa4492a3e7111eab1eaea1638d2f9c7bf510c8a02db44f6bf47dafe67bf98b4`
- Figure 6 source archive:
  `93eb9b1450e999014ce2c0e1a7dd55d51cc288e1641208f1b19cef8e9d23829b`

## Protected-data statement

Astrocyte outcomes were not inspected, analyzed, recorded, or used for v3
development; an inherited test previously loaded the complete worksheet
programmatically, and this deviation was disclosed before v3 model
development.

The Moffatt GSE334718 candidate archive was not opened, listed, extracted, or
used. Phase 2 reads only the unrelated TDP-43 study and its post-lock outcomes.
