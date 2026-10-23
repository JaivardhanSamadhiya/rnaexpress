# Source execution policy for the frozen V4 invented profile

V4 binds the initial committed manifest through worker launch and all outputs.
Root review verified all 113 pins and found one existing repository cache, the
parent `src/__init__.py` cache, absent from that source manifest. An additional
operational cache policy avoids loading any source cache rather than assuming
that `-B` disables cache reads. Frozen V1–V4 source and tests remain unchanged.

Both controller and its worker will inherit `PYTHONPYCACHEPREFIX` pointing to the
specified never-created path under V4 results, with `-S -B`. A separate invented
subprocess test proves that a deliberately stale normal cache returns 11 while
the absent-prefix process executes the current source and returns 22, reports
the exact prefix and bytecode writes disabled, and never creates that path.
This test opens only invented temporary files and runtime/source metadata.

The V4 source, scientific cases, numerical threads, native package inventory,
120-second lifetime and 768/896-MiB job limits stay fixed. Before launch and after
completion root checks that the cache prefix still does not exist and the exact
113 source pins/manifest are unchanged. The worker inherits the controller's
environment; none of its arguments ignore environment settings. This policy
does not admit biological data or change any scientific guard.
