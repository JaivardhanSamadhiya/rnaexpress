# Sparse exact-rule support: defer broad modeling

The outcome-blind design was frozen before coverage and committed at26c336d. The primary-paper pieces, both linear orders and10–25 strictly intervening bases were not changed after counts. The standard-library scan used only NEXT's two certified six-field sequence/metadata inventories. Nine invented-sequence/schema controls passed. No labels, feature matrices, predictors, localization decisions or protected outcomes were read; zero models were fitted.

| Assay/input | Total intervention rows | WT-containing-pair rows | Mutant-containing-pair rows | Rows changing paired geometry | Changed parent contexts | Changed biological components | Unique changed allele pairs |
|---|---:|---:|---:|---:|---:|---:|---:|
| Astro original/encoded |3984|0|7|7|2|2|7|
| Mikl original/encoded |13781|114|146|50|50|17|25|
| Moffatt original/encoded |6749|0|11|11|6|3|9|
| SRLE original6 |1744|0|0|0|0|0|0|
| SRLE encoded46 |1744|5|5|10|7|1|10|

Mikl's17 units are certified whole-gene components among187 supplied genes. Its50 affected rows are the two measured cells of25 unique allele pairs; they are not50 independent sequences or genes. The other assays' supplied units are conservative biological components. Overall original support is68/26258 rows in22 components; encoded support is78/26258 rows in23 components. The independent support is sparse, with only one SRLE construction component and two Astro components in the full underlying cohort. These are sequence coverage counts, not biological effect measurements.

The prespecified single-piece controls have broader edit support. Original isolated-CGGAC count changes occur in24 Astro rows,123 Mikl rows,59 Moffatt rows and zero SRLE rows; second-piece count changes occur in354,2474,837 and106 rows respectively. Old ACACCC-proxy changes occur in10,54,18 and1 rows. Encoded SRLE adds10 isolated-CGGAC changes and376 second-piece changes; its old proxy remains1. Raw second-piece prevalence cannot replace paired-site evidence.

There is no observed gained/lost-pair turnover with unchanged net count in either inventory. No geometry-changing row leaves both isolated recognition-piece counts unchanged. Those observations do **not** establish that general geometry is redundant with isolated counts: context determines whether changed pieces have an appropriately spaced partner. A special exact redundancy does occur in SRLE encoded46: the complete set of `(pair_count_delta, isolated_CGGAC_delta)` values is `{(-3,-1),(0,0),(3,1)}` across all1744 rows. Thus its paired-count delta is exactly three times the isolated-CGGAC delta, because this fixed construction supplies the other recognized pieces. Its apparent10-row local-arm support adds no independent paired-count information beyond that control. This is local construction context, not a uniquely reconstructed mature HBB reporter or certified IGF2BP1 occupancy.

**Recommendation:** defer a broad fitted zipcode-geometry campaign. The exact rule is a biologically grounded refinement of the old ACACCC proxy, but the admitted edit roster supplies little independent paired-site support. Do not broaden recognition strings, change spacers, exclude unfavorable assays, invent gene independence or inspect localization labels to rescue it. This metadata result neither disproves the established binding/localization mechanism nor proves absence of motifs in unknown full mature reporters. A future narrow mechanistic question would need additional independently certified constructs and prespecified single-piece/proxy controls; it would not replace the current universal/generalization gates.

All counts are preserved in `results/generalization_zipcode_geometry_20261007/coverage_by_assay.csv`; row-level sequence-only summaries are in `coverage_rows.csv.gz`. Coverage receipt SHA256: `756e196f33c65476f7c7a8539222e3f7cd14b14a722896c87b386c54ccbf224a`. Design freeze SHA256: `c8c8033f9863526a3cac87d14f11c16cce1d7233cd6e1e54750ea1487fcbaded`. Source definitions, tests and protocol remain frozen and unchanged.
