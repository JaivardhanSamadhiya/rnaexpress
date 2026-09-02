# FinalShot stability-prior decision

Freeze date: 2026-09-02

Resource-audit base commit: `f2b2c01`

## Decision: no stability feature in the primary FinalShot family

The resource audit did not identify a reproducible, pretrained model that can
accept each 150- or 260-nt parent/mutant sequence and return a validated mouse
neural `stability(parent)`, `stability(mutant)`, and `delta stability` without
using target intervention measurements. FinalShot therefore freezes **no
stability input** for M0-M3.

This is an exclusion, not a zero-valued imputation. Gate I and the stability
permutation/ablation are recorded as not applicable. No AU-rich, m6A, codon,
ViennaRNA, or ad hoc motif score will be added after localization results are
seen.

## GSE249405 / Spatial NT-seq

[GSE249405](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE249405) and
Spatial NT-seq (DOI `10.1038/s41593-026-02420-y`) were audited as a valuable
mouse-brain turnover atlas. The public resource supplies measured spatial and
cell-type-resolved turnover observations and analysis code. It does not supply
a frozen, validated sequence-to-mutant-effect checkpoint compatible with the
RNAddress reporter inserts. Training a new sequence model would require new
target construction, transcript mapping, architecture selection, and leakage
controls beyond this final-shot protocol.

The astrocyte-specific component is also prohibited from being used to tailor
development toward the sealed Astrocyte MPRA. Accordingly, GSE249405
contributes literature context only: no sample, label, coefficient, embedding,
or derived feature enters FinalShot.

## TDP stability values

The historical TDP EV5 stability values remain quarantined and are not used.
They are neither training targets nor validation labels. Their absence cannot
be patched with localization outcomes.

## Consequence

M3 means M2 plus a shared latent biological score and low-capacity monotone
assay measurement heads. It does **not** include a stability block. Any final
claim must say that the RBP-binding hypothesis was tested without a validated
independent stability predictor and must not imply stability was modeled.

