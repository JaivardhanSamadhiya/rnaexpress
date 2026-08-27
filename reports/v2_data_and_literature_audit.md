# RNAddress v2 rescue data and literature audit

## New intervention dataset

The 2025 study [TDP-43 directly inhibits mRNA accumulation in neurites through modulation of mRNA stability](https://pmc.ncbi.nlm.nih.gov/articles/PMC12864922/) introduced a 260-nt neurite/soma MPRA across 16 mouse genes. Every oligo containing a canonical TDP-43 motif (`GTGTG`, `TGTGT`, or `GTATG`) has a companion design in which all covered motif bases are complemented. These are **multi-base motif interventions, not SNVs**.

Reconstruction from the authors' public design code, Gencode vM17, mm10 sequence and the source workbook recovered:

- 7,389 natural oligo identifiers;
- 4,566 mutant identifiers, each with exactly one natural counterpart;
- 4,566 exact matches between reconstructed motif ranges and the mutation ranges encoded in the published identifiers;
- 4,566 complete parent/mutant/effect tuples across 16 genes;
- zero sequence-design mismatches requiring quarantine.

The raw Gencode annotation SHA-256 is `9a55407f2f193f6c74f202522d1a7bac5c928398dc667f4c51acbe837f81ce3`; complete per-source and targeted-mm10-slice hashes are recorded in `data/processed/tdp43_pairing_audit.json`. Raw workbooks remain unchanged and separate from processed tuples; each tuple retains source identifiers and source-table provenance.

## New outcome-blind lock

Before any v2 model was fitted, genes were divided into four construct-count quartiles. Within each quartile, the gene with the smallest SHA-256 of `rnaddress-v2-lock-2026-08-26|gene_id` was locked. The result is 12 development genes (3,560 interventions) and four locked genes (1,006 interventions): Fam160b2, Lars2, Diras1 and Synj2bp.

The locked feature artifact contains no localization outcomes. Exact paths and hashes are in `data/frozen/tdp43_v2_lock_manifest.json`. The full-data aggregate and reconstruction consistency were inspected before this split, but no sequence-associated model performance or per-gene model result was inspected. This is disclosed as pseudoprospective auxiliary evidence, not a perfectly never-opened dataset.

## Literature conclusions that change v2

1. The TDP-43 MPRA reports that motif occupancy/function depends on the surrounding approximately 260-nt context and structural accessibility. This directly supports parent-by-edit interaction and accessibility features.
2. A large combinatorial RNA study found that increasing motif accessibility can improve RBP binding and regulation, and identified local secondary structure as a widespread context gate ([RNA sequence context effects](https://pmc.ncbi.nlm.nih.gov/articles/PMC5107313/)).
3. A broad RBNS analysis found that RBPs sharing short motifs can differ in flanking-sequence and structural preferences ([sequence, structure and context preferences](https://pmc.ncbi.nlm.nih.gov/articles/PMC6062212/)).
4. The Mikl neurite MPRA concluded that adding a short RBP motif is often insufficient and that effects depend on broader context; it also explicitly identified secondary structure as an omitted potential determinant ([Mikl et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC9561380/)).
5. N-zip and the parallel high-throughput localization study support multiple distributed localization contributions, A/G-rich elements, G-quadruplexes, let-7 and AU-rich signals, but also show that simple composition alone is not sufficient ([N-zip](https://pmc.ncbi.nlm.nih.gov/articles/PMC9991926/), [parallel MPRA](https://pmc.ncbi.nlm.nih.gov/articles/PMC9561290/)).
6. RNA foundation models can encode structural and functional information, but existing results do not establish localization intervention ranking. RNA-FM was pretrained on 23 million ncRNAs ([paper](https://arxiv.org/abs/2204.00300)); RiNALMo was pretrained on 36 million sequences and emphasizes structure generalization ([paper](https://arxiv.org/abs/2403.00043)). Their embeddings are optional development-only representations, not evidence by themselves.
7. RNA language-model mutation design has received experimental support in structured functional RNAs ([GARNET](https://www.nature.com/articles/s41467-024-54812-y)), but that domain is too different to justify a zero-shot localization claim.

## Practical conclusion

The strongest defensible rescue is not a larger generic predictor. It is a data-efficient, context-conditioned intervention ranker with explicit interaction, structure/accessibility deltas, grouped validation and a strong forward-search comparator. The new TDP-43 data can test whether context interactions generalize across held-out genes; it cannot be merged with N-zip as if its interventions were single-base edits.
