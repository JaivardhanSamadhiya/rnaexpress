# Proposed roomy fresh fixed fit: operational changes only

This is a separate additive source generation after the managed attempt's
32-checkpoint RAM-reserve stop. The first attempt's explicit RAM-reserve stop
and the second attempt's unexplained process disappearance
remain preserved. No partial campaign is repaired, resumed or used for tuning.
No actual authorization, runtime request, run admission, static input binding
or attempt birth is supplied by this source preparation.

The unchanged scientific fit function delegates the original sampler, adapter,
runner, optimizer and lifecycle writer. Exact input bytes, nine source pools,
63 checkpoints, 84 units, arms, configurations, splits, purges, canonical score,
selection rules, tolerances and gate remain fixed. The new V6 bridge changes
only the immutable static-binding path; its full scientific function must be
AST-identical to V3. The original prefit/projection admission is unchanged.

Operational differences from the consumed fresh attempt:

- Root must launch the supervisor directly in a managed command session and
  retain/poll its returned session identifier, without Start-Process detachment.
- An exclusive 8 MiB bounded JSONL journal records the durable birth, child
  assignment/resume, sampled memory/job counters/exit status at most once per
  second except terminal samples, monitor return and intent to commit.
  Each recorded line is flushed and fsynced. A write failure is fatal.
  The final journal event and all log closes precede the final identity,
  resource and total-deadline checks and exclusive supervisor receipt. The
  receipt binds the closed journal's hash. No mandatory journal operation
  follows receipt creation; a failed final fsync cannot leave a PASS receipt.
- Supervisor/worker enable Python fault handling in distinct preserved logs;
  the worker logs its PID at entry. Hard external termination may still prevent
  a final receipt; the journal is evidence, not guaranteed crash recovery.
  Only the JSONL journal has the explicit byte cap; fault logs have no separate
  byte cap and are limited to the one process invocation and failure output.
- The monitor uses the original stage start, including setup, for the same
  1,800-second limit. It cannot restart the deadline at child launch.
- Startup still requires 4 GiB available physical RAM. All approved process/job
  caps, physical/commit/disk reserves, one worker/thread and original scientific
  resource aliases remain unchanged.

The user explicitly requested a new try after the 4 GiB memory-freeing question.
The actual answer and context are recorded under this reviewed source freeze,
tied to the saved managed-failure audit; no claim is made that the user approved
this future hash in advance. This grants one from-zero attempt only. No old
consumed answer or automatic retry is used. No spending, schedules or app closing.

Tests use invented dependencies and temporary logs only. Preparation rehashes
the original/native source closures without scientific package imports,
project payload reads, pool creation or fits. A separate toy managed process
tests launch lifetime without study data; it is not proof of full-fit success
or an explanation of the historical interruption.
