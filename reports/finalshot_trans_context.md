# FinalShot outcome-blind trans-context reconstruction

Freeze date: 2026-09-02

Resource-audit base commit: `f2b2c01`

## Decision

FinalShot will use a deliberately small **RBP-expression proxy** for the two
development cell lines, CAD and Neuro-2a (N2A). It is an RNA-abundance proxy,
not protein abundance, active RBP concentration, CLIP occupancy, or a measured
intervention response. It was constructed before any FinalShot localization
model was evaluated.

The source is [GSE67828](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE67828),
the Taliaferro et al. soma/neurite transcriptome study associated with
DOI `10.1016/j.molcel.2016.01.020`. This is the closest public dataset that
contains both mouse CAD and N2A cells and the relevant soma/neurite states. It
is not represented as an exact batch match to Mikl, TDP-43, or Moffatt.

## Exact samples

Only the twelve untreated cell-line samples were prespecified and extracted:

- N2A soma: `GSM1656708`, `GSM1656709`, `GSM1656710`;
- N2A neurite: `GSM1656711`, `GSM1656712`, `GSM1656713`;
- CAD soma: `GSM1656714`, `GSM1656715`, `GSM1656716`;
- CAD neurite: `GSM1656717`, `GSM1656718`, `GSM1656719`.

The perturbation, cortical-neuron, Mbnl-knockout, control-siRNA, and separate
CAD serum-comparison samples in the archive are excluded. The complete GEO
archive is 74,485,760 bytes with SHA-256
`e2bce64320274f7a81b87598235934f6c6af0636126d6deca14ecc5b42a488c2`.
Every selected member has a separately frozen SHA-256 in
`results/finalshot/context_source_manifest.json`.

GEO reports mouse poly(A) RNA, porous-membrane soma/neurite fractionation,
TopHat 2.0.12 or STAR 2.0.4d alignment, Cufflinks 2.1.1 expression, and an mm9
genome supplemented with alternative isoforms. These are old FPKM estimates;
they are adequate only as a coarse fixed context covariate.

## Gene resolution and eligibility

RBPNet contains 103 human HepG2 checkpoint channels. The frozen MGI snapshot
maps those symbols to mouse. GSE67828's Cufflinks tables frequently put `-` in
`gene_short_name` and use sample-specific `CUFF.*` identifiers, so exact symbol
matching would falsely classify most RBP genes as absent.

The outcome-blind resolver therefore uses the UCSC mm9 `refGene` table,
SHA-256 `7eb239607afa72581e1eebb9c90156e8d83d871953118357b93d39df88208ac4`.
For each canonical mouse RBP gene it unions RefGene transcript coordinates on
the dominant chromosome and selects the overlapping Cufflinks locus by:

1. exact case-insensitive symbol match, when present;
2. maximum interval Jaccard overlap;
3. maximum target-span coverage as the deterministic tie breaker.

`Qki` is resolved to its mm9 RefGene name `Qk`. MGI links human `LARP7` both to
protein-coding `Larp7` and `Larp7-ps`; the unique exact-symbol match `Larp7` is
used. The 98 eligible channels have an overlapping finite nonnegative locus in
all twelve files. Five channels are excluded from trans conditioning:
`HNRNPA1`, `HNRNPC`, `NCBP2`, and `ZC3H11A` have non-one-to-one MGI mappings;
`TROVE2` is missing from the frozen MGI report. Their RBPNet sequence outputs
remain eligible for M1, but no expression interaction is fabricated for M2/M3.

All 1,176 selected sample/RBP loci, their FPKM values, matching identifiers,
interval quality, and hashes are in
`results/finalshot/rbp_expression_proxy_samples.csv`.

## Frozen proxy

For RBP `r`, cell line `c`, compartment `q`, and replicate `k`, define:

`x[r,c,q,k] = log(1 + FPKM[r,c,q,k])`.

The compartment summary is the median over its three replicates. The final
context value is:

`E[r,c] = 0.5 * median_k x[r,c,soma,k] + 0.5 * median_k x[r,c,neurite,k]`.

Equal compartment weighting is intentional: the samples are separately
fractionated and do not provide a defensible mass-weighted whole-cell mixture.
Both compartment medians and the combined proxy are retained in
`results/finalshot/rbp_expression_proxy.csv`.

No outcome-driven normalization is used. Within an outer model fold, feature
standardization is fit on training rows only. CAD is assigned to certified CAD
rows from Mikl, TDP-43, and Moffatt; N2A is assigned only to certified Mikl N2A
rows. No vague substitute cell line and no Astrocyte state is used.

## Frozen interactions and ablations

M2/M3 may use only same-RBP elementwise interactions:

- `E[r,c] * delta_binding_summary[r]`;
- `E[r,c] * parent_binding_summary[r]`.

There are no cross-RBP polynomial terms. RBP groups are regularized together.
The trans block is retained only if the frozen cell-transfer ablation gate is
met. The mandatory context control swaps CAD and N2A vectors in compatible
Mikl rows while leaving sequence, geometry, and outcome assignment unchanged.

## Limitations

- RBP transcript abundance is not active protein abundance.
- RBPNet was trained on human HepG2 eCLIP, whereas these covariates and the
  localization assays are mouse neural cell lines.
- GSE67828 is a matching public cell-line study, not the same experimental
  batch or culture protocol as every development assay.
- FPKM and interval-based recovery add measurement and annotation uncertainty.
- Only two cell contexts are available, so this block tests a CAD/N2A contrast,
  not a universal cell-state embedding.

The context block must earn retention through crossed CAD/N2A transfer. A null
or harmful ablation result removes it; biological plausibility alone is not a
reason to keep it.

## Frozen Gate H result

The trans-interaction knockout removes every `E × binding` term, reducing M2
to the corresponding M1 feature space. M3 was independently retrained with its
frozen nested recipe search and measurement heads on that same knockout feature
space. All comparisons use the same four held-out task×direction evaluations
and never fit to target-cell outcomes.

| Full family | Knockout | Mean rank improvement | Mean regret improvement | Companion floor | Gate H pass |
|---|---|---:|---:|:---:|:---:|
| M2 | M1 feature space | +0.00357 | -0.00169 | Yes | No |
| M3 | M3 retrained on M1 feature space | +0.00389 | +0.00120 | Yes | No |

Neither family reaches the frozen +0.010 rank or +0.005 regret threshold. The
companion metrics remain above the -0.002 harm floor, but that alone cannot
pass the gate. **Gate H fails and trans-context interactions are dropped.**

The two M3 control archives contain 11,808 target rows each, have matching test
indices, and were selected only from source-cell inner folds. Their SHA-256
digests and selected recipes are recorded in
`results/finalshot/gate_h_summary.json`.

No N-zip outcome was accessed and no Astrocyte outcome or sequence data was
accessed. Frozen features, folds, model grids, seeds, selection rules, and gate
thresholds were not changed after results.
