# One newly requested fresh fit with at least 4 GiB startup RAM

The prior managed attempt stopped on the 256 MiB physical reserve after 32
checkpoints/43 completed units. Its full failed receipt and journal, frozen
source, partial campaign and read-only audit remain preserved. No partial
model/score/configuration is used for tuning or resumed.

Root asked the user to close unused applications so at least 4 GiB would be
available for the full run, stating that the failed attempt would be preserved
and no automatic restart would occur. The user explicitly answered:
"Ok I removed stuff, try it now". This is one new human request to try the same
fixed study after freeing resources. It is not an automatic retry, the old
consumed approval, or a claim that this future source hash was in that answer.
The actual question/answer and authorization basis must be recorded verbatim.
No further permission is inferred beyond this one complete fresh attempt.

The new output namespace is `generalization_knowncell_fit_roomy_execution_20261025`.
The only resource-policy tightening is a **4 GiB available physical RAM** floor
before its attempt birth and again before child creation, retaining the same
parent/worker managed-session telemetry and terminal commit ordering. If that
floor is unavailable, do not create a birth or start a worker. All other caps,
live reserves, one worker/thread, 30-minute total limit and original resource
aliases remain unchanged: 768 MiB/process, 896 MiB/job, 1,920 MiB startup global
commit, 256 MiB live physical RAM, 1 GiB live commit/disk and two active processes
including Git. Higher startup RAM cannot guarantee that other apps stay stable.

All science and exact data/prefit/projection bindings remain fixed, including
the sampler, nine pools, 63 checkpoints, 84 units, optimizer options, controls,
source-only selections, split/purges, canonical scores, tolerances and gates.
No partial resume, automatic retry, spending, cloud, schedule or app closing.

Use D: as explicitly requested. Its existing Dirty / Full Repair Needed warning
remains recorded; no disk repair/dismount/formatting or warning-clearing is
authorized. Exact file hashes and resource gates remain mandatory. Only a
complete accepted campaign can enter the unused independent replay/evaluation.
