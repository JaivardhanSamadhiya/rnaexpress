# Owned paging feasibility: PASS on invented bytes only

One V2 native diagnostic completed successfully in 12.109 seconds. The owned
worker allocated and touched 384 MiB of invented page-pattern buffers and
verified three complete identical hashes against independently constructed
expected bytes. Peak private commit was 415,207,424 bytes (395.97 MiB); lifetime
resident peak was 199,237,632 bytes (190.008 MiB), below the fixed 192 MiB
measured ceiling. The requested API maximum was 190 MiB. Exact readback and
unchanged original Job limits were checked repeatedly across 118 samples.

Minimum sampled free physical RAM was 2,146,377,728 bytes. The closed parent
journal SHA-256 is 9499d4fdafa172beefd3e37dd64d86b999d034866f1863c03246fdff6f3cfba2.
The terminal receipt reports PASS_OWNED_PAGING_TOY_ONLY. No biological payload,
optimizer or scientific attempt was used. This pass is a memory-control
feasibility result; it establishes no numerical or biological result.

The first probe's exact 192 MiB request was installed successfully but its
lifetime peak overshot that value by 8 KiB. That failure and its raw logs remain
preserved in the original namespace. V2 reduced the requested cap to 190 MiB
while retaining the same 192 MiB measured ceiling. No other application,
browser tab, pagefile or global memory policy was changed.
