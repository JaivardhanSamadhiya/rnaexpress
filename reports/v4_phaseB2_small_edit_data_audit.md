# RNAddress v4 Phase B2 small-edit public-data audit

Audit date: 2026-09-01. This audit was completed before B2 model fitting.

## mutREL-seq

Primary record: *U1 snRNP regulates chromatin retention of noncoding RNAs*, public sequencing accessions `GSE134287` and `SRP214639`.

- Assay: chromatin/cytoplasm retention rather than neurite/soma localization.
- Intervention landscape: random mutagenesis of one principal 162-nt NXF1 chromatin-retention element.
- Public scale: approximately 469 observed mutation/deletion events reconstructed in the prior RNAddress literature/data audit from public supplementary/source records.
- Pairing: exact variants and enrichment outcomes are reconstructable in principle from the mutREL-seq design and public records.
- Independence: one principal parent; no held-parent test is possible.

Decision: **audit-only, excluded from B2 training and model selection**. Its single parent cannot identify cross-parent ContextValue, and using it to calibrate a parent×edit model would overweight one nuclear-retention mechanism. It may remain future single-parent sanity evidence under a separate protocol.

## 2026 nuclear-speckle SNVs

Primary record: *RNA localization to nuclear speckles follows splicing logic*, DOI `10.1093/nar/gkag174`, imaging outcomes in Supplementary Tables S3/S6, verification sequencing in `GSE318459`, and analysis code at Zenodo `18598678`.

- Assay: microscopy partition coefficient for nuclear-speckle localization in HeLa cells.
- Biological SNV pairs: two parent-exon comparisons—SMN1 versus the single-nucleotide-different SMN2 exon 7, and COLQ exon 16 WT versus its disease-associated mutant.
- Exact SNVs: two biological SNV pairs across two parent exons.
- Outcome mapping: construct names map deterministically to partition coefficients in Supplementary Table S6; GEO contains long-read construct-verification data, not the localization endpoint.
- Compartment mismatch: nuclear speckles are not neurite/soma localization.

Decision: **audit-only, excluded from B2 training and model selection**. Two pairs cannot support representation calibration or independent statistical evaluation. The direction of both effects is biologically useful sanity evidence only.

## Frozen auxiliary policy

Neither source enters B2 residual labels, nuisance fitting, model selection, thresholds, gates or transfer metrics. B2 therefore remains based only on certified Mikl, TDP-43 and Moffatt outcomes. Performance “with auxiliary data” is not run because the sources fail the pre-result eligibility threshold of at least five independent parents and at least 100 exact small edits with deterministic assay-compatible outcomes.
