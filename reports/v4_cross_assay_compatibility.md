# RNAddress v4 Phase A cross-assay compatibility audit

## Bottom line

The sources justify a **shared parent × intervention sequence representation with assay-specific heads**. They do not justify pooling all outcomes into one scalar target. The compatible unit is the sequence operation and its cost; the incompatible units are reporter scaffold, cell line, intervention-generation process, normalization, and uncertainty semantics.

## Certified development foundation

| Source | Certified interventions | Gene labels | Independent parent contexts | Outcomes | Uncertainty status |
| --- | ---: | ---: | ---: | --- | --- |
| Mikl/GSE173098 | 11,900 | 224 | 5,830 | CAD and Neuro-2a neurite/soma deltas | three paired raw-count delta replicates; finite SE for every pair |
| TDP-43/GSE288185 | 4,566 | 16 | 4,566 | CAD neurite/soma mutant-minus-WT | four biological replicates exist; pair-level processed uncertainty missing |
| Moffatt/GSE334718 | 46,292 | 10 | 10 labeled contexts / 8 exact sequences | five families × GFP/Firefly where finite | up to four raw paired ratios retained as diagnostics; not author-effect SE |
| Total | 62,758 | 248 case-folded labels | 10,406 | 93,397 long-form finite outcome rows | heterogeneous, explicit semantics |

The 248 value is a case-folded label union, not a claim that every label is an independent gene. Moffatt's `cdc42`/`cdc42bpg` and `trp53`/`trp53inp2` pairs share exact parent sequences and require sequence-equivalence sensitivity grouping.

## What can be shared

- Exact parent and mutant sequence encoding.
- Parent embedding, mutant embedding, signed/directional delta, absolute change, and parent × delta interaction.
- Continuous changed-base, changed-fraction, insertion/deletion/replacement, and operation-cost features.
- Operation-class and assay-context conditioning.
- Biological-parent grouping and leakage guards.
- Candidate-set decision objectives such as budgeted regret, top-k recovery, and probability of finding an acceptable intervention.

## What must remain assay-specific

- CAD versus Neuro-2a.
- GFP versus Firefly reporter scaffolds.
- Mikl author logFC deltas, TDP Figure 4E effects, and Moffatt WT-normalized effects.
- Each Moffatt assay family, especially sufficiency, whose recovered code documents omitted WT oligos and control-based normalization.
- Replicate uncertainty semantics and missingness.
- Direction prevalence and effect scale.

No z-score, rank transform, or sign flip is authorized in Phase A to make incompatible outcomes appear exchangeable.

## Direction asymmetry

Mikl is decrease-heavy in both cell lines, TDP is decrease-heavy, and Moffatt is increase-heavy among finite reporter outcomes. That can reflect true mechanism, candidate-generation bias, reporter context, or normalization; Phase A cannot identify one universal cause.

A future model should therefore use either:

1. a direction classifier plus direction-conditional magnitude heads; or
2. separate increase and decrease utilities within each assay head.

At minimum, evaluation must report increase and decrease separately. A symmetric absolute-effect loss alone would erase the intervention objective.

## Arora representation support

Arora/GSE183192 contributes 7,360 labeled 260-nt forward constructs, with 7,115 complete across GFP/CAD, Firefly/CAD, GFP/Neuro-2a, and Firefly/Neuro-2a. It spans 14 gene groups. It is an observational tiled library, not a deterministic parent-mutant landscape, and therefore adds **representation/forward-head support only**.

The four Arora assays have incomplete concordance (historical source audit pairwise Spearman 0.041–0.204). This supports assay-specific pretraining heads and rejects an unqualified four-assay average. Exact source hashes and mappings are incorporated into the v4 machine manifest via `data/frozen/v2_4_external_forward_audit.json`.

## Recommended Phase B architecture boundary

If Phase B is authorized, the defensible first architecture is:

- one leakage-audited sequence encoder for parent and intervention;
- explicit sequence-delta and operation-cost representation;
- assay-family, reporter, and cell-line context embeddings;
- separate output heads for Mikl CAD, Mikl Neuro-2a, TDP CAD, and Moffatt family × reporter outcomes;
- optional Arora forward-only auxiliary heads;
- sign/magnitude or direction-conditioned outputs;
- heteroscedastic or replicate-weighted loss only where uncertainty semantics are valid;
- grouped splits by biological parent, plus gene-held-out and exact-sequence-equivalence sensitivity analyses.

The encoder may be initialized from a frozen contextual model, but Phase A provides no evidence that a specific pretrained encoder is optimal. Architecture selection must occur entirely within grouped development data.

## Leakage hierarchy

The primary split key is biological parent context. The following are always co-grouped: all variants of one parent, all assay-family views of that parent, both reporters, every cell-line outcome, every barcode, and all replicates.

Sensitivity analyses must additionally hold out:

- exact parent-sequence equivalence across labels;
- full gene identity;
- intervention family;
- one source assay at a time, when assessing cross-assay transfer.

Variant-row random splits are forbidden because they would let nearly identical siblings and the same parent sequence enter training and testing.

## Compatibility verdict

- **Shared representation:** justified.
- **Single pooled localization target:** not justified.
- **Assay-specific heads:** required.
- **Direction-aware modeling:** required.
- **Minimum-budget conditioning:** justified from small through large edits.
- **Exact-SNV-only modeling:** not justified by development data alone.
