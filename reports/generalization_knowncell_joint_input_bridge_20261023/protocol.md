# Exact sampler and supplied-input bridge — source preparation only

These two deferred helpers connect the unchanged original sampler and original
loader outputs to the already frozen joint-known-cell engine. They expose no
CLI, worker, runtime bootstrap, file writer, optimizer, or alternative sampler.
This preparation uses source text, static readiness summaries and invented
fixtures only. It does not load actual labels, arrays, metadata or a provider.
Every actual helper call retains the default original 3 GiB available RAM,
1 GiB disk and one-thread guards. No caller-supplied replacement guard exists.
All previously approved PUM/PRELib exceptions are inapplicable.

The source-only factory extracts exactly the sole pair_indices FunctionDef
from committed src/cross_assay_20260927/models.py, full SHA256
a7d43f49c37e0e2a86e5c9c64cbf97bca78aabab36a007f10f886fb916d54d71.
The original common.py full SHA256 is
dfb658f9fd437bae5fef2b1ae33ae0bd9167a1b118394756bab8e81f8b6745dc.
The sole SEED=20260927 declaration and original empty PAIR_CACHE declaration
must remain exact. The function AST is not edited. Only that FunctionDef is
compiled, with globals np, hashlib, itertools, original seed and a private
PAIR_CACHE, plus the original module __name__. The original modeling/common
modules and their broad imports are never executed. No alternative RNG,
sampling cap, pair selection, tie rule, cache key or old pair weight is added.
The existing engine later replaces original study weights using its unchanged
hierarchical preference contract; this factory performs no such replacement.

The returned GuardedSampler is transparently new wrapper code. Its intentional
callable name/module match the engine's pair_indices identity check. Its
receipt separately records full original source, extracted function source,
AST, seed, original compiled filename, wrapper source and supplied actual
runtime-proof hashes. It does not pretend the wrapper was compiled from old
source. The wrapper gates before every call, including a cache hit, checks the
original globals, delegates unchanged, and gates after success. Failure poisons
that handle; no automatic retry is provided. Factory source reads, compilation
and function definition are separately gated and source/Git-pinned. Tests
exercise exact AST/globals and an invented original-cache path. Actual native
NumPy/pandas sampler-roster parity remains unperformed and is not certified.

The second helper accepts supplied metadata-bundle bytes, the admitted ndarray,
array-certificate bytes, existing labels_result and FIT-label-manifest bytes.
It requires exact committed supplied metadata/array/FIT bytes through the old
pinned Git helper. Its expected_bindings are a NEW prospective root declaration,
not invented fields added to an existing loader result or an admission produced
by this module. Root must verify that declaration and bind this bridge's own
sources in a separate actual-stage controller. The binding fields are the
metadata bundle, array certificate, FIT-label admission, runtime binding,
FIT source manifest, native profile, numerical source and lifecycle-v2 manifest
SHA256 values. Here runtime_binding_sha256 is explicitly the canonical hash of
the array certificate's existing accepted after_array proof; the native-profile
receipt remains the original accepted V4 origin dc3e6a1e2f31b5d6c868de7302feb0e1e719835cc370f0eb5eacb307d08b5b2b.
This binding does not assert a new fresh native proof after label parsing.
Future actual-stage and checkpoint controllers must separately check current
origins, runtime identity, committed admissions and resource headroom.

The exact existing provider after_array schema is recognized, including its
request/software/NumPy identities and separate fresh-proof hash. It is not
inferred from invented runtime compatibility. The shared absent provider cache
prefix, -S and -B remain required. No provider is called by either helper.
Actual FIT-label runtime/provider integration and its separately committed
authorization remain external; the currently array-only provider does not
automatically authorize or implement a label stage.

The bridge rechecks the full frozen metadata/menu/split/count contract and
original ID order, certificate metadata hash and original array scalar-byte
hash. It requires ordinary native float64 ndarrays of exactly 13781×102 and
13781. Matrix bytes remain unchanged. The sole effect conversion is the actual
original measured_delta.tolist(); every result must already be a finite Python
float. The bridge never parses a string or coerces an unknown label type. It
replays the loader's little-endian float64 effect hash, preserving signed zero,
then forms the exact ID-to-Python-float mapping in original row order. It also
rechecks the original parser identity, unflipped orientation, source-core hash,
metadata/array/software/FIT bindings and no-fit flags. Missing, extra, reordered,
mutated or otherwise mismatched inputs stop, without repair or filtering.

It returns the original matrix, metadata, ordered effect map, engine-compatible
admission declaration and an explicit incomplete bridge report. Input matrix
and effect hashes use the existing engine's exact C-order native float64 header
and byte convention. No source pools, prefit, checkpoint, model, replay or gate
is produced. Root must complete and commit all actual admissions and the exact
shared pools/prefit before any of the fixed 63 checkpoints/84 optimizer units.
No biological or generalization result follows from these source tests.
