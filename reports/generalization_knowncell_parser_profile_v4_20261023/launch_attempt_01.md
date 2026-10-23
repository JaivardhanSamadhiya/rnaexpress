# Preserved launcher environment error

The first root launch exited in the controller's environment check, before a
Windows job, worker, scientific import or invented case started. The root shell
set the numerical-thread and bytecode variables but omitted the required
`PYTHONUTF8=1`. The controller correctly rejected that environment. Its original
stdout/stderr logs are retained as `native_background.*.log`.

A separate explicit root launch uses `native_attempt02_background.*.log`, with
the missing variable restored. Frozen source, manifest, scientific cases,
resource limits and source-cache policy remain unchanged. No worker output is
overwritten and no failed scientific stage is resumed. This is a corrected
launcher invocation, not an automatic retry or biological result.
