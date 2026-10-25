# Calibrated prefit compatibility on supplied immutable bytes

This is a small uninvoked compatibility library, not a data reader, prefit builder, resource adapter, trainer or execution controller. It changes no old source and introduces no sixth resource alias or monkeypatch. No actual prefit, root admission, current-runtime proof or owner record is created during preparation.

The existing engine emits a generic `resource_exception_applies=false` declaration. Its unchanged lifecycle validator requires that flag. A truthful actual prefit prepared under the approved known-cell resource policy must instead persist `true`, and can add actual resource/owner provenance. The numerical and split fields do not need to change.

## Two documents with explicitly different roles

The additive `CalibratedBoundPlan` subclasses the original immutable `BoundPlan`. Its inherited `prefit_raw`, `prefit_sha256`, `prefit_commit`, path and runtime identity refer to the actual committed truthful-true document. `actual_document()` always parses that raw provenance. `document()` returns a detached transient legacy view that changes exactly the top-level generic resource flag to false. All other values, keys and arbitrary added provenance remain canonically identical. The unchanged scientific prefit validator must pass the view. The view must never be saved or advertised as the actual prefit.

The old writer and supplied-campaign replay separately verify the actual raw byte digest and validate `plan.document()`. Neither requires `strict_json(plan.prefit_raw) == plan.document()`. The old adapter and runner compare supplied prepared documents with `document()`, and use its unchanged source-pool fields. The old per-checkpoint identities continue to bind the actual raw prefit SHA. All numerical configurations, source masks, IDs, features, effects, pair rosters, weights and scaling are unchanged.

`identity()` retains the old identity and adds `calibrated_resource_compatibility_view`. This descriptor binds raw SHA, canonical actual/view hashes, the one declared field change, root-admission SHA/path/commit, caller-verified context hash, policy/authorization/scope, actual prefit/current owner receipt hashes, runtime/input/source identities and an explicit statement that the view is not persisted provenance and grants no actual execution authority. The unchanged writer includes this identity in campaign birth and completion; checkpoint campaign-birth hashes transitively bind it. The descriptor never claims original resource guards remained unchanged.

## Small supplied-byte API and external authority

`bind_calibrated_plan(prefit_raw, admission_raw, context_raw, *, committed_reader, verify_root_context)` is pure except for those mandatory caller-owned verification callables. It compares both actual prefit bytes and root-admission bytes to their exact declared commits before returning a plan. It requires the context verifier to return the Python singleton `True` for the exact bound request, and rejects mutation of that request. No default, fake, permissive or automatically selected production verifier is provided.

The prospective admission/context schemas are fixed in `spec.py`; they are not existing project certificates. They bind the actual raw-true prefit SHA/commit, runtime, input-admission-map SHA, this library's eventual source manifest, the approved `a49b82f...` policy, `b67d5d...` authorization and `c40b929...` scope, prefit owner receipt and current owner receipt. The root admission also declares the exact additional top-level provenance field names. False authority-grant fields and the sole projection declaration are mandatory.

A future source-frozen controller must supply its fixed independently reviewed exact-Git reader and a real context verifier that actually checks approval, actual owner/job, live resource policy, runtime origins, input bindings and source closure. An arbitrary callback or matching JSON declaration does not establish those facts. This library can verify logical supplied-byte binding but cannot authenticate Win32/process state, Git implementation, live reserves or native origins on its own. Its object type is not a FIT capability. Construction or a source test never authorizes a stage.

## Narrow prepared-pool rebinding

`rebind_prepared(plan, prepared)` requires an original `PreparedPools`. The unchanged original false-flag document must validate. Every original key must still exist with canonically identical value in the projected actual view; only the declared extra top-level provenance keys may have been added. Every supplied pool binding must equal its immutable view entry. It then returns a new original `PreparedPools` object, retaining the exact metadata and pool objects by identity and attaching the projected document. The original object/document is not modified.

Rebinding does not recalculate or admit native arrays. The old engine's actual array/pair/weight/scaling hash checks and the future controller's input/runtime/owner/integrity checks remain required. Actual extra provenance is retained rather than silently dropped. No solver, source selection, lambda grid, checkpoint count, objective, gate or scientific estimator changes.

## Invented tests and remaining work

Tests use only invented full-count ID lists, declared hashes and supplied JSON; no project values or scientific package is loaded. They check one-field projection, original validator rejection of true, raw-byte/commit retention, unchanged arbitrary provenance, detached immutable plan results, actual/view/owner descriptor hashes, original writer subclass/birth compatibility in a temporary invented directory, exact-commit/context-verifier failures, strict return type, mutated verifier requests, wrong runtime/input/source/owner/approval/schema, and exact prepared-pool identity/equality rules. The temporary test writes only an invented campaign birth, with no model checkpoint or optimizer call.

The next integration remains prospective: prepare and independently verify an actual truthful prefit under its separately admitted controller, commit its raw document and real root admission, provide reviewed real reader/context-verifier implementations, and replay bindings before any actual campaign. Current source and invented evidence do not establish actual stage readiness, resource success, numerical parity or biological benefit.

The first 15-test pass and its source hashes are preserved. Initial source preparation stopped because a predecessor's existing artifact `.gitattributes` marker was outside the new freezer's path allowlist. The incident preserves the initial source snapshot; no manifest or project stage was created. The narrow preparation repair admits only existing pinned static artifact markers, with no new artifact writes, and the unchanged 15-test suite is rerun into a separate reviewed receipt. No binding, projection, resource, numerical or tolerance rule changes in this repair.
