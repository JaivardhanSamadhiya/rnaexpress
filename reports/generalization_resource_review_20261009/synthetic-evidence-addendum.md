# Synthetic resource evidence addendum — 9 October 2026

Read together with `proposed-calibration.md`; the earlier document and static-review receipt remain unchanged. Status: **measured invented-case evidence only, not production admission or permission to replace a resource guard**.

Root ran46 selected invented-case tests of the fixed PUM2 implementation and independent numerical replay. The receipt reports PASS, elapsed0.40599999998812564 seconds, successful Windows process-memory query, peak working set25,038,848 bytes, and peak private commit16,732,160 bytes. Before the tests, total physical memory was16,805,040,128 bytes, available physical697,442,304 bytes and system commit headroom4,871,168,000 bytes; afterward available physical686,112,768 bytes and commit headroom4,868,599,808 bytes. Receipt timestamp2026-10-09T20:17:16.580455+00:00. These are observations of that short test process, not a new resource check for the queued producer.

The tests exercised invented140nt states and fixed358-byte public parameter files. No biological sequence, outcome, production worker or model was loaded; no existing RAM safeguard changed. This reviewer checked the completed receipt's scope fields and all four tested source digests against current bytes, without rerunning tests or importing the numerical helpers.

This is useful evidence that the selected scalar arithmetic can execute with a small footprint. It **does not cover** full6,293-row source-design parsing, all4,070 production sequences, the largest pinned input during whole-file hashing, one full background's retained dictionaries, JSON encoding/writing, completed-background resume validation or full numerical replay. It does not establish a peak bound for the two original full producer/replay functions, validate the proposed768 MiB process/896 MiB job ceilings, or validate a512 MiB free-physical admission floor.

The before/after samples happened to exceed the proposed512 MiB startup and1.875 GiB system-commit thresholds. They do not reserve memory for a future process, test100 ms monitoring, enforce a Windows job cap, or show that another app cannot consume the remaining physical headroom. The main proposal's transient-paging/UI-disruption and partial-output risks remain.

**Approval scope remains unchanged:** only the original fixed-PUM feature producer and independent numerical replay may be considered for a newly reviewed controller after explicit user authorization. Queue PID18748/caller3.5 GiB, conservation/native/downstream guards, scientific grids/IDs/parameters/tolerances and all old source bytes remain outside the exception. No implementation or guarded production execution was performed by this reviewer.

Source evidence: `results/generalization_resource_synthetic_profile_20261009/synthetic_profile_receipt.json`. The addendum receipt binds its actual SHA256, the unchanged main proposal/static receipt and the four source digests.
