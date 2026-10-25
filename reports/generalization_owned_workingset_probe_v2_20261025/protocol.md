# Toy feasibility test: retain tabs, limit only our child's resident pages

The user needs all current tabs open. The unused 4 GiB-startup study generation
therefore remains preserved, with no attempt birth. This probe explores an
additional physical working-set cap on our own suspended toy process. It does
not trim other applications, change the pagefile, kernel configuration, disk
health, global guards or any scientific data/solver/settings.

Microsoft documents that [SetProcessWorkingSetSizeEx](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-setprocessworkingsetsizeex)
can enforce a hard maximum for a process's resident working set. The existing
owned Job still enforces its unchanged 768 MiB private/process and 896 MiB job
commit caps, two active processes and kill-on-close. The proposed additional
cap is **190 MiB requested resident pages**, below the unchanged measured ceiling of192 MiB, preserving the child's original minimum
flags/value. It is set only after exact owned-Job membership is checked and
before resume, then read back exactly. An unsupported API/flag/readback is a
failure; no fallback or privilege escalation is permitted. This is an empirical
feasibility test, including compatibility with the existing Job hierarchy.

The toy child allocates a 384 MiB invented page-pattern buffer in bounded
chunks, verifies its full SHA-256 repeatedly and reads no project payload.
Native counters must demonstrate private commit above the resident cap while
the working set stays within it. Repeated page-ins can slow computation; no
full-study runtime or scientific numerical parity is certified by this test.

Startup remains at least 512 MiB available physical RAM and 1,920 MiB global
commit headroom, with live reserves of 256 MiB physical and 1 GiB global
commit/disk. The parent samples at 0.1 seconds and stops the owned job on any
violation or 150-second lifetime limit. One toy worker/thread, no retries,
spending or schedules. No actual FIT invocation/approval is consumed here.

The first probe installed the exact192MiB API cap, then stopped on a lifetime
working-set peak of201,334,784bytes: two pages above its201,326,592byte
request. It had committed280,633,344bytes of invented buffer/process memory
before termination; no full buffer hash or numerical claim passed. All evidence
remains preserved. V2 tightens the API request to190MiB and keeps the absolute
observed peak ceiling at192MiB. This is an operational guard band, not a change
to any scientific tolerance or the measured memory ceiling. Any new overshoot
above192MiB still fails. No global or other-application working set is changed.
