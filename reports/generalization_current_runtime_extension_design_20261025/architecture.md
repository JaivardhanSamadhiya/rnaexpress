# Current-runtime extension: design only

Recommendation: introduce a lean, honestly named current execution context with a small scientific compatibility adapter. Preserve original files and proofs as historical records. Do not copy the full chain of legacy controllers merely to satisfy fields that mean the old runtime is currently valid. This document implements no guard, admission, bootstrap, retry or scientific operation.

## Present readiness

- The original resource manifest, human record and scope remain exact historical bytes: `a49b82f965dd6e389f908764d2bf1c331eb3441fe8a0d683b0fca2466c847ba9`, `b67d5d45abdd6812997d3b84f6cbd5ff2abaf68cd8786638f5312d2744ab24e3` and `c40b929187a35199e88523ab5c6b351789c45fddb3aebe6dcf68172684ce6495`.
- Root reports drift in 38 of 42 current native fingerprints. Version equality is insufficient. The old policy's `admit_authorization()` calls its old native `verify_sources()`; the old bootstrap/current-payload checks also enforce obsolete native expectations. Those functions must remain unchanged and must not be wrapped to produce a false current PASS.
- The actual refresh V2 inventory attempt failed with an I/O error, followed by a failure-record write error. Its file coverage and current-runtime admission are incomplete. Later successful reads do not establish stable storage. No old hash, incomplete inventory, omitted file, cached PASS or automatic retry can replace the missing proof.
- The latest manual FIT attempt is consumed. Its original operational completion is unknown. Saved checkpoint declarations are not a complete accepted campaign, and none of those models is scored or used for selection/tuning by this design. Any future FIT needs a separately reviewed concrete scope and a new actual manual authorization; none is requested or created here.

These are independent software, storage and execution-readiness blockers. They are not evidence of a negative biological result or a proven cause of the earlier process disappearance. No drive repair, relocation, host-job breakaway, global-guard change, cache modification, spending or scheduling is proposed.

## Two options

| Option | Concrete change | Benefit | Main cost or risk |
| --- | --- | --- | --- |
| Additive policy/provider/bridge/projection extension | Add a current-native policy verifier, new provider, new current-input bridge and a new `BoundPlan`-compatible binder; stage-specific controllers call these directly. | Retains the established layering and scientific identity. | Keeping every legacy wire schema creates many generations and misleading old-current field names. It must never call old authoritative native admission to manufacture compatibility. |
| Lean current protocol with explicit scientific equivalence | Define `HistoricalScientificReference`, `CurrentSoftwareIdentity` and `OwnedAttemptContext`; use one fixed current guard/provider and a minimal scientific `BoundPlan` adapter. Delegate exact original scientific functions. | Separates data history, present software and stage authority in a truthful schema; substantially less copying. | Requires careful equivalence tests and a new reviewed integration contract. It does not inherit an old operational PASS. |

Prefer the second option. It can use the first option's narrow policy and `BoundPlan` mechanisms without reproducing all legacy runtime/controller schemas. A new protocol here is an operational renewal, not a change of hypothesis, method, primary endpoint or scientific gate.

## Three separate identities

**Historical scientific reference.** Bind exact committed metadata, NPZ/array certificate, persisted label certificate and bit hash, actual prefit, root projection admission, source manifests and sampler. The admitted label list is decoded and packed exactly as before; no CORE read, pandas reparse, truth recomputation or altered orientation occurs. Reload the same NPZ by the original `np.load(..., allow_pickle=False)['features'].astype(float)` convention and verify the same shape, finite values, raw/cast hashes, row order and cross-cell allele parity. All nine rebuilt pool bindings must exactly match the accepted prefit. Missing rows, intersections, tolerances, fallback zeros or changed menus are forbidden.

The old array after-proof anchor and old native-profile receipt remain historical provenance keys. Keep those bytes unchanged. Do not label either as the current native identity. Original admission mappings can remain internal scientific-reference inputs to pure legacy functions, with this meaning made explicit outside them; they are not a present runtime capability.

**Current software identity.** Require a complete newly sealed inventory with the exact current 42 native paths/hashes and the unchanged 7,998-file D: scientific payload. Reject missing, extra, aliased, escaped or unreadable files. Check the actual executable, current loaded native origins, declared package paths/versions and full admitted payload; a version string or metadata inventory alone is insufficient. Any additional cache allowance must remain the exact previously declared allowance, not a widened glob.

Require a new owned, invented-only parser/optimizer/native profile under that identity, including the unchanged original pandas parser/options, exact accepted invented numerical reference comparisons and before/after loaded-origin proofs. The previous finite tests may be reused as source fixtures. Do not call the old `current_payload()` or original authoritative bootstrap and make its old checks appear to pass. A new explicit bootstrap must validate the new inventory, then import the unchanged scientific package payload with fresh resource checks before each top-level import and proof action. It must check actual loaded origins after imports/lazy numerical loads and reject drift throughout the stage.

A finite compatibility profile does not establish universal old-interpreter bitwise parity. Preserve that limitation. If exact declared comparisons fail, report the gap; do not select a favorable subset, loosen the comparison, alter scientific constants or use study outcomes to repair compatibility.

**Current owned attempt.** Bind a new source generation, software admission, committed request, exact scientific reference, real owner/job/birth and stage-specific authorization. Historical resource-human evidence can be verified directly as exact committed bytes and schema; do not invoke its now-invalid native gate as present authority. The new generation itself must pass its real current-native/source checks. A compatibility certificate is not FIT permission. A missing new manual FIT authorization or missing stage prerequisite always fails closed.

## Minimal future source plan

The following are proposed modules, not files implemented by this design.

| Module | Responsibility and hard boundary |
| --- | --- |
| `historical.py` | Check exact old source/human/data/projection bytes and commits as historical evidence only. No old `admit_authorization()`, native PASS, data read, import or stage authority. |
| `current_guard.py` | Fresh exact current-source/native/payload verification and actual resource/environment checks; no injected public probe or native verifier. Source closure and regular parent inits are mandatory. |
| `provider.py` | Explicit current bootstrap and actual-origin proofs using the new profile. One owned set of software objects; request/phase/owner changes poison the process. Separate new current proof from historical anchors. |
| `inputs.py` | Verify supplied old certificates/values/bits and guarded reload of the same NPZ. New current-proof contract; no call to a historical checker pretending to establish current runtime validity. Return the original metadata/features/effects and unchanged scientific-reference bindings. |
| `plan.py` | A minimal subclass of the original pure lifecycle `BoundPlan`, with the exact original scientific document/view and stable identity, plus a separate new execution context. No old current-context PASS fields are fabricated. |
| `context.py` | Join the historical reference, current software and actual owned stage. Fixed real dependency paths and source pins; no public Boolean/callback that grants native/owner authority. |
| Small stage entry points | Reuse original runner, arithmetic replay and evaluator. New truthful receipts and sidecars identify the current generation/native profile/birth while delegated scientific artifacts retain their original format. |

The old projection binder cannot be used unchanged to claim current validity: it requires `current_runtime_binding_sha256` to equal the old data anchor. Instead, the new binder independently verifies the old admission's static scientific fields and exact commits, and verifies a genuinely new current context. It constructs the compatible pure plan without passing a manufactured old-current context into an authoritative binder.

The original runner/writer and whole-campaign replay require the generic lifecycle `BoundPlan` type, so a compatible new subclass is feasible. Its scientific identity must be canonical-byte equal to the old stable V2 identity; current owner/native evidence stays in a distinct execution identity. The pre-existing sole resource-compatibility view remains explicit; raw prefit/projection bytes and scientific keys are unchanged. A narrow rebinder reproduces the original exact scientific-key/pool equality checks with the new type. Test this before any study operation.

The same five-alias resource transaction and real owned-job implementation may be reused at their approved narrow boundary. A new fixed factory calls the new current-context verifier; it must not monkeypatch old policy/provider functions or supply a fake guard. Deletion/replacement/restoration failures, low resources or native/source drift poison the stage. Current resource annotations must state the actual extension/policy/owner proof and must not relabel historical certificates.

## Acyclic freeze and authority order

1. Current refresh source and complete inventory, preserving all failed refresh evidence.
2. Invented-profile source, actual owned profile, independently reviewed software admission.
3. Current-context source closure, historical-reference contract and current-policy extension source/admission.
4. Stage source and controller-source admission; then static scientific binding, runtime request and a complete prospective run template/precise scope, with no unknown response/birth hash invented.
5. Any separately required actual manual authorization binds that reviewed source/scope/template. Only afterward create the final exact run admission containing the actual authorization hash; then exclusive owned birth, real current proofs and execution receipts. No authorization/run hash cycle is permitted.

No source/profile admission includes future run, birth or current-proof hashes. Dynamic PID/birth/current-origin evidence is produced inside the real owned stage. A fixed caller's source can be included in provider preparation without embedding that preparation's eventual hash in the same caller source. Stage source must pin the current extension, not pretend an obsolete native source generation passed. No placeholder hash is an admission.

## Science and artifact invariants

The original three arms, three lambdas, nine pools, 63 checkpoints/84 optimizer units, weights, pair sampling/scaling, gene/component/allele purges, source-only OOF selector, exact score ties, replay tolerances, full menus, bootstrap draws/seed and thresholds remain fixed. Original pure sampler, adapter, numeric routines, lifecycle writer, whole-campaign arithmetic/reselection and evaluator are delegated by exact source identity. No new selection, scoring of saved models, reuse/resume, convergence gate or favorable filter is introduced.

Use a new truthful envelope with separate `historical_scientific_reference`, `current_software_identity` and `current_owned_execution` sections. The original runner's integrity hook can retain current native/source/owner evidence before each checkpoint birth, keyed by task and stable scientific identity. After the original writer completes, a new receipt binds those phase-proof hashes to the exact birth/model/completion bytes. This is explicitly a post-write byte binding, not a retrospective claim that a missing creation-time certificate existed. A stricter after-birth/before-optimizer hook would require a separately reviewed new orchestration adapter; do not silently monkeypatch the old runner to supply one. Old generic runtime-binding keys inside pure scientific artifacts are documented provenance references, not present software attestations. Record `old_native_identity_currently_valid=False` and `original_study_operational_pass_inferred=False`; never substitute a current proof hash for an old accepted proof or vice versa.

Actual successful FIT, complete independent replay and evaluation still require their own complete closures. A file count, declared optimizer units or historical saved model does not supply a missing closure. Any future permitted use of old saved models would require a separately declared review; this design authorizes none.

## Before implementation or execution

- Review the chosen schema and minimal source plan; do not mass-copy controllers first.
- Resolve the incomplete current inventory and the independent I/O readiness blocker through separately authorized diagnostics/actions. Preserve D: and existing caches; no repair, relocation, file omission or automatic inventory retry is implied.
- Add invented tests proving rejection of old-current proof substitution, incomplete inventories, read errors, changed current native files, altered data bits/IDs/pools, caller/source changes, bad owner/jobs and restored aliases. Prove canonical scientific-plan equivalence without any study payload.
- Require complete durable inventory/profile writes and close/hash checks before PASS. A failure-record write error must not be converted into success; preserve available error/parent telemetry and stop. Diagnostics should identify the attempted path and read offset before failure without widening scientific access.
- Treat the 18-minute launcher toy as a separate finite lifetime experiment. It does not establish a termination cause, stable storage, numerical admission or permission for another FIT.

No actual inventory retry, native/scientific import, project payload, model, fit, replay, evaluation, authority record or resource/host change was performed to produce this design.
