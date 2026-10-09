# Exact native WT fragment identities
All13 fixed UCSC/NCBI requests succeeded, totaling44,501bytes. The bounded worker peaked at34.29MiB. Seven additional native WT140nt fragments have exact reference matches. Together with the preserved IRF2BP1 pilot, all8 native WT fragments across7 nominal lineages now have whole-fragment reference matches.

| Author lineage | Fixed reference interval, 0-based half-open | Strand / annotation |
|---|---|---|
| HIAT1 | hg19 chr1[100548728,100548868) | +, MFSD14A, NM_033055 |
| MGEA5 | hg19 chr10[103545443,103545583) | -, OGA, NM_012215 / NM_001142434 |
| PGBD4 | hg19 chr15[34395390,34395530) | +, PGBD4, NM_152595 |
| AP1S1 (source prefix APIS1) | hg19 chr7[100804125,100804265) | +, AP1S1, NM_001283 |
| SMARCA2 | hg19 chr9[2161706,2161846) | +, SMARCA2, seven exon-covering annotations |
| NORAD fragment1 | NR_027451.1[1396,1536), .2[1400,1540) | Forward, unique in each version |
| NORAD fragment2 | NR_027451.1[2593,2733), .2[2597,2737) | Forward, unique in each version |

All5 genomic matches fall within annotated RefGene exons on the declared strand. SMARCA2 matches identically in the fixed hg38 comparison; this does not uniquely identify author assembly. NORAD.1 is5,378nt and.2 is5,339nt; archived bodies show explicit versions, and no latest-record substitution occurred. Full-length version differences must not be silently mapped onto the reporter.

Separate reconstruction from every preserved source body replayed1,400base comparisons, all full-fragment matches, RefGene exon coverage and version lengths. It used separate GenBank parsing, sliding-window matching and complement arithmetic, sharing only resource/identity utilities. Same root/runtime execution, not independent agent confirmation. Exact WT fragments do not certify engineered backgrounds, complete mature reporter RNA,3UTR identity in every transcript or original CLIP peak-file provenance.

The original named lineages and ancestry artifacts remain unchanged. A cached gene/transcript alias screen against the26,258-row canonical roster found0matches; exact/RC and61nt fragment screens also found0. This is a limited metadata certificate, not complete orthology or common-ancestry exclusion.

Sources: [UCSC API](https://genome.ucsc.edu/goldenPath/help/api.html), [versioned NORAD RefSeq](https://www.ncbi.nlm.nih.gov/nuccore/NR_027451.2).
