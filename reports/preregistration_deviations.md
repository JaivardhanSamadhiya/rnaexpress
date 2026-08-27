# Preregistration deviations

## 2026-08-26 — inner tree-count surrogate

The first implementation run was stopped before any formal outer-parent prediction artifact or aggregate benchmark metric was written. Runtime showed that the complete nested ExtraTrees grid at 300 trees per inner fold would exceed the preregistered 1–6 CPU-hour budget on the available four-core machine.

Amendment: inner hyperparameter screening for `forward_extratrees`, `intervention_extratrees`, and `intervention_plus_mikl_prior` uses a low-tree surrogate. An initial 60-tree surrogate still projected to several hours before any formal outer fold completed, so the final inner screening count is 20 trees. After a leaf-size/feature-fraction configuration is selected, the outer-fold prediction and final locked-test fit use the preregistered 300 trees. All candidate configurations, features, outcomes, seeds, folds and selection metrics are unchanged. Completed outer folds are checkpointed and resumable.

This amendment was caused by observed runtime, not model performance. A one-parent implementation smoke test had printed method-level development scores before the amendment; no method, feature or hyperparameter option was added, removed or selected based on those scores.

## 2026-08-26 — Mikl joint-ablation compute cap

The restarted run was stopped before a complete formal outer fold after the fixed joint N-zip+Mikl forest alone took several minutes per fold. Because this is a domain-mismatch ablation rather than the primary strong model, it is capped at 100 trees, minimum leaf size 10 and feature fraction 0.25. The Mikl-only prior and primary N-zip forward/intervention models are unchanged. The full outcome-independent feature matrices and Mikl prior are cached after construction to avoid repeated preprocessing.

## 2026-08-26 — grouped inner folds for compute-heavy models

Even at 20 trees, one full forward-model inner LOPO grid took roughly five minutes; the projected complete run was incompatible with the stated compute/deadline constraints. Before any complete formal outer fold, inner selection for retrieval, the three tree families and pairwise ranking was changed to deterministic three-fold grouped validation over the available training parents. Outer evaluation remains leave-one-parent-out, and ridge/motif selection retains inner LOPO. The fixed diagnostic local histogram-gradient model was reduced from 250 to 100 boosting iterations. These changes were based on runtime only; grids, outer folds, metrics, features and 300-tree outer fits are unchanged.

## 2026-08-26 — fixed grid-center configurations

One outer fold completed under grouped inner tuning, but its timing still projected the 12-parent run near three hours. Before any aggregate metric was calculated or viewed, the checkpoint was discarded and all parents were regenerated with outcome-independent grid-center configurations: ridge radius 10/alpha 10; motif k=4/support 10; retrieval radius 10/15 neighbors; tree leaf 5/feature fraction 0.5; pairwise C=1. This removes hyperparameter optimization entirely while retaining strict outer leave-one-parent-out method comparison. The local histogram-gradient diagnostic is capped at 50 iterations, pairwise sampling at 300 pairs per training parent, and the exploratory joint Mikl forest at 50 trees. Primary tree-family outer fits remain 300 trees. This is more conservative than the preregistered nested selection and must be disclosed in interpretation.
