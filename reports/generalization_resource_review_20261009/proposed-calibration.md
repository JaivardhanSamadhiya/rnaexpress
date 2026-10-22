# Proposed PUM2 resource calibration — 9 October 2026

Status: **STATIC REVIEW ONLY; IMPLEMENTATION AND EXECUTION NOT AUTHORIZED.** This document preserves a concrete proposal for explicit user review after automatic approval review rejected a RAM-floor adapter. It does not change a guard, launch a worker, create a job object, or certify a lowered threshold as safe. Root must separately review/freeze any eventual implementation; approval of this document's existence is not approval to execute its proposal.

## Observed state and rejection

Root reports installed physical memory 15.651 GiB, available physical memory fluctuating approximately 0.36–1.1 GiB, and approximately 4.95 GiB commit headroom. These are root-supplied snapshots, not fresh measurements by this reviewer, and the exact commit-headroom API provenance is unverified here. Queue PID 18748 is reported waiting, not modified or independently queried in this review. Installed memory does not establish memory currently available to a child.

Automatic approval review rejected the proposed additive adapter before its files were created: authorization to weaken the exact 3 GiB free-RAM requirement was unclear, and system-disruption risk remained unresolved. This document is the permitted review response. No indirect guard bypass, unguarded producer call, source callback replacement, environment trick, forced paging, app termination, or runtime change was performed.

The committed queue requires caller free physical RAM >=3.5 GiB, no other project Python workers, and unchanged original worker admission. It has a six-hour overall waiting deadline and stops on a one-shot phase failure. Its frozen order is conservation blocks, PUM2 fixed features, PUM2 independent replay, and synthetic masked-native admission. The three scalar/metadata workers each require >=3 GiB physical RAM; masked-native additionally requires >=5 GiB workspace disk. The queue and all four original entry points remain unchanged.

## Static shape analysis

These are logical payload calculations and source-derived allocation observations, **not peak RSS/private-commit measurements**. No project sequences, conservation values, count measurements, phenotype tables, feature arrays or model tensors were loaded by the reviewer.

| Work | Fixed dimensions / logical payload | Allocation caveats |
|---|---|---|
| PUM2 fixed producer | 4,070 sequence rows, four modes; 4,054 point deltas ×4 float64 numbers =129,728 bytes (0.124 MiB) | Standard-library implementation. At most 1,696 register objects per one mode/allele are transient; persisted results contain five scalar fields per mode, not every register. Source metadata, one background's records and JSON serialization coexist. `sha()` reads whole pinned files, so the largest pinned input affects peak. No total bound is established. |
| PUM2 independent replay | Same 4,070 sequences and four modes; one background read/replayed at a time | Standard-library implementation; transient register keys/energies and dictionaries. It retains source metadata and per-background numerical summaries, with whole-file hashing. Independent arithmetic and frozen tolerance remain unchanged. |
| Conservation feature blocks | 13,781 rows ×16 float64 numbers =1,763,968 bytes (1.682 MiB) | Also retains 26,258 coordinate row dictionaries, 15,132 annotations, parent metadata, original CSV rows, all output dictionaries, and whole JSON/text/bytes/gzip copies. The small numeric payload is not a process-memory bound. This route is outside the proposed exception. |
| RBP cell-axis downstream | One 13,781×1,014 float64 matrix =111,791,472 bytes (106.613 MiB); six declared matrices total382.292 MiB | Training slices, normalization copies, matrix hashing, pandas, optimizer and BLAS/native imports add memory. Root's separate metadata-only maximum pair count6,715 gives51.949 MiB for one pair-difference matrix at1,014 columns, not total RSS. No fitting exception proposed. |
| Full-core matrices | 26,258×246 float64 =49.282 MiB; ×1,014 =203.137 MiB | NPZ decompression, dtype conversion, boolean validation and copies increase peak. No array was opened here. |
| Synthetic masked MLM | Static configuration512 hidden,2048 intermediate,6 layers,16 heads,10-token vocabulary; tied stock parameters approximately19,710,474, or75.189 MiB float32 | Checkpoint file78,883,755 bytes; IR weight file77,795,508 bytes, determined by file stat only. Stock model, checkpoint mapping, compiled IR, allocator/native imports coexist. At batch2/262 tokens, one hidden tensor1.023 MiB, one attention tensor8.379 MiB and one intermediate tensor4.094 MiB. These payloads exclude runtime/allocator peaks. No native exception proposed. |

The PUM2 producer enumerates14,879,920 register states over the fixed cohort/modes, sequentially rather than retaining all those objects. It has no NumPy, pandas, Torch, OpenVINO or fitting import in its direct source path. Native Python/runtime and its brief Git helper still require accounting. This makes PUM2 a plausible first calibration subject, not proof that either PUM2 process will stay under a specified cap.

## Exact provisional exception for later user review

**Only if explicitly authorized**, a newly reviewed/frozen external controller may run these two original functions serially, once: `src.generalization_pum2_fixed_math_20261008.produce_features.run()` then `src.generalization_pum2_independent_replay_20261009.run.run()`. The producer's `fresh_guard` and replay's `guard` are the only proposed process-local resource-admission replacements. Their original source files, numerical helpers and callbacks on disk remain byte-identical. The original objects must be pinned and restored on every exit path. No global monkeypatch or other worker's admission is permitted. A transparent receipt must state the original3 GiB floor and exact authorized replacement policy.

Both phases require their original committed manifests, source/parameter hashes, fixed sequences/IDs/modes, existing-output rules, provenance and numerical tolerance. No labels, fitting, favorable subset, changed estimator, fallback model or automatic retry is added. The ordinary queue's manifest, caller3.5 GiB floor, lock and PID remain unchanged; no second queue is launched. The controller and child command lines must remain recognizable as project `generalization_` workers to its existing competing-worker check. Its timeout is not extended.

| Proposed setting | Exact fixed value / behavior |
|---|---|
| Fresh physical admission | >=512 MiB (536,870,912 bytes), checked before creating each child and by every admitted replacement guard call |
| Fresh system commit admission | `(CommitLimit-CommitTotal)*PageSize` >=896 MiB+1 GiB =2,013,265,920 bytes (1.875 GiB), before each child |
| Per-process committed-memory hard cap | 768 MiB (805,306,368 bytes), applied to the owned worker and inherited helper processes |
| Owned-job aggregate committed-memory hard cap | 896 MiB (939,524,096 bytes) |
| Job ownership | One scientific child at a time. Its original brief Git subprocess inherits the same job; no breakaway. The monitoring controller stays outside that job. Allow at most2 concurrent job processes for worker+Git helper, not2 scientific workers. |
| CPU | One scalar worker; no numerical library import/thread pool. A controller cannot change a numerical policy. Below-normal owned-child priority can be considered, but is not a memory safeguard. |
| Monitor interval |100 milliseconds; record actual sample gaps and include all owned descendants |
| Immediate owned-job stop | Available physical RAM <256 MiB (268,435,456 bytes), or system commit headroom <1 GiB (1,073,741,824 bytes), or a failed/missing resource measurement |
| Lifetime | `KILL_ON_JOB_CLOSE`, no breakaway, closed only by the owning controller. Bind before child execution; failed assignment/query/cap verification means no execution. |
| Deadline |30 minutes per phase; stop only the owned job, preserve partial artifacts, do not automatically retry or extend the deadline |
| Disk | Require >=1 GiB free workspace disk before each phase; stop/report if it falls below256 MiB. No pagefile or OS configuration changes. |

The proposed controller must attach a suspended child before it executes, verify effective job/process limits and job membership, then resume it. If the host's existing job hierarchy prevents attachment, preserve the admission failure; no breakaway workaround. The controller's own memory is outside the896 MiB job ceiling, so measure and report it separately; the1 GiB system commit reserve includes that overhead and other applications.

At the reported0.36 GiB free physical state, even this proposed512 MiB admission fails. At1.1 GiB it might admit, but admission remains unapproved and safety unvalidated. Approximately4.95 GiB reported commit headroom would pass the proposed1.875 GiB condition if a fresh system-wide measurement confirmed it. Neither observation proves the run safe.

## Required measurement and failure interpretation

Record immutable prelaunch source hashes and approval-scope identity; fresh physical/commit/disk samples; controller and child creation identities; effective job limits; per-process peak private bytes and working set; job aggregate commit/peak; maximum monitor gap; elapsed/CPU time; exit code; original receipt/hash identity; and all resource-stop/limit notifications. Sample startup, all parameter/manifest loading and hashing, background transitions, serialization and replay, not merely the scalar inner loop. Check unchanged source hashes again after each phase. Use original completion and independent-replay receipts for scientific integrity; a controller log cannot replace them.

Hard committed-memory caps do not bound aggregate physical residency: mapped/shared DLLs and file pages differ from private commit. A100 ms monitor can miss or respond after a short allocation burst, and unrelated apps can consume memory concurrently. Even with all proposed settings, transient paging, UI slowdown, process allocation failure or unsaved-work disruption cannot be ruled out. No measurement presently validates these lowered physical floors. A cap violation/timeout/resource stop is an operational failure, not negative binding or localization evidence, and cannot justify changing parameters, tolerances or cohorts.

An original producer can be interrupted during an exclusive file write. Preserve partial files/logs and any already completed backgrounds; do not delete them, overwrite them, silently treat them as completion, or auto-resume. Root must review the preserved state and existing producer's immutable admission before any separately authorized retry. Exiting a controller with kill-on-close must affect only its own job, never PID18748, Codex, browsers or unrelated Python processes.

## Safe actions now under existing policy

Continue bounded source/protocol review, primary-source literature search, documentation, manifest/schema checks and chunked hashing of already permitted non-outcome source/metadata files. Keep memory use small, avoid concurrent whole-runtime rehashes or model/array imports, and honor any existing module admission. Existing author metadata downloads require their own frozen acquisition scope; this review grants no network/data permission.

Await existing queue admission naturally; the user may voluntarily close unused apps after preserving their own work. Do not terminate unrelated processes, clear system caches, change paging, purchase compute, install runtimes or modify the queue deadline. GQ has a distinct existing1 GiB production/assembly floor and3 GiB fitting floor; that historical scoped policy is not a precedent to transplant into these queue workers. This review runs no GQ work.

**Next decision:** approve/reject this exact PUM2-only calibration scope. If approved, prepare/review a new controller and receipt contract before its first launch. Conservation production, masked-native admission, all downstream3 GiB fitting guards and all scientific gates remain outside the exception. Results of a calibration may inform a later separately reviewed policy; they cannot retroactively certify a general lower floor or authorize other routes.

## Primary operating-system references

Microsoft distinguishes available physical memory from current-process commit capacity; system commit headroom uses `GetPerformanceInfo`, not a guessed amount of free pagefile space. [MEMORYSTATUSEX](https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/ns-sysinfoapi-memorystatusex), [PERFORMANCE_INFORMATION](https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-performance_information).

Windows job limits separately bound process/job committed memory; they do not guarantee resident-memory protection. [Extended job limits](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information). Child inheritance, nested-job compatibility and kill-on-close need explicit ownership checks. [Job objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects). CPU rate control is a separate cycle budget rather than a memory guarantee. [CPU rate control](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_cpu_rate_control_information).
