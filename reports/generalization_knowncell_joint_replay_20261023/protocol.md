# Deferred checkpoint arithmetic replay

This finite layer independently checks supplied checkpoint arithmetic without
reading project files, importing numerical packages or refitting models. A
future admitted controller must first verify exact committed prefit, pool,
birth/model/completion hashes, runtime and full checkpoint roster. This code
does not replace those provenance checks or authorize a project-data run.

For each supplied checkpoint it reconstructs valid preference weights from
source metadata/effects, pair differences and the scalar weighted RMS. Support
must agree exactly; numerical differences must be strictly below the existing
1e-9 bound. Saved birth-bound scales are then used for independent scalar
objectives and gradient norms. The independent arm is checked both globally
and as two conditional 2w heads with the original lambda. This compares the
saved diagnostics; it adds no gradient convergence gate or optimality claim.

A separate canonical scorer reconstructs full C-order float64/102-column
arithmetic without calling the production scorer. Both cell heads use the
complete validation shape. Saved canonical scores must match exactly. The
independent scalar coefficient sum must also agree within 1e-9; that tolerance
never replaces exact canonical ties or changes candidate choices.

The original three-GiB/one-GiB/one-thread contract is applied before work,
canonical scoring and completion. Future root-owned callbacks must use actual
fresh probes and separately admitted numerical objects. Tests here use only
invented arrays and optimizer spies, not numerical fitting. A whole 63-model /
84-unit replay, source-selection and decision/gate replay, bootstrap and actual
resource certification remain unfinished. No result or generalization claim is
made by this source preparation.
