# RNAddress v4 Mikl source-truth audit

## Verdict

Mikl/GSE173098 is certified as a provenance-complete development intervention source after reconstructing its biological 150-nt test inserts from first principles. The certified set contains **11,900 deterministic parent-mutant interventions across 224 genes and 5,830 independent parent contexts**. It is not an exact-SNV landscape: only 13 interventions are one-base substitutions, while the median observed edit is five bases.

This audit corrects the prior exploratory representation that compared complete 198-nt synthesis constructs. Those constructs include primers and a barcode and are not the biological intervention sequence. No historical model was rerun and the corrected records are new Phase A development records only.

## Primary sources and immutable identity

- Study: Mikl et al., *A massively parallel reporter assay reveals focused and broadly encoded RNA localization signals in neurons*.
- DOI: [`10.1093/nar/gkac806`](https://doi.org/10.1093/nar/gkac806); GEO: [`GSE173098`](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE173098).
- `TableS2.csv`: 47,347 analyzed constructs; SHA-256 `c3b3257976af7cd2253aa5503a8a53f374e5730fe012f2320f449eee06d67ee3`.
- `TableS1.csv`: gene identifiers; SHA-256 `089137d72f9a203f1ba254ef712aa9ba2c171aa113de87df34244c2d2c75c2c5`.
- `GSE173098_RNAloc_MPRA_counts.csv.gz`: 47,989 raw-count constructs; SHA-256 `809e4d3f286edd3373ebf2dfb3b93a658179a83eac85007a04ad381612f44d99`.
- Full file sizes, output hashes, Python/package versions, processing commit, and processing-script hash are in `results/v4_phaseA/source_manifest.json`.

## Construct and sequence reconstruction

The paper defines a 198-nt synthesis construct as:

`18-nt forward primer + 12-nt barcode + 150-nt variable test insert + 18-nt reverse primer`.

Accordingly, the certified biological sequence is Python slice `[30:180]`, or source bases 31–180 inclusive. Every source construct has length 198, and every extracted test sequence is exactly 150 canonical DNA bases.

The complete 198-nt sequence is unique in both the analyzed supplementary table and the raw GEO count matrix. All 47,347 analyzed constructs join exactly and one-to-one to the GEO matrix; 642 GEO constructs have no analyzed-table row and are not forced into the audit.

The source design contains 13,753 `wt scanning 50` rows and 12,909 `mut scanning 50` rows. Parent reconstruction is restricted to these two declared subsets. For each mutant:

1. candidate WT rows must have the exact same source gene and 3′UTR position;
2. the source `changes` field supplies the original motif string;
3. a candidate parent is valid only if every changed base lies within an occurrence of that declared motif in the 150-nt parent;
4. the parent is accepted only if exactly one unique parent sequence satisfies the rule.

No row-order, nearest-effect, sequence-similarity threshold, or outcome-dependent choice is used.

## Certified scale and exclusions

| Quantity | Result |
| --- | ---: |
| Certified interventions | 11,900 |
| Certified genes | 224 |
| Independent exact parent contexts | 5,830 |
| Exact one-base substitutions | 13 |
| Mean / median / maximum changed bases | 5.624 / 5 / 40 |
| Missing gene-position parent key | 770 |
| No unique semantic parent | 239 |
| Ambiguous accepted parents | 0 |

The 1,009 excluded mutant rows remain explicit in `results/v4_phaseA/exclusion_audit.csv`. They are not imputed, approximately paired, or silently dropped.

## Outcomes, replicates, and uncertainty

The assay has paired soma and neurite measurements in **three biological replicates** for each of CAD and Neuro-2a. The certified point outcome is the author-processed mutant-minus-parent `logFC(neurite/soma)` within each cell line.

For uncertainty, Phase A independently reconstructs a raw-count log2 neurite/soma value in each replicate using a fixed 0.5 pseudocount. When a parent has multiple barcoded WT constructs, parent ratios are averaged within replicate before subtracting them from the mutant ratio. The stored uncertainty is the standard error of the three paired replicate deltas. All three replicate deltas are retained as semicolon-delimited machine fields. This raw-count uncertainty is labeled separately from the author-processed effect and is never substituted for it.

All 11,900 certified interventions have finite CAD and Neuro-2a uncertainty estimates.

## Direction balance

| Cell line | Increase | Decrease | Exact zero |
| --- | ---: | ---: | ---: |
| CAD | 4,555 | 7,308 | 37 |
| Neuro-2a | 4,443 | 7,428 | 29 |

Decrease/disruption examples are therefore the majority in both cell lines, but each direction has thousands of observations. Direction is not interchangeable across cell lines and must be retained as an assay-specific outcome.

## Leakage-safe use

The required split unit is `parent_id`, which incorporates source gene, 3′UTR position, exact parent sequence, and a sequence hash. All variants, barcodes, cell-line outcomes, and replicates belonging to one parent stay in one fold. Gene-held-out evaluation is the stricter sensitivity analysis.

Mikl supports small- and motif-scale intervention learning across many contexts. It does not by itself justify an exact-SNV product claim or a universal cross-cell-line outcome head.

## Machine artifacts

- `results/v4_phaseA/mikl_interventions.csv.gz`
- `results/v4_phaseA/common_intervention_outcomes.csv.gz`
- `results/v4_phaseA/exclusion_audit.csv`
- `results/v4_phaseA/edit_distribution.csv`
- `results/v4_phaseA/phaseA_summary.json`
- `results/v4_phaseA/source_manifest.json`
