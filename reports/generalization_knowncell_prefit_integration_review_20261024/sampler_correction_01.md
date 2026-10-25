# Sampler requirement correction

24 October 2026. This additive correction preserves design.md unchanged at
SHA `8d634a3836d09d005db9f40e6f706f5a930930794a5554ecf9a2e514ff8804c1`.
It supersedes that report's sampler table statement requiring the actual
broad model-module function and prohibiting a source-extracted function. That
statement was too restrictive and contradicted the already frozen, reviewed
original supplied-input bridge. It is a reporting error, not a discovered
sampler or scientific failure.

The accepted existing design is
[sampler.py](D:/rnaexpress/src/generalization_knowncell_joint_input_bridge_20261023/sampler.py:11).
It verifies exact original models/common bytes and the sole fixed seed,
extracts the exact original `pair_indices` AST, checks its identity, and compiles
only that function with the original compiled code filename. Its isolated
globals contain admitted NumPy, hashlib, itertools, the fixed seed and a new
private empty PAIR_CACHE. It does not import the broad historical model/common
module or execute their other top-level code. The newly declared GuardedSampler
wrapper transparently exposes the name/module expected by the old engine,
checks its original globals, enforces actual guards even on cache hits, and
poisons its handle after failure. Its new-wrapper identity is disclosed.

This is reviewed exact original **algorithm/source reuse**. It is not a claim
that the wrapper is the original imported module object, that the original
module was loaded, or that source/invented tests prove historical native RNG
or whole-data sampler-output parity. Those distinctions are already explicit
in the original readiness/factory receipts. Actual current runtime admission,
exact source/seed/function-AST bindings, transparent wrapper/compiled-function
identity, allowed globals/cache and fresh genuine guard/source checks remain
mandatory. The frozen engine's callable name/module/source-SHA checks are
intentionally satisfied by that declared wrapper.

The integration should retain this frozen readiness and sampler path rather
than introduce a new broad-module import requirement. No scientific method,
sampler AST, seed, pair cap, tie handling, source array or protected boundary is
relaxed. The new calibrated supplied-input bridge does not load or call any
sampler; it preserves the old source readiness for a future reviewed actual
caller. No source files were changed for this correction and no actual
sampler/native/data execution occurred.
