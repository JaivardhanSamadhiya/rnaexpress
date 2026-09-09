# FinalShot integrity review — 9 September 2026

Status: **not an unqualified Gate L pass**. Existing predictions, folds, models,
and gate thresholds remain unchanged. This review discloses discrepancies; it
does not repair them by retrospective protocol revision.

## Matched Mikl analysis: missing cap and contradictory requirements

Section 12 specifies at most two candidates per gene in a matching stratum,
chosen by candidate hash, while requiring at least four candidates in each
within-gene decision subset. Applied to the same stratum, these conditions are
incompatible. `mikl_matched` in `analyze_finalshot_grouped_gates.py` filters strata
and within-set sizes but does not implement the two-per-gene hash cap. Its
recorded Gate C pass therefore describes the implemented uncapped analysis,
not literal compliance with the written protocol.

The archived +0.015818 rank and +0.017845 regret estimates remain available and
must not be silently overwritten. They cannot support an unqualified claim of
prospectively compliant matched-mechanism success. No new interpretation of the
cap is chosen after seeing results. Existing tests checked other invariants and
did not detect this discrepancy; their success is not proof of full protocol
fidelity.

## Selection tie order

Section 11 first mentions regret, rank, and GoodSelection@3, then says ties
within 0.002 regret choose the simpler family. The implementation forms the
0.002 regret window and prioritizes rank and GoodSelection@3 before simplicity.
M3 recipe selection similarly puts secondary metrics ahead of the stated
affine/regularization tie order. This is a material ambiguity between prose and
code, not evidence of target-outcome tuning. Tests explicitly document the code
behavior. The archived primary selected families are M1, M2, M3, M1, M1 for
outer folds 0–4; they are not M3 in every fold.

Do not retrospectively reselect families or change the tolerance to obtain a
different verdict. State both the implemented order and the prose ambiguity.

## Delta-block control semantics

The delta control reassigns intact blocks to donors in another biological unit
within the specified strata. For unequal unit sizes it cycles donor rows.
Consequently this is not a bijective row permutation: some donors can be reused
and others omitted. It breaks intervention alignment without using donor
outcomes, but does not preserve the exact empirical delta multiset. The donor
map is constructed over eligible rows and may cross biological folds at the
covariate level. That is not outcome leakage; nevertheless, this transductive
control construction must be distinguished from a fold-local permutation.

The independent RBP-identity control also fails necessity, so the delta-control
limitation cannot be used to claim that RBP necessity has been established.

## Measurement-head randomization aggregation

The original protocol requires calibration MSE/Spearman degradation without
specifying pooled versus equal-head aggregation. The September 6 implementation
requires both summaries to degrade; this conjunction was not in the September 2
freeze. Pooled MSE and Spearman degrade, equal-head MSE degrades, but equal-head
Spearman improves. Report this mixed result rather than treating an added
aggregation rule as a prospectively frozen gate. Gate J independently fails
its original transfer-harm condition in two source-direction tasks.

## Repeated-fit checks and numerical sensitivity

Two complete outer-fold-0 refits of M0, M1, and M2 produce identical predictions
within a fixed runtime configuration. Native-runtime results are in
`deterministic_reproducibility_threads_default.json`. M0 agrees with the archive
to approximately 1e-16; M1 and M2 differ by maxima 2.32e-6 and 5.74e-5 despite
identical repeated results. Their iterations match 202 and 253 in this check.
Thus the literal repeated-smoke condition passes, but cross-run archive
reproduction at 1e-8 has not been established for the sparse models.

An earlier one-thread diagnostic is preserved in
`deterministic_reproducibility.json`; it also repeats exactly but differs more
from archived predictions. That initial M0 diagnostic used the direct-model
float32 rank-target helper instead of the representation benchmark's float64
helper. The corrected diagnostic imports the exact M0 helper. Neither run
overwrites primary predictions or changes solver tolerances. Thread-dependent
floating-point behavior is a plausible contributor to sparse-model differences,
not a fully isolated diagnosis. No claim of bitwise cross-platform reproduction
is warranted.

## Boundaries and release consequence

Only the certified Mikl, TDP, and Moffatt development outcomes are in scope.
No N-zip outcome or Astrocyte data is admitted. Reading/hash-checking the
protected loader's source code in an integrity test is not loading its data.
The 32 existing FinalShot tests passed on September 9, but scientific protocol
compliance is a separate review from software tests.

These limitations cannot be concealed by a favorable overall metric. FULL GO
already fails other frozen gates. Any final report must distinguish implemented
results from unresolved or contradicted protocol requirements; prospective
Phase C and a claim of a validated universal compiler are not justified.
