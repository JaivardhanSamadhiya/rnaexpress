# Bounded managed-session toy diagnostic after drive reconnection

One scientific-data-free toy child runs for 360 seconds, within an unchanged
owned Windows Job (768 MiB/process, 896 MiB/job, at most two processes). It starts
with 512 MiB physical RAM, 1,920 MiB commit headroom and 1 GiB disk reserve;
live reserves are 256 MiB physical and 1 GiB commit/disk. The parent enforces
the fixed 420-second diagnostic deadline. Numerical thread settings are one.
No scientific resource guard is modified by this diagnostic.

Source/log paths differ from the failed first probe. Parent and child flush
and fsync JSONL progress each second. The managed command session is retained
and polled. If progress recording fails, a C: fallback is attempted and owned
job termination occurs in finally even if error recording also fails. No study
data, pools, fitted model or optimizer is accessed. A successful probe does not
clear filesystem warnings, establish the earlier failure's cause or consume a
scientific fit approval. Root's exact metric/hash receipt is in results.
