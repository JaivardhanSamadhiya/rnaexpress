# Preserved pre-worker resource rejection

With the UTF-8 environment corrected, the second controller invocation stopped
at its fixed startup physical-memory floor. Its error was `Physical reserve
floor violated`; no job, worker log or case completion was created. The original
`native_attempt02_background.*.log` files remain preserved. This controller did
not save the rejected startup snapshot, so the precise available-byte count at
that moment is unknown.

Root makes a separate third launch after available RAM recovers, retaining the
same exact committed V4 source, initial-manifest binding, 512-MiB startup /
256-MiB active floors, 120-second lifetime, one thread, hard 768/896-MiB caps and
absent-cache-prefix policy. This is a manual startup attempt, without changing
or resuming any scientific case. The known-cell project-data floor remains
three GiB; this invented-only launch cannot override it.
