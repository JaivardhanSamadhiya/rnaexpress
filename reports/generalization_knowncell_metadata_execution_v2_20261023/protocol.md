# Prospective metadata V2: source and creation-identity corrections

V1 was not executed. Its review found an unpinned parent initializer and a live
manifest hash that could be redefined during completion. A separate review
identified the existing-bytecode-cache gap and a possibly missed final memory
peak. All 61 V1 pins, its admission and test receipts remain unchanged. An earlier
pre-freeze preparation failed on a nonexistent namespace-package initializer;
it stopped before creating the admission or execution manifest. That draft
receipt is preserved without describing it as a successful source freeze.

V2 pins the actual `src/__init__.py`, captures the exact manifest bytes compared
with Git, carries their initial SHA as a required worker argument and requires
that same SHA before project loading, outputs and completion. It never replaces
the expected identity with a fresh live hash. Both controller and worker require
`-S -B -X pycache_prefix=<the exact V2 never-created results path>`. The path must
remain absent. A separate invented subprocess experiment demonstrated stale
normal cache use versus current-source execution under this policy. Neither
process creates a cache. Final lifetime memory peaks are queried while the
worker process handle remains open.

The existing metadata admission and selective loader are reused unchanged. Only
the ten Mikl metadata fields, exact menus, splits and contradictions are admitted.
No numerical labels, feature array, other study, scientific package or fit is
admitted. CORE tokens are traversed, including unused effect tokens, without
converting or retaining effects. All original per-read and continuous floors are
three GiB free physical RAM, one GiB workspace disk and one numerical thread.
System commit reserve is one GiB; the owned job caps remain 768 MiB per process,
896 MiB total and two active processes for worker plus pinned Git. The deadline
is five minutes. PUM/PRELib exceptions do not apply.

Review and commit exact V2 bytes before an explicit root start. A startup floor
failure writes an exclusive blocked receipt without starting a worker or opening
a project payload. Partial and failed outputs remain preserved; no automatic
retry or resume exists. A successful metadata bundle still requires independent
reconstruction and a commit before separate numerical array/label admission.

The source corrections were begun by a separate agent. Account usage limits
interrupted it; root finished the tests, preparation and review. This is not a
claim of an additional independent-agent review of final V2 bytes.
