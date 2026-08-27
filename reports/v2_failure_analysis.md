# RNAddress v2 failure analysis

Frozen historical result: the original preregistered internal gate **failed**. Nothing in v2 changes that result or converts the spent three-parent lock into a fresh confirmatory test.

## What failed

The selected `pairwise_rank` model reached rank percentile 0.566 on the three locked parents, below `forward_extratrees` at 0.624. Its recommendations also repeated edge-proximal choices (`C1T` for two increase tasks). In the post-lock 15-parent audit, pairwise rank percentile was 0.622, but metadata-only was already 0.612 and GC-only 0.594. The custom method therefore did not establish an intervention-specific advantage.

## Root implementation defect in the modeling idea

The pairwise learner is linear and is trained on

`intervention_features(parent, edit_i) - intervention_features(parent, edit_j)`.

All unchanged parent-sequence features are identical within a parent and cancel exactly. The fitted model can learn substitution, local-context, k-mer-delta and position rules, but it cannot learn that the *same edit feature should have a different effect in a different parent context*. This contradicts the intended formulation `g(parent, edit) -> delta` and explains why positional/source shortcuts can compete with the full model.

This is a structural problem, not a hyperparameter problem. Increasing tree count, changing regularization, or reusing the revealed lock would not repair it.

## v2 corrective hypothesis

RNAddress v2 will retain parent information inside pairwise comparisons through explicit parent-by-edit interactions. Its core score is factorized as

`score(parent, edit) = additive(edit) + parent_embedding' * W * edit_embedding + residual(parent, edit)`.

When two edits from the same parent are compared, the interaction term becomes

`parent_embedding' * W * (edit_i - edit_j)`

and therefore does not cancel. Structure/accessibility deltas and motif-context features are included because RNA binding and localization motifs are demonstrably context dependent, not because they were selected from Astrocyte outcomes.

## Non-negotiable interpretation

- Original lock: permanent FAIL.
- All 15 N-zip parents: v2 development evidence only.
- New TDP-43 gene lock: independent auxiliary intervention evidence, but multi-base and not a substitute for SNV validation.
- Astrocyte SN-MPRA: still the only untouched external SNV transfer benchmark.
