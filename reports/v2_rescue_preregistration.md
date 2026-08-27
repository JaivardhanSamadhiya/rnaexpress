# RNAddress v2 rescue preregistration

Frozen on 2026-08-26 after the original internal failure, after outcome-blind reconstruction/splitting of the new TDP-43 dataset, and before fitting any v2 model. Astrocyte outcomes remain sealed.

## Status and hypotheses

The original three-parent internal gate remains a FAIL. V2 is a new, explicitly labeled development cycle; it cannot rescue or reinterpret that lock.

Primary v2 hypothesis: a parent-context-by-edit interaction model will rank directional N-zip SNV effects on held-out parents better than strong forward prediction plus exhaustive search and better than shortcut controls.

Auxiliary locked hypothesis: context interaction will improve prediction/ranking of motif-complement intervention effects on four held-out TDP-43 genes. This is multi-base gene-level transfer, not SNV validation.

## Data boundaries

- N-zip: all 15 clean parents and 4,395 SNVs are now development data. Evaluation is nested leave-one-parent-out and is not called a new lock.
- Mikl: 11,926 truth-safe multi-base motif replacements across 6,104 parents; development-only auxiliary pretraining/regularization.
- TDP-43 development: 3,560 multi-base motif interventions from 12 genes.
- TDP-43 lock: 1,006 interventions from Fam160b2, Lars2, Diras1 and Synj2bp. Only outcome-free features may be accessed before the v2 freeze.
- Astrocyte SN-MPRA: 4,553 SNVs across eight in-vivo parents; all outcome fields remain sealed.

No dataset is treated as homogeneous with another. Dataset, assay and intervention type are explicit. Gene identity may define groups but may not be a predictive feature.

## Candidate task and inference units

For N-zip, enumerate all assayed SNVs for each held-out parent and rank separately for requested increase and decrease. Primary inference unit is the parent-direction pair, aggregated first within parent and then across 15 parents.

For TDP-43, rank the assayed motif-complement interventions within each held-out gene for increase and decrease. The unit is gene-direction. This tests contextual intervention discrimination but is not described as same-parent exhaustive editing.

## Fixed feature families

All sequence features are outcome independent:

- normalized 1–4-mer parent and mutant frequencies and their deltas;
- edit count, edited span, relative position summaries and reference/alternate composition;
- parent/mutant edit-centered sequence windows at radii 5, 10 and 25;
- fixed literature motifs: AU repeats, let-7 seed-related sites, A/G-rich windows, G-quadruplex-like patterns, canonical TDP-43 motifs and QRE-like motifs;
- ViennaRNA 2.7.2 parent/mutant minimum free energy, ensemble diversity, mean edit-site pairing probability/accessibility and their deltas;
- optional frozen RNA-FM embeddings only if acquired without using any locked outcome and computed identically for every dataset.

Measured parent localization, gene identity, source row/order, barcode, batch and any Astrocyte outcome are prohibited features.

## Models

Baselines retained: exact random; substitution mean; motif delta; retrieval; local ridge; direct ExtraTrees; old linear pairwise rank; metadata/position-only; GC-only; and strong forward model plus exhaustive search.

Strong forward family:

- forward ExtraTrees from v1;
- forward LightGBM on absolute sequence/structure features;
- a compact shared 1D CNN with parent-grouped early stopping. Candidate effect is `f(mutant)-f(parent)`.

V2 custom family:

1. `context_lambdamart`: LambdaMART grouped by training parent/gene on concatenated parent, edit, structure and explicit cross features.
2. `factorized_context_ranker`: additive edit score plus a low-rank bilinear parent-by-edit term. Pairwise logistic loss uses only pairs from the same parent/gene, so the parent interaction remains present after differencing.
3. `factorized_context_ranker_structure`: the same model with prespecified ViennaRNA features.
4. Development-only auxiliary variants initialized or regularized by Mikl and/or the 12 TDP-43 development genes, with dataset-specific output heads and equal aggregate dataset weight.

Fixed search ranges:

- bilinear rank 4, 8 or 16; hidden width 32 or 64; L2 `1e-4`, `1e-3` or `1e-2`; learning rate `1e-3` or `3e-4`;
- LambdaMART leaves 7, 15 or 31; minimum child samples 10 or 30; learning rate 0.03; 300 trees with grouped early stopping capped at 500;
- CNN channels 32 or 64; kernel widths 5 and 9; dropout 0.2 or 0.4; learning rate `1e-3` or `3e-4`.

Seed is `20260826`. Hyperparameters are selected inside grouped inner folds only. If runtime forces a smaller prespecified grid, the change must be logged before aggregate outer predictions are examined.

## Development selection

N-zip uses nested leave-one-parent-out. For each outer parent, all tuning and early stopping use only the other 14 parents. TDP-43 development uses leave-one-gene-out. A model family is selected primarily by N-zip parent-macro directional selected rank percentile; ties within 0.005 use normalized regret, Spearman, then simplicity. TDP-43 development may break a remaining tie but cannot override a materially worse N-zip result.

Mikl/TDP auxiliary learning is retained only when its parent-level N-zip outer-fold gain is positive after removing the two most favorable parents. RNA-FM and structure features are retained only by the same rule. No best-of-many result is selected from the locked TDP-43 genes or Astrocyte outcomes.

## Metrics

Primary N-zip metric is selected experimental rank percentile, averaged over increase/decrease within parent and then over parents. Secondary metrics: normalized regret, experimental regret, Spearman, Success@1/3/5 and Precision@1/3/5 under the original fixed threshold.

TDP-43 uses the same continuous directional rank percentile and normalized regret within gene, plus within-gene Spearman. Binary thresholds are not introduced for TDP-43.

All intervals and paired differences resample parent/gene units, never individual variants as independent units.

## V2 development gate before opening the new TDP-43 lock

The selected custom method must satisfy all of:

1. N-zip nested-LOPO macro rank percentile at least 0.630.
2. Gain over the strongest forward-search baseline at least 0.030.
3. Gain over metadata/position-only at least 0.020.
4. Custom-minus-forward improvement in at least 9 of 15 parents after averaging directions.
5. Positive custom-minus-forward gain after removing the two most favorable parents.
6. Shuffled edit identity no higher than 0.540 and shuffled labels no higher than 0.530.

If this gate fails, the TDP-43 locked outcomes and Astrocyte outcomes remain sealed.

## New TDP-43 locked gate

After the development gate passes, freeze model checkpoints, code, all 1,006 lock predictions and their hashes before opening TDP-43 locked outcomes. The auxiliary gate requires:

1. macro directional rank percentile above 0.550;
2. positive gain over both the strongest forward model and a motif/accessibility heuristic;
3. positive within-gene Spearman for at least three of four genes;
4. no single locked gene accounting for the entire aggregate advantage.

Failure is reported and Astrocyte reveal is not authorized. Passing supports context-conditioned intervention transfer, but does not establish SNV transfer.

## External authorization and freeze

Only after both v2 gates pass may the final method be refit on permissible development data and used to generate outcome-blind rankings for all 4,553 Astrocyte SNVs. Before reveal, commit model/checkpoint hashes, environment, code hash, features, baselines, random seed and complete prediction artifact. No model, calibration, threshold or feature may change after reveal.

The final project reaches the requested scientific level only if the frozen Astrocyte ranking beats random, shortcut controls and strongest forward exhaustive search across multiple parents with parent-level uncertainty. UI or presentation work cannot substitute for these results.
