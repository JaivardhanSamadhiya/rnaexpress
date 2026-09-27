# GSE334718 admission: EXPOSED

**This resource cannot provide an untouched third-system test.** The project deliberately unsealed it for v4 development on August 31, 2026, at `2026-08-31T07:19:02.0735799Z`. The pre-unseal protocol was committed at `bdbd9f1fbf30ea0094ea7bf7f029c4f828ec82ed`; the irreversible development-data transition was recorded at `e5cec4985cdc841673b95f5e9b63b5662b5ffb9d`. Later outcome-driven development is already part of project history. No mutation table or count member was reopened for this admission.

Evidence comes from the existing `reports/v4_moffatt_unseal_log.md` and `reports/v4_moffatt_source_truth_audit.md`, rather than another outcome access. Official provenance is [GEO GSE334718](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE334718), [the study DOI](https://doi.org/10.64898/2026.06.09.731215), and [PMC13277945](https://pmc.ncbi.nlm.nih.gov/articles/PMC13277945/). The archived audit records the title as *Robust mammalian RNA localization elements are large and multipartite*. A fresh direct GEO browser request was unavailable; historical accession/source provenance remains the basis for this decision.

| Admission field | Established historical metadata |
| --- | --- |
| Biological/reporting structure | Neuronal soma/neurite fractions; GFP and Firefly reporters |
| Replicates | Four biological replicate labels per reporter/fraction/family |
| Full sample design | Five families × two reporters × two fractions × four replicates = 80 samples |
| Parent length | 260-nt insert with 20-nt flanks on each side |
| Parent breadth | Ten labels/eight unique sequences across all families; mutation reconstructs six parents |
| Mutation class | 14,235 certified random substitution interventions within declared windows, generally three designs/window; not a saturated single-SNP library |
| Other families | Sufficiency replacement, necessity deletion/padding, regional shuffle, structure-directed mutations |
| Endpoint | Author WT-normalized log2 neurite enrichment, reporter-specific; raw UMI fraction ratios are separate diagnostics |
| Exact mapping | Existing certified sequence dictionary and deterministic parent/operation reconstruction; unmapped/malformed rows excluded explicitly |
| Small-edit support | Historical full-library audit found only six exact one-base changes, all in one parent context |
| Candidate alternatives | Certified designed sequences can be enumerated, but are mixed-window/mixed-edit-size interventions, not all three SNP alternatives at each position |
| Prior influence | Outcome access and extensive v4/later model development; irreversible exposure |

The original archive SHA-256 is `abc6e571ed68833e3fb0c0028209303a0f468347ac5f6efbeffd788c35c7ade1`. The archived dictionary SHA-256 is `202c019bfbd91e0a5d4f94da2b2b340e4f76ceda10d7c73f75f08090d346195e`. This audit reads the prior records, not the archive contents. Parent-sequence duplicates, sparse exact-SNP support and assay-family-specific normalization also limit direct compatibility.

**Decision: EXPOSED.** The conditional third-system untouched-validation branch stops. Reusing it would be an explicitly exposed development/replication analysis under a different protocol, never restored independent confirmation. No additional third-system fit was performed.
