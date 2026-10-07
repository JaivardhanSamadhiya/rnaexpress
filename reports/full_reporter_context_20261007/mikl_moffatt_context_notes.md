# Mikl and Moffatt reporter context: bounded metadata audit

7 October 2026. No outcome columns, count files, protected measurements or model fits were read/run for this reconstruction. Notebook outputs, R history and saved analysis objects were excluded. The new metadata certificate is [mikl_moffatt_metadata_certificate.json](D:/rnaexpress/artifacts/full_reporter_context_20261007/mikl_moffatt_metadata_certificate.json); its bounded script is [mikl_moffatt_metadata_audit.py](D:/rnaexpress/src/full_reporter_context_20261007/mikl_moffatt_metadata_audit.py).

## Mikl: synthesis, reference cloning and measured RNA are distinct

Measured author TableS2 sequence metadata, rather than the randomly generated prototype library, certifies a synthesis layout `prefix18 | barcode12 | variable150 | suffix18`. Every 13,753 WT scanning record uses prefix `CGAAATGGGCCGCATTGC` and suffix `CACTGCGGCTGATGACGA`; every 12,909 mutant scanning record uses `GACAGATGCGCCGTGGAT` and `AGCCACCCGATCCAATGC`. These are sense-strand sequences. The 18-base prefixes differ at 15 positions and suffixes at 14. All 6,901 unique admitted mutants differ from every exact matched WT synthesis construct by 35–47 of 198 bases; none shares the same12-base barcode with a matched WT.

The [published cloning methods](https://doi.org/10.1093/nar/gkac806) specify forward tails `cacaGGCGCGCCa` and reverse tails `cacaCCTGCAGGa`, followed by the matching 18-base PCR cores. They describe SgsI/SdaI digestion and same-site ligation into a modified pcDNA3-EGFP cassette downstream of GFP. The manufacturer documents sense cuts [SgsI/AscI `GG^CGCGCC`](https://www.thermofisher.com/order/catalog/product/ER1891) and [SdaI/SbfI `CCTGCA^GG`](https://www.thermofisher.com/order/catalog/product/ER1191).

The outcome-free synthetic orientation/cut certificate derives:

```
PCR sense224 = cacaGGCGCGCCa + original198 + tCCTGCAGGtgtg
sense cuts0 =6 and218; retained sense fragment =212nt
restored local duplex216 = GGCGCGCCa + original198 + tCCTGCAGG
variable150 interval0 = [39,189)
```

The two recognition sites are outside the complete198-base synthesis construct. Both primer cores and the barcode survive the described reference DNA cloning. The outer lowercase four-base pads are removed. This inference assumes the described orientation, cleavage and ligation; it does not certify an actual final clone or mature RNA processing. Replacing mutant-specific constants with WT constants would contradict this local DNA design.

[Author notebook source](https://github.com/martinmikl/RNAloc_MPRA) identifies reporter-read anchor `GAGCGCACCCGTCCGAGC`. A fixed third public example R2 read contains that 18-base anchor, `TAAGGCGCGCCA`12, the exact WT18-base core, a 12-base barcode and part of the insert. It supports local retention in a targeted reporter amplicon. The README does not uniquely identify that example's RNA-versus-DNA sample, so it cannot independently certify mature RNA. The first three sequence-only reads and their fixed indices are saved in the certificate; no counts were computed.

The prototype author dictionary has 47,989 records and all barcode fields are 14nt, equal to synthesis slice `[16:30)` (last 2 primer bases plus the true 12-base barcode). Example code starts its mapping slice 46 bases after the18-base anchor and accepts 12/14 bases. Its UMI slice is 12 nt, while the methods describe 15 nt. This legacy example code is not proof of the exact published counting pipeline. Its README explicitly warns randomly generated motif mutants need not match the measured library. Current measured TableS2 sequences take precedence.

The complete modified master cassette has not been sequence-certified. The paper names Addgene 13013; the catalog's [pcDNA3-EGFP record is 13031](https://www.addgene.org/13031/). That discrepancy must remain explicit. The base-vector map is not the final modified cassette. Exact reporter start, splicing, cleavage/polyadenylation products and complete RT-primer position remain uncertified. Neither 198 nor 216 nt is a certified complete mature reporter RNA.

The [original-author lineage audit](D:/rnaexpress/reports/generalization_rbp_20261007/original_author_lineage_audit.md) independently verified the 150-base insert parent semantics and author numerical contrasts. A common reference subtraction and fixed mutant-versus-WT additive constants cancel when ranking candidates within one parent. Context-dependent nonlinear effects and candidate-specific barcode effects can remain. The construction difference therefore limits isolated-small-edit causal interpretation; it alone does not invalidate within-parent ranking or explain its performance.

## Moffatt: certified variable insert and PCR handles only

The author sequence dictionary contains 17,294 mutation records of 300 bases, all `GCTTCGATATCCGCATGCTA | variable260 | CTCTTGCGGTCGCACTAGTG`. Both cached public [SHAPE design](https://github.com/charliemoffatt/LE_SHAPE_Summary) source documents explicitly label these 20-base flanks PCR handles. This establishes synthesized DNA sequence and the central 260-base insert. It does not establish whether either handle persists in a final plasmid/transcript; restriction-site substrings alone cannot settle the cloning design.

Official free GEO metadata for fixed [GFP sample GSM9795691](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM9795691) and [firefly sample GSM9795683](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM9795683) describes polyA RNA, targeted reporter-transcript RT-PCR with UMIs, GFP/firefly reporters and bowtie2 oligo extraction. Selected method lines and URL/hash receipts are saved under `artifacts/full_reporter_context_20261007/reporter_sequence_metadata`. No linked count file was downloaded. Those records omit exact vector/primer/junction and processing boundaries. BioRxiv fulltext access returned403 during this audit; that access limit is not evidence no public record exists.

No complete expressed GFP or firefly reporter is uniquely reconstructed. A generic coding sequence, guessed restriction product or arbitrary start/polyadenylation boundary must not be used as measured full-context truth. The existing 260-base parent/allele reconstruction remains certified within its declared scope.

## Provenance pins and stopping rule

The machine certificate pins every inspected sequence/code source, its own script, canonical metadata roster and lineage metadata. Key source hashes:

| Source | SHA256 |
|---|---|
| Measured Mikl TableS2 | `c3b3257976af7cd2253aa5503a8a53f374e5730fe012f2320f449eee06d67ee3` |
| Mikl article cache | `1d0b3a02d7097b1af0c215eb02073a3e12e97f53da559f7c46d84065f251c05c` |
| Author LibraryDesign source | `1434be13ae30d94619b06c9df19a75c0a2d111c85d9f59b39f5f262ee8de3720` |
| Author mapping source | `3cea4982d799e57838b7ccca17a3b5f60fb602b5b9fda4f877bc83699575ad14` |
| Author prototype sequence dictionary | `cabb3b6d5fe4755d06a2ecf5475f56693355a5d5d9a94aba726dc806c8f36eae` |
| Fixed public example R2 FASTQ | `c2761082047fd201834a2f24f13799d8926ee112352e599c49c188be3bbd03bb` |
| Moffatt sequence dictionary | `202c019bfbd91e0a5d4f94da2b2b340e4f76ceda10d7c73f75f08090d346195e` |

Admit a whole-reporter feature experiment only after exact final construct, reporter-to-assay mapping, retained barcode records/aggregation and supported RNA start/splice/cleavage states are resolved without outcomes. Otherwise local retained DNA is provisional provenance metadata, not certified full RNA. The companion [feasibility report](D:/rnaexpress/reports/full_reporter_context_20261007/feasibility.md) addresses SRLE. Current experiment inputs, protocols and frozen conclusions remain unchanged.
