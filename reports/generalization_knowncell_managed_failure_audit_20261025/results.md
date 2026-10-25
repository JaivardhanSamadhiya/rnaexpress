# Managed fit preserved after a measured physical-RAM reserve stop

The actually approved managed attempt started with 2,393,776,128 available
physical bytes. It stopped after 490.234 seconds total because available RAM
fell below the approved 256 MiB live reserve. Minimum sampled physical RAM
was 139,681,792 bytes (133.21 MiB). The worker/job peak was 536,682,496 bytes
(511.82 MiB), below both hard caps. Global commit headroom stayed above 6 GiB.
The reserved stop is a system-wide availability condition; it is not evidence
of an optimizer error or the worker exceeding its cap. No historical process
inventory establishes which other process or kernel/cache usage caused the
remaining physical-memory demand. A later process snapshot cannot prove that.

The parent recorded 4,776 monitor samples, at most 0.203 seconds apart. It
terminated the owned job, observed zero active owned processes and wrote a
FAILED receipt only after closing/hashing its mandatory journal. This time
there is a complete operational failure receipt and no unexplained process
disappearance. No worker completion/full campaign/replay/evaluation exists.

Root's read-only saved-declaration audit passes for **32 checkpoints: 28 inner,
4 outer, 43 recorded completed optimizer units**. The 32 runtime proofs match
the same source/run/birth. There is no subsequent partial checkpoint file.
The exact frozen roster prefix, original saved model/prediction schemas,
hashes, source-pool bindings, actual approval and final failed journal/receipt
are checked. No coefficient, score, selected configuration or performance is
used for tuning. All 33 protected user files remain intact.

The first audit adapter expected detached-launch log filenames inherited from
the prior attempt. Managed sessions capture those streams externally. That
read-only audit stopped before producing a receipt; the log-name expectation
was corrected to the actual worker/fault/progress files, then the audit passed.
No scientific file or failed-attempt evidence was changed by that correction.

The actual one-attempt approval is consumed; no automatic retry or partial
resume follows. The user then answered the explicit request to free at least
4 GiB with "Ok I removed stuff, try it now". Root treats that as one new explicit
attempt authorization in context, with the stricter 4 GiB startup floor, all
other caps/live reserves/science unchanged and a new namespace. This is not
a claim that the user approved a new source hash before it existed. The actual
answer/context and subsequent reviewed freeze must be preserved honestly.
The immediate recheck had about 2 GiB available, so no new attempt started.
