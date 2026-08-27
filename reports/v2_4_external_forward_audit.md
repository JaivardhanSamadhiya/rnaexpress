# RNAddress v2.4 external forward-source audit

Frozen on 2026-08-27 before external embedding/model development and before any v2.4 N-zip fit. TDP-43 locked outcomes and astrocyte outcomes remained sealed.

## Source semantics

The Arora supplementary legends identify Table S1 as GFP/CAD, S2 as firefly/CAD, S3 as GFP/N2A and S4 as firefly/N2A. Supplementary File 1 contains the 260-nt biological inserts without the 20-nt PCR handles. The source has 7,374 labeled FASTA records plus 750 unlabeled 260-nt controls; all 7,360 result IDs map one-to-one to a 260-nt labeled sequence. There are 7,115 constructs with all four localization measurements, and the four tables contain 7,217-7,326 nonmissing outcomes individually.

The Mikl article and design define each 198-nt library sequence as an 18-nt primer, 12-nt barcode, 150-nt test insert and 18-nt primer. Only positions 30:180 are therefore biological input to the forward model. The natural `wt scanning 50` subset contains 13,753 tiles.

Primary literature: [Arora et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC9561290/) and [Mikl et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC9561380/).

## Leakage audit

- Arora has zero gene overlap with the 15 N-zip parents, zero complete-parent containment and zero shared exact 31-mers.
- Mikl contains seven normalized N-zip genes. Four N-zip parents occur completely inside one or more Mikl constructs, and seven parents share at least one exact 31-mer with Mikl.
- Restricting Mikl to natural `wt scanning 50` tiles and globally excluding every normalized N-zip gene leaves 13,309 rows. This decontaminated cohort has zero complete-parent containment and zero exact 31-mer overlap with every N-zip parent.
- These exclusions are global, not fold-specific, so no held-out N-zip parent can enter external pretraining through a sequence or gene proxy.

## Reliability implication

Arora's pairwise assay Spearman correlations range from 0.041 to 0.204. This agrees with the paper's conclusion of statistically significant but incomplete concordance and rules out treating a simple four-assay average as noise-free ground truth. External model development must preserve assay-specific heads or otherwise demonstrate its aggregation rule using gene-grouped validation on external data only.

The complete row counts, table mappings, SHA-256 values, gene lists, missingness, correlations and per-parent overlap checks are frozen in `data/frozen/v2_4_external_forward_audit.json`. The audit code reads only N-zip identifiers and parent sequences; it does not read N-zip outcomes or either sealed outcome lock.
