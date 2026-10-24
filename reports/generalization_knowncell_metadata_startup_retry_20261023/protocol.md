# One explicit metadata startup opportunity

This additive controller may be started once by root after review and commit of
its exact execution manifest. It preserves the V2 startup-blocked receipt
`071e5c006c5af60b752e249964b766596f271fa9aa6e296dc101ad003d3ac89a`
and all75 V2 pins. That original attempt started no worker and opened no project
payload. This is an operational retry authorized separately by root; it does
not change the scientific metadata admission or any existing resource guard.

Both addon and original V2 manifests must be exact bytes in HEAD. Their initial
SHA values are captured once and reused through completion. The new exclusive
`attempt_birth.json` consumes this opportunity even if startup blocks again.
Any pre-existing worker log, worker completion, admitted bundle, new attempt
birth or new supervisor receipt rejects the run. Existing/partial files are
preserved; there is no resume, worker retry, cleanup or output replacement.

The unchanged original V2 worker command receives the original execution SHA
`dccab5219dcc6a82e015a31e248748cef160ee2e0408105ddfd8e2a0c86e35f7`.
Controller and worker use the exact original V2 absent cache prefix with
`-S -B -X pycache_prefix=...`. No module globals, loader/resource callbacks,
admission, output bundle or worker-completion path are patched. Only the new
supervisor receipt and attempt birth are written in this new namespace.

An explicit optional integer wait of0–60 seconds samples resource readiness
before the first and only spawn. Default is0. It opens no project payload and
imports no scientific package. It is not a repeated worker launch. A fresh
original three-GiB physical / one-GiB disk / one-GiB commit-reserve check is
required after Job setup immediately before spawn. The unchanged per-read and
continuous worker floors remain active. The original owned Job caps stay
768MiB per process /896MiB total / two active processes, including pinned Git;
all four numerical thread variables must be1. The300-second metadata-stage
deadline begins after the separately bounded readiness wait. Original monitor
and final live-process-handle peak queries are reused unchanged. Provenance
hashes are computed before the final metadata-stage resource/deadline check.

New receipts bind their initial addon SHA, initial V2 SHA, preserved first
blocked-receipt SHA and exclusive attempt-birth SHA. Success means only that
the original selective metadata worker completed; independent reconstruction,
full-menu checks and a later commit remain required. No array, converted
numerical outcome, native scientific import or model fitting is admitted here.
The source-only tests use invented temporary paths and mocked Jobs and never
open actual metadata inputs or run a native process.
