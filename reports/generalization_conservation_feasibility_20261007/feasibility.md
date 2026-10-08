# Evolutionary annotation: coordinate feasibility and limits

The bounded reference pilot succeeded for all six selected Mikl parents and both selected Slc1a2 parents. Their entire original inserts and every admitted edit replay against pinned mm10 reference DNA and coding-3UTR exon/strand metadata. This establishes a practical coordinate route for those parents; it is not a conservation result, localization predictor, new mechanism, genome-wide uniqueness proof or independent biological confirmation.

The fixed design was committed as `53e7b01` before remote mapping. No old sources, outcome tables, models, features, candidate menus or gates changed. No localization, stability, replicate or protected outcomes were selected; no phyloP/phastCons/alignment scores, fitting or paid resource were used. All cases selected by metadata remain present.

## Full admitted metadata coverage

The local author `mouse_3utrs.txt` sequence reference is associated with BioMart GRCm38.p6 in the original LibraryDesign source code. Its headers contain gene and transcript identifiers plus **gene** chromosome/start/end; they omit strand, transcript version and UTR exon blocks. Header coordinates and author scanning offsets alone therefore cannot certify edited-site coordinates.

| Study | Admitted rows | Biological genes/context | Exact parents | One source transcript occurrence | Multiple source transcript occurrences | No exact source UTR / synthetic |
|---|---:|---:|---:|---:|---:|---:|
| Mikl | 13,781 | 187 genes | 2,417 | 1,482 | 935 | 0 |
| Astrocyte | 3,984 | 2 genes | 7 | 4 | 1 | 2 |
| Moffatt | 6,749 | 6 genes | 6 | 0 | 0 | 6 |
| SRLE | 1,744 | 1 engineered HBB reporter | 592 sixmer parents | 0 | 0 | 592 synthetic |

These are exact full-parent occurrences among same-gene entries in **this author reference**, not full genomic mapping coverage. Multiple transcript records may describe the same genomic insert, as the Meis2 pilot demonstrates; they must not automatically be called distinct genomic loci. Conversely, a single transcript occurrence is insufficient until its exon/base vector replays.

Moffatt's preserved admitted lineage identifies Mus musculus for all 4,163 distinct admitted mutation identities across the six genes, using only organism/gene/identity columns. Absence of its six 260-base parent inserts from the older Mikl reference does not prove synthetic origin or absence from all mouse transcripts. Exact author accessions/releases, native-versus-engineered boundaries, or another certified sequence reference are still needed; approximate matching and guessed native coordinates were not substituted. Two Sparc Astrocyte parents also lack exact support in this reference. The original synthetic SRLE inserts and vector/HBB junction contexts have no assigned native coordinates.

## Predeclared pilot and coordinate replay

For each non-SRLE study the fixed rule selected the first/middle/last lexical gene names, then first/last lexical parent IDs, removing repeated indexes. The resulting 13 parents and **all 5,701 corresponding admitted allele IDs** were frozen before mapping. There was no outcome-based selection, replacement of unsuccessful parents or intersection trimming.

UCSC's public catalog identifies `knownGene` as **GENCODE VM23**; `ensGene` was absent and was not guessed. GENCODE's official [M23 release](https://www.gencodegenes.org/mouse/release_M23.html) and [release history](https://www.gencodegenes.org/mouse/releases.html) identify GRCm38.p6/Ensembl98. Exact stable transcript IDs, with version suffixes stripped solely for cross-release identity matching, anchored the pilot. This still does not prove the author's precise transcript annotation version or physical reporter processing.

Four fixed gene regions were requested, totalling **371,056 reference bases**, with eight track/sequence responses totaling **388,283 bytes**. All eight returned HTTP200. Catalog/schema discovery separately downloaded 7,360,002/2,786 bytes before pilot freezing; the 4MB response cap applies to pilot region requests. Each region stayed below the fixed 500kb cap and the total below 2Mb. Every response has URL, access time, HTTP status, byte count and SHA receipt.

| Selected parents | Parent count | Reference outcome | Forward-genome chromosome / expressed strand |
|---|---:|---|---|
| 2810459M11Rik scanning offsets1100/750 | 2 | Unique reference vector | chr1 / + |
| Meis2 scanning offsets1150/600 | 2 | 5/6 transcript matches collapse to one vector per parent | chr2 / − |
| Zscan20 scanning offsets1000/950 | 2 | Unique reference vector | chr4 / − |
| Slc1a2.1 parents3281–3381/4181–4281 | 2 | Unique reference vector | chr2 / + |
| Cdc42, Net1, Trp53 | 3 | No exact source UTR; no remote substitution | Unassigned |
| Sparc parents1041–1121/901–981 | 2 | No exact source UTR; no remote substitution | Unassigned |

The pilot yields **8/13 unique parent vectors**, covering **1,164/5,701 allele rows**: 24 Mikl rows and 1,140 Astrocyte rows. The other 4,537 rows remain unmapped (3,401 Moffatt and 1,136 Sparc). This small deterministic pilot must not be extrapolated into a full-cohort coverage rate; its mapped row count is dominated by the two densely mutated Slc1a2 menus.

An additive independent replay checks 17 transcript-match vectors, all 13 parent statuses and every 5,701 allele identity. It independently reconstructs ordered coding-3UTR exon coordinates, reads bases directly from downloaded genomic DNA, checks complementary orientation, exact whole-parent sequence and each forward-genome reference/alternate nucleotide. All **1,268 edited-site records**, including repeated cell/allele observations, replay; there are **434 distinct forward-genome edited positions**. The eight unique parents split four plus/four minus. All pilot inserts happen to be contiguous within a genomic exon; multiexon logic is covered synthetically but has not been tested by a real junction-spanning parent in this pilot. Complete vectors, rather than endpoint-only intervals, are saved for future junction cases.

Eight invented-coordinate tests passed before freezing, including overlapping occurrences, plus/minus multiexon positions, isoform-vector collapse, strand ambiguity, noncoding exclusion and fixed-region bounds. The independent replay passed with original frozen source/input bytes unchanged before and after. An actual version-specific mature reporter or globally unique locus remains uncertified.

## Public access, scope and next certificate

The [official UCSC API](https://genome.ucsc.edu/goldenPath/help/api.html) documents sequence/track access and coordinate parameters; queries were spaced by more than one second. Its [licensing page](https://genome.ucsc.edu/license/) permits public API/table-data use while retaining source-specific conditions. [Ensembl](https://static.ensembl.org/info/data/index.html) supplies freely available project data and one-based coordinate starts; its [disclaimer](https://sep2025.archive.ensembl.org/info/about/legal/disclaimer.html) retains third-party constraints. [NCBI](https://www.ncbi.nlm.nih.gov/home/about/policies/) permits molecular-data use without transferring submitter intellectual-property rights. No credentials, account, contact, installation or spending occurred; no original all-genome/reference redistribution bundle is proposed.

The bounded historical search found no implemented edited-site phyloP/phastCons or evolutionary-MSA feature experiment. Existing [Mechanism-v2 gene-family grouping](D:/rnaexpress/src/mechanism_v2/gene_families.py) and [FinalShot orthology-based expression mapping](D:/rnaexpress/src/audit/build_finalshot_trans_context.py) already use orthology for different purposes. This route is therefore a newly audited annotation possibility within this project, not discovery of evolutionary constraint or a guaranteed generalization advance.

The next required certificate is a separately declared **full-parent mapping inventory**: exact genome assembly/reference-release and response hashes; original allele IDs; exon/strand/base replay for every mapped parent and edit; all no-map, ambiguous, cap and source-version cases; native versus engineered boundaries; and gene/component coverage with original full menus preserved. The present pilot cannot substitute for that certificate. Moffatt/Sparc require stronger author reference metadata; SRLE remains explicitly synthetic. A later extraction would need separately fixed track/release/species-set hashes and annotation missingness semantics before reading any annotation values.

As the official [mm10 conservation documentation](https://www.genome.ucsc.edu/cgi-bin/hgTrackUi?c=chr17&db=mm10&g=cons60way) explains, phyloP assesses basewise evolutionary conservation/acceleration, while phastCons estimates membership in conserved elements. They annotate the **native coordinate**. A substituted allele does not acquire a new empirical phyloP value merely by changing its base. Constraint at an edited site may indicate disruption sensitivity but cannot specify localization increase versus decrease, alternate-base preference, cell-specific RBP state or transport mechanism. Allele-aware consensus disruption would require independently certified aligned-base evidence and its own fixed design. Missing annotations cannot be treated as zero constraint or selected using model outcomes.

The v1 download helper has a known **transport-failure resume limitation**: an HTTP0 receipt has no cache file, but its existing-receipt branch tries to hash that missing file. The fresh pilot encountered no such failure (allHTTP200), and no retry was performed. A future retry requires a new additive corrected helper with separate tests/manifest; the frozen v1 source and design must remain intact. Request failures would be missing reference data, never negative biological evidence.

## Receipts

- [Fixed pilot design](D:/rnaexpress/results/generalization_conservation_feasibility_20261007/pilot_design_manifest.json): `2013b952034f556aac3ecd31a8a937f90b3b72b5722027ea6e44713733619327`.
- [Local metadata coverage](D:/rnaexpress/results/generalization_conservation_feasibility_20261007/metadata_receipt.json): `fb694de167f3946f7c24d061e905f60fcda0fe912db9fcb8be689d4ed02eb5ae`.
- [Completed coordinate pilot](D:/rnaexpress/results/generalization_conservation_feasibility_20261007/pilot_mapping_receipt.json): `92951bb44bcbbd2284cea3bd4759f4bff70385c529ba39373ef67cf7e2a670df`.
- [Independent coordinate replay](D:/rnaexpress/results/generalization_conservation_feasibility_20261007/independent_coordinate_replay_receipt.json): `f99735b9f9c08d5250965e735c55afd82fc39b61a3586ad3d8bdfccd30114ddf`.
- [Exact parent vectors](D:/rnaexpress/results/generalization_conservation_feasibility_20261007/pilot_parent_mappings.json) and [edited-site coordinates](D:/rnaexpress/results/generalization_conservation_feasibility_20261007/pilot_edited_site_metadata.json); official response receipts reside in [public_metadata](D:/rnaexpress/artifacts/generalization_conservation_feasibility_20261007/public_metadata).
- [Pilot log](D:/rnaexpress/logs/generalization_campaign_20261007/conservation_coordinate_pilot_01.log): `4b1625316d1d6454f62322e8e2139e741f1d2b48e87e03fe9100267e3f853a96`.
