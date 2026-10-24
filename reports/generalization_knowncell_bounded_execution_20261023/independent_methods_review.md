# Independent methods review of the resource-policy proposal

Source-review verdict: **PASS for review of the proposed metadata-only
entrypoint, with no remaining concrete blocker found in that entrypoint.**
This is not human authorization, validation of lower-memory operation, an
actual metadata admission, or readiness of all seven scientific stages.

The reviewed execution manifest is
`a49b82f965dd6e389f908764d2bf1c331eb3441fe8a0d683b0fca2466c847ba9`.
I independently rehashed all **326** declared source/static/software-evidence
files (5,192,822 bytes), found zero mismatches, and parsed all **157** pinned
Python sources. No project CSV, array, label, checkpoint or protected outcome
payload was opened. I did not run tests, a worker, the public calibration
context, Win32 resource probes or scientific packages.

The two preserved invented-test receipts match their current source maps:

| Receipt | Reported tests | SHA256 |
|---|---:|---|
| controller_tests_receipt.json | 26 | 96280a777c6d0e833e950ddfcf8c1f4605ea63067bcb05435404c0050364446b |
| calibration_tests_receipt.json | 21 | 3f0d034859a8cd4a5cb8ea572e56872e7954f18bedad120a4814b7a60efb1a49 |

Their 47 tests are source/mock evidence reported by the producer. They do not
establish actual Job behavior or safe full-cohort resource use. At this review,
authorization.json, metadata_attempt_birth.json, metadata_worker_completion.json
and the shared cache prefix were absent.

The policy is one scientific worker, one numerical thread, 512 MiB physical
headroom and 1.875 GiB system commit headroom at startup; 256 MiB physical and
1 GiB commit reserves while active; 1 GiB disk reserve; 768 MiB process and
896 MiB Job limits; a 1,800-second owned-stage deadline and 100 ms polling.
Automatic retries, resume, spending and scientific protocol changes are
forbidden. Only metadata is currently an implemented entrypoint. The other
six stage names describe proposed resource scope and require separately
committed, independently reviewed controller admissions before alias entry.

The final source resolves the concrete issues raised during review:

- The exact captured manifest bytes are SHA-checked and Git-checked; a later
  reread cannot substitute a different initially committed identity.
- Pinned Job.spawn creates suspended, assigns to the exact Job, and verifies
  membership and hard limits. Child.resume verifies both again before resume.
  The child's own membership check correctly relies on that parent half.
- Parent monitoring performs resource/process/Job queries without blocking on
  whole-source hashing. Terminal process and Job peaks, actual resource values
  and elapsed time are checked while creation handles remain available.
- All final source, approval, birth, completion and bundle checks precede the
  final actual resource/deadline sample and terminal receipt. No subsequent
  provenance check can invalidate an already saved PASS.
- Deleted or replaced resource aliases are detected without bypassing the
  unconditional restoration of all five original callback objects. A failed
  or caught resource check cannot leave a successful context.
- Annotation uses reviewed resource fields, preserves scientific guard
  statements, and leaves metadata rows and contracts unchanged. It corrects
  the four metadata original-floor claims and records restoration as pending
  until the separate completion proves restoration. Old sources and the pure
  original admission function remain unchanged.

Independent metadata reconstruction is a **remaining workflow integration
gap**, not a reason to claim this resource-policy review failed. The current
fixed metadata birth permits one acquisition opportunity. It cannot silently
represent a second separately owned reconstruction worker. Before array
admission, a future additive controller generation must provide a distinct
fixed invocation/birth/receipt, source admission and independent metadata
verification, preserving all acquisition evidence. This is verification of a
completed acquisition, not a retry or reuse of its birth. Approval wording
must explicitly cover both metadata invocations under the same policy and
state whether the 1,800-second limit is per owned invocation; this review
does not silently expand a total-family time limit.

Future array, label, pool, fit, replay and evaluation controllers remain
unimplemented here. They must establish actual runtime origins, scientific
and input admissions, global one-worker coordination, exact pools and prefit,
checkpoint births, independent replay and unchanged evaluation gates. In
particular, the current original-floor label bridge deliberately rejects an
honestly calibrated original-gate=False label receipt; a separately reviewed
integration is required. Already-hashed nested software proofs also need
stage-specific preservation rather than generic recursive rewriting.

Observed critical source hashes are:

| Source | SHA256 |
|---|---|
| common.py | ea7c7eda94a86c734336094fb0fe41f082aaacd301b224fddc1078d6479197fe |
| supervise.py | 6c7bbb2b15477dfb4a1f39695f0a0920694225dd2f1c128b905457b3f1a24da6 |
| worker.py | 07826c48851cf243739605fafe83d04611fc3d133ed506262c1ab3c69f4df547 |
| calibration.py | 79651a44d4b8681f5d32da178ec022aa03b53e8bac4b9d64e10e82139e2a7c27 |

No generalization, biological mechanism, compatibility beyond the reviewed
evidence, or successful lower-memory execution follows from this report.
