# Guarded exact-array admission API — source-only preparation

This additive API prepares one future array-only admission. It does not run a
project stage, bootstrap a scientific runtime, open biological metadata or array
payloads, parse labels, fit models, or write an admission certificate. Invented
tests and source preparation are not biological admission.

The exact frozen simple102 array is declared as
`artifacts/generalization_crosscell_20261007/simple_model_features.npz`, SHA256
`490ab90c1289ea50a75ff6960b9a979f2f2bd747b1c9419ed7c085383272c8a6`.
Its original creation and metadata receipts are respectively
`results/generalization_crosscell_20261007/prepare_receipt.json` / SHA256
`41f50e2422ce2998278c9ddb9655b5f4a960c594edb82325b06e748f0ada6a2f`
and `results/generalization_crosscell_20261007/metadata_receipt.json` / SHA256
`99bc4ad1086c0113dfcd1fdff27b7ea59755ef1bb19cc4d12c206f3e134a2e1a`.
These declarations come from the immutable original crosscell prefit manifest,
SHA256 `547a4765e225f47c2564daa978951bc380b00933fc27220663fbe38efe8bb345`.
Preparation reads that static declaration only, never those three payloads.
The reviewed separator normalization creates a separate map and rejects alias
collisions; it does not change the original Windows-keyed file map.

Future execution requires root_start=True and a separately committed
`results/generalization_knowncell_array_admission_20261023/array_request_manifest.json`.
That request must bind this committed source readiness manifest, the committed
metadata bundle, exact original payload pins and ID order, the reviewed array
contract, and a separately reviewed and committed deferred runtime provider.
It must explicitly authorize runtime imports and forbid label and FIT access.
The original metadata-only admission must already have completed and its exact
bundle must be committed. No substitute or inferred metadata is allowed.

Software evidence is the actual V4 verified status SHA256
`e1938a597c18ecf144c42724371aed2c58c8a064889fef89d5ba8a767497d821`
and loader pandas-admission software certificate SHA256
`923ff701e31b7c09969ff01dc63cb6560821a97176e8e85bd76cb841021c260e`.
Their existing schemas certify invented current-runtime compatibility and
explicitly grant no biological admission. They are not required to contain
invented future actual-runtime fields. Instead, the future committed request
binds the provider preparation SHA and exact source/function identity. The
provider must return fresh actual current-Python and loaded-native-origin proof
before and after validation, bound to the identical request and software hashes.
The original V4 profile-origin SHA remains distinct from each new proof SHA.

Both the array API and provider use this one never-created cache prefix:
`results/generalization_knowncell_runtime_provider_20261023/source_cache_must_remain_absent`.
The worker must use -S -B and that exact -X pycache_prefix. The path must remain
absent; this API never creates it. Every actual read, provider invocation and
native validation has the original fresh 3 GiB available physical RAM, 1 GiB
disk and one-thread checks. The actual guard is not injectable through the
public API. PUM and PRELib exceptions do not apply.

Canonical provider call is provide(request_binding, phase=..., root_start=True).
The binding contains exactly request_relative_path, request_sha256,
provider_preparation_manifest_sha256, software_status_sha256 and
pandas_admission_sha256. Phases are before_array and after_array. The provider
returns np, pd, minimize, expit, actual_origin_receipt_sha256, fresh_origin_proof
and fresh_origin_proof_sha256. This API uses np only. The proof hash uses sorted
compact finite JSON plus a trailing newline. No fresh-resource callback is
passed into the provider. Actual origin checking is the provider's obligation;
this API additionally binds its exact committed source/function and NumPy
module path, version and source SHA.

The NPZ acquisition uses bounded guarded_payload with a 32 MiB compressed cap,
exact original SHA and complete-stream hash. The existing supplied-byte array
validator receives the full actual metadata rows and original receipt bytes.
It checks all 13,781 rows × 102 columns, finite values, original creation order,
NPZ/NPY envelope, original astype(float) scalar bits and exact same-allele feature
bytes across both cells, with no tolerance or zero filling. This wrapper does
not replace that validator or permit alternative arrays. Readiness maps cannot
smuggle an array, CSV or outcome payload into source validation.

Only after all checks does the function return matrix plus a certificate with
status PASS_EXACT_FROZEN_SIMPLE102_ROWS_VALUES_AND_ALLELE_PARITY, exact NPZ and
metadata bundle hashes, dimensions, both fresh runtime proofs and the complete
underlying validation report. Root must save that certificate exclusively and
commit it in a later authorized step. No file is written by the API, no label
or FIT permission is granted, and no complete biological trainer is claimed.
The real request, metadata completion, actual provider acceptance and full-size
array validation remain separate future prerequisites.
