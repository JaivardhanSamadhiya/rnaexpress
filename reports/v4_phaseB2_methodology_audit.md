# RNAddress v4 Phase B2 methodology audit

Audit date: 2026-09-01. Search terms included residual RNA mutation effects, context-conditioned MPRA prediction, RNA intervention contrastive learning, multi-assay mutation residual models, perturbation-response decomposition, multi-study R-learners and cross-protein mutation transfer.

## Perturbation-response decomposition

Molina and Zhang's 2026 preprint separates global, perturbation-specific, context-specific and perturbation×context response components and shows why aggregate prediction can reward generic response templates. RNAddress borrows this diagnostic decomposition, mapping the components to generic edit geometry, parent state, source/assay nuisance and parent×edit interaction. The single-cell CRISPR setting and transcriptome-wide outcome differ from RNAddress, so this is methodological motivation, not evidence that RNA intervention interactions are predictable.

Source: https://doi.org/10.64898/2026.07.24.740459.

## Multi-study residualization

Shyr et al.'s multi-study R-learner estimates study-specific nuisance functions with cross-fitting before heterogeneous-response learning. It motivates strict out-of-fold nuisance predictions and explicit separation of shared and source-specific components.

RNAddress does **not** claim causal treatment-effect identification: its measured candidate libraries are not randomized treatment assignments with the overlap/ignorability structure required by R-learner theory. B2 borrows only the cross-fitting and nuisance-residualization principle.

Source: https://academic.oup.com/biostatistics/article/26/1/kxaf040/8383358.

## Context-matched mutation learning

Protein variant literature supplies adjacent precedents for context-dependent mutation effects, protein-level holdouts, delta representations and within-protein/within-assay ranking. EVmutation models epistatic sequence dependencies; deep generative mutation work uses leave-protein-out residual correction; ESMRank treats heterogeneous overlapping assays as within-protein ordinal evidence; and MutaPLM explicitly represents mutant-minus-WT embedding deltas.

These are protein precedents, not RNA-localization validation. They block broad novelty claims and support strict biological-unit partitioning.

Sources: https://www.nature.com/articles/nbt.3769, https://pmc.ncbi.nlm.nih.gov/articles/PMC6693876/, https://www.biorxiv.org/content/10.64898/2026.02.26.708185v1, and https://arxiv.org/abs/2410.22949.

## Contrastive perturbation learning

ContrastiveVI demonstrates supervised contrastive disentangling of cellular perturbation representations. B2's matched contrasts are much simpler: deterministic differences between outcome-compatible interventions matched on nuisance geometry. No representation-learning novelty is claimed.

Source: https://proceedings.mlr.press/v240/tu24a.html.

## Collision conclusion

No located work exactly tests incremental parent-specific RNA-localization intervention value over a cross-fitted geometry nuisance baseline across Mikl, TDP and Moffatt. The defensible contribution is the decomposition and falsification test, not a claim to have invented residualization, bilinear interactions, contrastive learning or mutation-effect modeling.
