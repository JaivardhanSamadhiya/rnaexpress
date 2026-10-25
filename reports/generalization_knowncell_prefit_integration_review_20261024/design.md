# Fixed known-cell prefit, FIT and replay integration review

Source-only review, 24 October 2026. This is an implementation design, not a
source freeze or execution admission. No biological payload, CORE, feature
array, label certificate values, existing checkpoint, native scientific
library, resource probe, test or model was read/executed for this review. Only
source and existing source-design reports were inspected. No frozen file was
edited. Root reports that corrected metadata acquisition and its independent
reconstruction have passed and been committed; their actual payloads were not
independently inspected here. Array execution and labels preparation are owned
by other agents/root.

The approved policy and original authorization remain separate from any new
integration generation: policy `a49b82f965dd6e389f908764d2bf1c331eb3441fe8a0d683b0fca2466c847ba9`,
AUTH `b67d5d45abdd6812997d3b84f6cbd5ff2abaf68cd8786638f5312d2744ab24e3`,
scope `c40b929187a35199e88523ab5c6b351789c45fddb3aebe6dcf68172684ce6495`.
The remaining four owned invocations are prefit, the fixed FIT campaign,
independent complete replay, and complete evaluation. The scope requires a
reviewed additive controller/admission and distinct immutable birth for each;
it does not itself supply those sources or scientific input admissions. See
[the unchanged approval scope](D:/rnaexpress/reports/generalization_knowncell_bounded_execution_20261023/approval_scope.md:13).

## Confirmed policy-schema conflict

The original [prepare_pools](D:/rnaexpress/src/generalization_knowncell_joint_engine_20261023/adapter.py:114)
constructs exactly nine pools and emits the generic top-level
`resource_exception_applies=False` at line 143. The original
[validate_prefit](D:/rnaexpress/src/generalization_knowncell_joint_campaign_20261023/contracts.py:64)
requires that flag to be exactly false at line 68. The
[Campaign constructor](D:/rnaexpress/src/generalization_knowncell_joint_campaign_20261023/writer.py:99)
checks raw SHA at line 101 and revalidates `plan.document()` at line 102.
Therefore merely changing the flag to true breaks the existing lifecycle;
leaving it false in an actual calibrated receipt is an inaccurate generic
resource claim. A PUM/PRELib-specific false exception flag remains correctly
false and must not be confused with this generic flag.

The five approved aliases are exactly those listed in
[calibration.TARGETS](D:/rnaexpress/src/generalization_knowncell_bounded_execution_20261023/calibration.py:24).
They are resource aliases in loader guard, array validator, engine adapter,
checkpoint arithmetic replay and outer evaluation. No validator, BoundPlan,
writer, selector, sampler, numerical callback or runtime provider is an
additional approved monkeypatch target. The original pure
`admission.require_resources` remains unchanged. Keep the exact reviewed
resource transaction/restore bodies and real owner/probe admission; do not use
the old private invented-test dependency-injection helpers in production.

## Smaller compatibility projection is feasible, with explicit limits

The source supports a narrow additive BoundPlan subclass without copying the
writer, selector or finite runner. The original
[BoundPlan.document](D:/rnaexpress/src/generalization_knowncell_joint_campaign_20261023/contracts.py:107)
normally parses raw prefit bytes, but its callers do not separately assert
`strict_json(plan.prefit_raw)==plan.document()`. The writer checks the raw SHA
and then separately validates the returned view. The
[runner](D:/rnaexpress/src/generalization_knowncell_joint_runner_20261023/runner.py:37)
and writer use `isinstance(plan, BoundPlan)`, which accepts a derived plan.
Engine equality checks compare supplied pools to `plan.document()`; they do
not decode `prefit_raw` again. The unchanged numerical callbacks, V2 immutable
selector and writer can therefore consume a narrowly defined legacy view.
This is a reviewed semantic adaptation of the plan interface, not proof that
the original BoundPlan API already certified calibrated execution.

Recommended finite design:

1. Run the unchanged original `prepare_pools` only inside the genuinely owned
   approved prefit context, after actual input/runtime admission. Keep its
   numerical pools and all scientific binding values unchanged. Its returned
   false-policy document is a transient legacy declaration, never the actual
   persisted prefit.
2. Build an actual prefit with `resource_exception_applies=True` and explicit
   actual policy/AUTH/scope, generation, owner/birth and prefit completion
   provenance. Save and commit its exact raw bytes. Preserve the same status,
   scientific metadata, IDs, folds, pools, original pair rosters, source-only
   weights/scaling, configurations, feature/effect hashes and stable runtime
   binding. The actual prefit's whole-document SHA necessarily changes with
   truthful provenance; scientific-subtree hashes must not change.
3. A new binder verifies the actual raw bytes against the exact commit and
   initial raw SHA, validates calibrated-policy/owner/completion evidence,
   and checks every scientific invariant. It must not call the old
   `bind_plan` on the actual true-policy raw bytes: that factory rejects them.
4. Define `actual_document()` as the exact decoded actual raw bytes. Define
   the compatibility `document()` as a fresh strict-JSON copy whose **only**
   difference from `actual_document()` is the generic field set from true to
   false. Assert this exact one-field difference, both whole-document hashes,
   and scientific-subtree equality. Reject missing fields, an already-false
   actual policy, extra projection rules, changed hashes, mutated raw bytes,
   mismatched runtime or uncommitted input. Do not suppress unknown provenance
   or resource keys.
5. If actual provenance adds fields absent from the original returned
   document, retain them in both actual and compatibility documents. Create a
   new original `PreparedPools(metadata, pools, compatibility_view)` after
   asserting equality of every original field except the generic policy
   declaration. Otherwise its exact prefit-document equality checks fail.
   Do not remove arbitrary provenance to make old equality pass. Do not alter
   the pool arrays, bindings or source/target masks.
6. Preserve `prefit_raw`, `prefit_sha256`, path and commit as the **actual**
   truthfully calibrated bytes. The subclass's `identity()` should call the
   original identity logic and add an explicit compatibility descriptor:
   actual raw SHA, compatibility-view SHA, exactly one policy-field
   projection, scientific binding hash/equality, policy/AUTH/scope and source
   generation. The descriptor must say the view is not actual resource
   provenance. The original writer includes this identity in campaign birth
   and completion; each checkpoint binds their birth and actual prefit SHA.
7. Integrity/readers/reporters use actual raw/`actual_document()` for resource
   provenance and must never persist `document()` as the actual prefit. The
   mandatory pre-checkpoint hook should verify both representations and the
   actual policy. Revalidate the projection during independent replay. No
   original validator or global function is rebound.

This preserves the exact original objects for `make_fit_callback`, numerical
fit/scorer, `adapter_v2.select_outer`, `writer_v2.Campaign` and `run_campaign`.
The subclass and binder must be frozen/tested/reviewed before use. If a future
consumer begins to require raw/document identity, it must fail rather than
expand the projection. A derived Campaign constructor plus copied runner is
the more explicit alternative, but changes more lifecycle source and repeats
critical failure handling. No currently reviewed raw/document check forces
that larger approach.

## Input and runtime prerequisites

| Needed object | Existing source contract and remaining owned-stage obligation |
|---|---|
| Metadata | Preserve the committed exact acquisition bundle and separate independently reconstructed metadata report/supervisor. Rebuild full both-cell masks and retain all 13,781 rows, 187 components, 2,408 paired menus and nine unmatched contexts. No source/gene/allele contradiction repair. |
| Simple102 | [Array admission](D:/rnaexpress/src/generalization_knowncell_array_admission_20261023/admit.py:187) certifies the frozen NPZ, original row/creation receipts, exact `astype(float)` bits and same-allele parity. The actual [array worker](D:/rnaexpress/src/generalization_knowncell_array_execution_20261024/worker.py:60) discards its matrix after saving the certificate. Later stages may narrowly guarded-reload the same NPZ, validate shape/order/finite values and exact admitted bits against the committed certificate; this is not another array-admission opportunity or a new feature source. |
| Original effects | [parsers.pandas_effects](D:/rnaexpress/src/generalization_knowncell_joint_loader_20261022/parsers.py:89) fixes original pandas `read_csv(usecols=..., low_memory=False, skiprows=original mask)` and `to_numpy(float)`, exact ID/order and `<d` float64 hash. Root's current producer plan persists `measured_delta.tolist()` plus that hash in the label certificate. Later stages guarded-load that committed exact certificate, check all IDs/length/finite values, repack each value as `<d` and require the original hash. No CORE reread, Python replacement CSV parser or numerical access to other assays is needed. This persistence plan is reported by root, not certified by reading actual labels here. |
| FIT admission | The original loader's label admission explicitly does **not** authorize fitting ([loader.py:126](D:/rnaexpress/src/generalization_knowncell_joint_loader_20261022/loader.py:126)). New committed per-stage admissions must bind successful array/label/metadata proof hashes, source closures, correct original orientation and the exact nine-pool prefit. Readiness alone is insufficient. |
| Sampler | Use the actual original [pair_indices](D:/rnaexpress/src/cross_assay_20260927/models.py:13): fixed `SEED=20260927`, context-hashed RNG, cap256 and exact truth-tie exclusion. Engine checks function name/module and source SHA but delegates full callable/native provenance to the controller. Bind its imported code/dependency chain and assert the callable is the actual module function, exact code path and source SHA, with admitted NumPy/pandas/SciPy objects. Do not substitute a source-extracted function or another sampler. |
| Native/runtime | Admit current CPython payload and exact NumPy1.26.4, pandas2.2.3, SciPy1.14.1, actual minimize/expit and one-thread loaded native origins. Fresh runtime proofs are required for each owned process and before each fit checkpoint through the existing mandatory integrity hook. The invented software profile is necessary evidence, not full-size FIT admission. Historical interpreter bitwise parity remains false. |

The original array provider is deliberately request/phase-limited:
[provide](D:/rnaexpress/src/generalization_knowncell_runtime_provider_20261023/provider.py:103)
accepts `before_array`, then `after_array` exactly once for one committed array
request. The new labels provider likewise accepts only
[`before_labels`/`after_labels`](D:/rnaexpress/src/generalization_knowncell_labels_runtime_20261024/provider.py:54).
Neither should be relabeled or called with invented phases as a general FIT
provider. An additive fixed-stage provider can reuse unchanged reviewed
bootstrap/software-object/actual-origin helpers, while its new public request
contract fixes its own prefit/FIT/replay/evaluation input admission and phases.

Minimum truthful provider behavior: fresh process `-S -B`, the same absent
cache prefix and four thread variables1; actual real resource/owner checks
before imports; exact current Python/native/package/possible-cache and loaded
DLL evidence; initial and terminal actual-origin checks; actual `np`, `pd`,
`minimize`, `expit` identity checks after the sampler import. Preserve one
owned software object set per stage. FIT requires a fresh actual-origin proof
in the pre-checkpoint integrity hook and fresh resources before each actual
minimize, as the original callback already enforces. Replay needs fresh proof
before its checkpoint traversal; evaluation before/after its native bootstrap.
No provider gains a general project reader or new label permission.

Keep a **stable admitted runtime binding** in the scientific prefit and all
checkpoint identities, e.g. the source admission's accepted array-after proof
SHA plus pinned static software identity. Separately record each current
stage's fresh proof SHA, UTC and PID. Compare current Python/modules/native
hashes and source policy to the stable admitted identity. Do not require
different dynamic proofs to have identical UTC/full JSON hashes, and do not
substitute a new dynamic SHA into an already committed plan runtime binding.
The identity should explicitly distinguish admitted anchor evidence from
fresh current-process verification.

## Fixed campaign, complete replay and evaluation

The [finite runner](D:/rnaexpress/src/generalization_knowncell_joint_runner_20261023/runner.py:19)
already fixes 54 inner plus nine selected outer checkpoints and 84 actual
optimizer units, all six inner checkpoints before each arm/outer selection,
mandatory integrity hook, exclusive new directory and failure poisoning. Its
callbacks retain the original L-BFGS-B options, common pair-RMS/full102 support,
independent conditional2w heads, joint shrink10 and full-shape canonical scorer.
No gate/roster/configuration/seed/precision change is proposed.
Keep operational logs, stage births/origin proofs and controller receipts
outside the runner's `checkpoints` child: the original writer's final exact
filename roster admits only campaign birth plus63 birth/model/completion
triples before its own completion file. Additional operational evidence belongs
in the enclosing owned-stage directory, not inside that closed roster.

`Campaign.finish()` deliberately certifies only lifecycle. The independent
owned replay must first verify the exact complete directory roster, all63
birth/model/completion raw hashes, campaign birth and committed actual prefit,
each task/configuration/unit roster, source/target IDs and every pool binding.
The controller must implement this finite traversal; the existing
[replay_checkpoint](D:/rnaexpress/src/generalization_knowncell_joint_replay_20261023/arithmetic.py:76)
is a supplied-checkpoint arithmetic helper, not a complete campaign reader.
It checks separate scalar scaling/objective/recorded gradient norm under the
unchanged strict `<1e-9` bound and exact canonical full-shape scores. It does
not establish global optimizer optimality or input provenance by itself.

Replay all54 inner and nine outer fits. Independently reconstruct the exact
two-inner-fold concatenated source-only OOF decisions for all three lambdas
and each arm/outer fold; preserve the original paired-only equal-cell,
component, context and direction weighting. Verify each selected lambda,
configuration metrics hash, six source checkpoint hashes and source-only
selection receipt. Preserve exact score then original intervention-ID ties
and the fixed configuration ordering/`1e-12` selection tolerance
([selection.py:68](D:/rnaexpress/src/generalization_knowncell_joint_implementation_20261022/selection.py:68)).
Do not call production selection and describe that alone as independent
reselection. No refit, partial selection, threshold search or favorable
checkpoint omission is permitted.

Only after that committed accepted replay, the separately owned
[evaluate](D:/rnaexpress/src/generalization_knowncell_joint_evaluation_20261023/evaluation.py:94)
can consume all nine exact outer records and all original effects. It retains
every row once per arm, 9,650 full directional decisions per arm, 9,632 paired
primary decisions and unmatched secondary summaries. Keep the same joint-only
eligibility, both pooled/independent controls, shared seed20261007 5,000-draw
exponential bootstrap and all unchanged gates. The evaluation function
explicitly does not certify input provenance or whole-campaign replay itself.
Its result remains represented-cell/unseen-gene exposed development, not
unknown-cell generalization, independent confirmation or proven novelty.

## Conservative memory and timing limits

No actual full-size memory, pair count, process peak or duration was measured.
The supplied-array invented profile is not a proof that this campaign or its
scalar replay fits the approved 768MiB process / 896MiB Job caps or 1,800s
deadline. Preserve all caps/reserves and no-retry behavior.

Let N=13,781, C=4,825 contexts (4,816 paired plus nine unmatched) and P be the
whole-cohort original valid sampled-pair count. Every context has at least two
candidates ([contracts.py:32](D:/rnaexpress/src/generalization_knowncell_joint_implementation_20261022/contracts.py:32)).
For n>=2,
`min(n(n-1)/2,256) <= 12(n-2)+1`; hence P<=12N-23C=54,397, independent of
effects. Truth ties can only reduce this bound. Since each inherited fold
appears in two inner-training pools and two final-training pools, the exact
nine-pool schedule retains 4P pair rows. No actual menu-size distribution or
tie outcome was inspected to refine this conservative bound.

| Retained numerical payload | Source-defined aggregate bound |
|---|---:|
| Nine source feature matrices (4N rows) plus validation matrices (3N rows), width102 float64 |78,717,072B, about75.07MiB|
| Nine prepared z matrices, 4P rows, width102 float64 |at most177,551,808B, about169.33MiB|
| These two payload classes together |at most256,268,880B, about244.39MiB|

These are not process-memory bounds. Add original input matrices, preparation
advanced-index copies, the `differences`, squared/weighted and standardized
arrays in [prepare_training](D:/rnaexpress/src/generalization_knowncell_joint_numeric_20261022/numeric.py:36),
label/weight/sign arrays, Python metadata and IDs, pair index lists and the
original sampler's nine-entry `PAIR_CACHE`. Imports, BLAS/SciPy workspaces,
native threads/stacks and JSON serialization also count. Independent fitting
allocates its selected cell matrix. Original callback integrity hashing makes
additional C-order arrays and byte strings, including z, before every actual
minimize. Model count63 is not a63-times dense matrix multiplier: the same nine
pools are shared and one actual optimizer runs at a time.

Replay is the larger concern. Its
[training.tolist/differences](D:/rnaexpress/src/generalization_knowncell_joint_replay_20261023/arithmetic.py:95)
and [z list](D:/rnaexpress/src/generalization_knowncell_joint_replay_20261023/arithmetic.py:106)
materialize Python floats and lists in addition to retained native pools.
At nominal CPython64-bit 24B float +8B list reference, differences and z alone
can add approximately `2*P_pool*102*32` bytes: up to355,103,616B (338.65MiB)
at the loose P_pool<=P bound, plus row-list headers, training scalar lists,
reference calculations and native score copies. Thus a fit that fits the cap
does not establish replay viability; a conservative upper case can exceed
768MiB after unmeasured native/object overhead. This is a risk bound, not an
observed failure or precise peak prediction.

Preserve scalar summation order, `math.fsum`, all102 coordinates and exact
full-validation canonical shape. Do not silently chunk vector products,
compress active coordinates, replace scalar replay with NumPy, raise the cap
or widen tolerances to make it pass. A separately reviewed operational replay
controller can load/reconstruct and verify one immutable pool at a time,
release it between pools, and replay its bound checkpoints without refitting;
that does not require changing the nine-pool science. It still needs a proven
pool reconstruction/read contract and may remain near the scalar-object cap.
Any streaming arithmetic rewrite is a further source-proof task, not part of
this report. Full matrix hashing, scalar Python loops, current-origin refresh
and63 artifacts also make the30-minute duration unproven. Use actual owned
caps/deadlines; preserve a technical failure and do not automatically retry.

## Finite next integration order

1. Finish and commit the exact array and original-pandas label certificates;
   label certificate must carry the exact selected values and `<d` hash as
   root specified. Freeze additive per-stage runtime/input providers and the
   explicit one-field compatibility plan/binder with invented corruption
   rejection tests. No production run is granted by this report.
2. Implement reviewed prefit ownership/source/input admission, persist the
   truthfully calibrated actual prefit and commit it. Implement the FIT
   controller around the unchanged finite runner, with fresh runtime/source
   proof in the mandatory hook, exact initial manifest identity and terminal
   checks after provenance work. It retains one exclusive nonresumable run.
3. Complete the independent63 traversal/reselection controller and separate
   evaluation controller before claiming an executable end-to-end study.
   Apply the same policy and distinct owned births; use no new scientific
   settings or favorable partial results. A lifecycle PASS, resource PASS or
   smaller invented-profile PASS cannot substitute for complete replay/gates.

Conclusion: the original components are sufficient foundations, but the
calibrated prefit interface, stage-bound providers/readers, actual FIT
ownership/admission and complete replay traversal are real integration work.
The one-field compatibility projection is the smallest coherent option found
in this source review, provided its actual-versus-view semantics are explicit
and frozen. No biological or operational success is established here.
