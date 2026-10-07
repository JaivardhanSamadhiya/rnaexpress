# Original-insert similarity audit and robustness feasibility

7 October 2026. **A stricter similarity exclusion is computationally feasible and changes the source training roster modestly.** This is metadata-only evidence; it reports no new localization metric, model fit or positive generalization result. Existing frozen experiments and their verdicts are preserved.

The primary criterion was declared before project graph calculation: unit-cost global Levenshtein distance <=30 over complete original150-nt inserts, in their recorded orientation. It allows indels. Thus >=80% normalized edit similarity does **not** mean >=80% ungapped sequence identity, local-overlap identity or biological homology. No cutoff grid or favorable threshold selection was performed. [The protocol](D:/rnaexpress/reports/generalization_similarity_crosscell_20261007/protocol.md) records the single criterion and future split boundaries.

The metadata loader reads only previously admitted original sequences and known gene/cell/fold fields, excluding measured_delta. All9,318 unique parent/mutant alleles from13,781 Mikl rows and187genes were deduplicated. The installed, free RapidFuzz3.14.1 native scorer performed43,407,903 unordered nonidentical allele comparisons, in blocks64 with1worker. Full graph construction took36.17seconds; its largest temporary distance buffer was1,192,704bytes. Eight existing runtime/source/license files are hashed, including the scalar AVX2 scorer and native matrix implementation. There was no installation, download, cloud service or cost.

There are no exact shared cross-gene alleles, but20 nonidentical close cross-gene allele pairs. Four direct gene edges create a single four-gene transitive family, reducing187 original gene components to184 similarity families:

| Gene pair | Minimum global edit distance | Witness Hamming disagreement | Close allele pairs | Inherited folds |
|---|---:|---:|---:|---|
| colec12–arpc1b |27|95|2|0/0|
| colec12–agtrap |30|91|1|0/2|
| colec12–cdk15 |26|55|15|0/0|
| arpc1b–agtrap |30|106|2|0/2|

Every edge witness was independently checked with full dynamic programming and its original gene ownership. Independent adjacency flood-fill reproduced the184 components; independently implemented set logic reproduced all6outer and12inner support counts. Another100 fixed, outcome-blind original sequence pairs matched independent exact dynamic-programming scalar scores and the cutoff behavior. Six bounded synthetic tests passed: distance/matrix symmetry and cutoff, indel-versus-Hamming distinction, transitive grouping, multi-gene exact ownership, inherited target retention/global closure, and native runtime binding. These checks do not substitute for a separate reviewer or a committed supervised prefit freeze.

The colec12–cdk15 witness has only26 and15 distinct4-mers; other witnesses contain83–92. This is a warning that low complexity can bridge genes without demonstrating evolutionary or functional relatedness. The algorithm retains every such link. It does not mask repeats, discard unfavorable links, assign paralogy or infer biological mechanism. Large Hamming disagreement with a small global edit distance also illustrates why these counts cannot be relabeled ungapped identity.

| Crossed direction / outer fold | Original source rows | Source rows after similarity purge | Source genes after purge | Extra rows removed | Target rows retained |
|---|---:|---:|---:|---:|---:|
| CAD→Neuro-2a /0|4,099|4,073|115|26|2,788|
| CAD→Neuro-2a /1|4,250|4,250|120|0|2,641|
| CAD→Neuro-2a /2|5,429|5,343|135|86|1,463|
| Neuro-2a→CAD /0|4,104|4,078|115|26|2,790|
| Neuro-2a→CAD /1|4,251|4,251|120|0|2,639|
| Neuro-2a→CAD /2|5,429|5,343|135|86|1,460|

All six outer source rosters and twelve source-only inner training/validation rosters remain nonempty. Inner training retains at least48genes. Existing13,781 target rows, parent menus and both ranking directions are unchanged. Similarity grouping uses the full original allele roster, including target sequence metadata only for exclusion; it is never recomputed from a narrower source fold. The previously reviewed component/gene/exact-allele exclusion remains mandatory before this additional family purge.

A separately frozen follow-up is justified as a **robustness check**, rather than a new representation method. Its scientific question would be whether a result from the original crossed-cell/gene experiment survives removing this identified sequence-similarity connection. All matched controls must be refit under the same stronger source/inner masks, with unchanged target menus and source-only hyperparameter selection. No claim may rely on only purging a favored model. The exact feature arrays could be reused without recomputing structure or pretrained embeddings. Source roster differences require new training-input bindings and immutable checkpoints; existing fitted checkpoints cannot be relabeled as purged fits.

Future uncertainty should be prespecified carefully: the point estimate can retain equal original-gene weighting for comparability, while a paired bootstrap can draw one shared weight per global similarity family across both cells. Members of the four-gene family then receive the same resampling weight. This is a proposal, not a newly frozen supervised gate; root review must fix weighting/control/gate details before fits. With only three original genes merged, this does not address more distant evolutionary families or all short-motif sharing.

The [mRNABench primary preprint](https://pmc.ncbi.nlm.nih.gov/articles/PMC12265608/) motivates leakage controls and describes paralog-based transitive groups, which differ from this150-nt insert graph. [PubMed](https://pubmed.ncbi.nlm.nih.gov/40672173/) explicitly identifies the cited version as a preprint; [the author repository](https://github.com/morrislab/mRNABench) provides its split implementation. This note does not present its broad benchmark findings as independently replicated evidence. Native metric and matrix semantics are documented by [RapidFuzz](https://rapidfuzz.github.io/RapidFuzz/Usage/distance/Levenshtein.html) and [its matrix API](https://rapidfuzz.github.io/RapidFuzz/Usage/process.html); executed version3.14.1 is pinned separately from the live documentation version. No external weight or dataset license was inferred from code licensing.

Receipts: [preanalysis manifest](D:/rnaexpress/results/generalization_similarity_crosscell_20261007/preanalysis_manifest.json), [graph certificate](D:/rnaexpress/results/generalization_similarity_crosscell_20261007/metadata_graph_receipt.json), [independent metadata check](D:/rnaexpress/results/generalization_similarity_crosscell_20261007/independent_metadata_check.json), [split counts](D:/rnaexpress/results/generalization_similarity_crosscell_20261007/split_support.csv), [direct edges](D:/rnaexpress/artifacts/generalization_similarity_crosscell_20261007/direct_gene_edges.csv). The graph certificate SHA256 is `a4fb230cb8d46b9351f49b9888acb06285d01c4ee486d49f812282dad5d294ce`; it pins the original metadata hash, six prepared source files, the predeclared protocol, native runtime and graph/count outputs. It is an outcome-blind sequence certificate, **not** a supervised prefit manifest. No fit has been run in this namespace.
