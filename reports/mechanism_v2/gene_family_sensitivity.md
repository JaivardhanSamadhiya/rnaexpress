# External gene-group sensitivity

The sensitivity now has a reproducible, outcome-independent grouping inventory.
It uses the official HGNC complete gene set and HCOP human–mouse orthology table
retrieved on 10 September 2026. HCOP aggregates orthology assertions from multiple
databases; HGNC provides curated gene-group memberships. These are public CC0
annotations, not localization measurements. [HGNC downloads](https://www.genenames.org/download/),
[HCOP documentation](https://www.genenames.org/help/hcop/).

Mouse Ensembl IDs and approved mouse symbols are matched exactly (symbols case-
insensitively). At least three distinct supporting orthology databases are
required. Repeated database names in an HCOP record count only once. Supported
multiple human orthologs contribute the union of their recorded group memberships;
no favorable mapping is selected. Available groups include broad functional or
structural categories, so this is a conservative gene-group split, not a complete
mouse paralog phylogeny. The mapping rule never uses localization outcomes.

Shared groups are merged transitively with the existing 95% all-allele/gene
components. Incomplete annotations are not treated as proof of distinct singleton
families. Only completely annotated connected family components enter either
side of this sensitivity's train/test split. The primary folds are unchanged.

| Quantity | Count |
| --- | ---: |
| Original biological units | 213 |
| Units with supported group annotation | 183 |
| Supported ortholog but no recorded group | 26 |
| No supported ortholog | 4 |
| Eligible connected gene-group components | 96 |
| Eligible candidate rows | 72,872 |
| Excluded candidate rows | 20,336 |

Coverage by source: Mikl 165/189 units, Moffatt 6/8, TDP43 12/16. All excluded
units and reasons are recorded. Exclusion reflects external annotation coverage,
not unfavorable performance. The 96 groups have outcome-blind five outer and
three inner folds. This inventory is ready for an annotated-only sensitivity;
no family-held-out model results have been produced yet.

Input SHA-256 values:

- HGNC complete set: `6a1423507780773fbcb373eaef84dba5f9357b36e7219db2aeaae13d8a42d62b`.
- HCOP human–mouse: `0cfb78e4eb273751e0557e8230445a60e844bfaf958e32740d4a266fb41cdb35`.
- Final sensitivity inventory: `bca7d082e57076c5ea06cbe92106cdbdef1bc9c69e03c7f16db2e143753f9b16`.

The complete rule is `configs/mechanism_v2/gene_family_design.json`; exact
memberships, merge edges, source coverage and fold mappings are in the paired
annotation/split files and manifest. Further ontology releases cannot silently
change this sensitivity after evaluation.
