# V3: prospective binding and current process evidence are separate

The V1/V2 sources, manifests, reports, tests and logs remain unchanged. V2 had a
real integration defect: its committed root-binding schema required a future
birth and fresh-origin hash before those values could exist. This additive V3
fixes only that operational timing contract. No science, parser, data source,
sampler, shape, scalar bits, feature/effect hash, runtime anchor or resource
alias is changed. No actual source payload or model is read/run in preparation.

Use the mandatory supplied-input API:

```
bridge_v3.bridge_inputs(
    np, metadata_bundle_bytes, matrix, array_certificate_bytes,
    label_certificate_bytes, root_binding_bytes,
    current_stage_origin_proof, current_owner_context, *, root_start=False)
```

Static binding path:
`results/generalization_knowncell_calibrated_input_bridge_20261024/root_bindings_v3_<stage>.json`
where stage is one of `prefit`, `fit`, `replay`, `evaluation`.
Its exact status is
`FROZEN_STATIC_ROOT_CALIBRATED_INPUT_BINDINGS_V3_NOT_FIT_PERMISSION`.
It is supplied as bytes and must be exact current committed bytes. It has the
same namespace/stage/reviewed-controller/policy/AUTH/scope/caller-required fields
as V2, with these preknown SHA fields only:

- `metadata_bundle_sha256`
- `array_certificate_sha256`
- `array_supervisor_sha256`
- `label_certificate_sha256`
- `runtime_binding_sha256`
- `fit_source_manifest_sha256`
- `numeric_source_manifest_sha256`
- `lifecycle_v2_manifest_sha256`
- `native_profile_receipt_sha256`
- `bridge_readiness_sha256`
- `reviewed_controller_admission_sha256`
- `reviewed_controller_source_sha256`

The static document explicitly rejects `caller_birth_sha256` and
`current_stage_origin_proof_sha256`. No post-start commit handshake is needed.
No actual root-binding file is created by this preparation. Actual certificate
SHAs are supplied by root through that later committed static document, not
inferred by reading certificates during preparation.

The required separate live context has exactly these keys:

```
status = SUPPLIED_CURRENT_OWNER_CONTEXT_REQUIRES_ACTUAL_FIXED_CALLER_VERIFICATION
stage
current_pid
parent_pid
caller_birth_sha256
current_stage_origin_proof_sha256
static_root_binding_sha256
reviewed_controller_admission_sha256
actual_parent_Job_and_native_origins_checked_by_fixed_caller = true
runtime_and_FIT_authority_granted_here = false
```

The context is generated and actually checked by the fixed reviewed owned
caller after birth/native admission. The bridge checks current integer PID and
parent PID, exact static raw-byte SHA, reviewed controller-admission SHA and
fresh proof's compact canonical SHA. The proof retains the V2 current-stage
schema/status and phase `before_supplied_input_bridge`, adds the same
`static_root_binding_sha256`, and binds the same stage, PIDs, caller birth,
controller admission and stable admitted runtime anchor. Its dynamic UTC and
hash may differ between processes without changing the precommitted binding.
The original pure proof-schema checker is reused with explicitly assembled
transient live checker arguments; this is never persisted as a root binding.

The output's separate `bridge_report` records current birth, proof and context
SHAs alongside static binding and stable runtime SHA. These are operational
provenance; scientific engine admission hashes and scalar values remain the
same across two valid live contexts using the same static document. The bridge
does not certify a Job or loaded native origins from dictionaries: it states
explicitly that actual owner/runtime verification belongs to the fixed caller
and that no runtime/input/FIT authority is granted here. Genuine reviewed
Win32 owner checks and fresh current-origin checks must precede this call.

V3 retains all14 invented V2 cases, adapting the operational tests for the new
mandatory context argument. Five further tests cover two distinct current
contexts with the same static bytes, forbidden live fields in static bindings,
owner/proof/static-byte/PID cross-binding corruption, and exact scientific
validation AST equality to V2. Test PIDs are those of the real invented-test
process; Job/native proof declarations remain invented and nonauthoritative.
The negative tests use private mocks only, never real resource/Git callbacks.
Clean production source-import closure, including package inits, is audited
before the additive source freeze. No sixth alias or new resource callback is
added and no actual root bindings/admissions/jobs are created.
