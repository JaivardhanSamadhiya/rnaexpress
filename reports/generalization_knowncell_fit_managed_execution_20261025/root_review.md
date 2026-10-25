# Root and independent source review before any additional execution

The initial draft passed 21 invented controller tests. Independent source
review found that it saved a PASS supervisor receipt before a final mandatory
journal fsync, allowing a logging failure to follow an immutable PASS. That
draft receipt and the three affected source snapshots are preserved in the
owned artifacts directory; they are not an executed or accepted fit.

The repaired draft completes the final journal event, disables fault handling
and closes both logs before `commit_receipt`. The latter hashes the closed
journal, rechecks birth/actual authorization/run/source identities, samples
final resources and the stage-total deadline, and exclusively saves its
receipt. No mandatory journal operation follows. A late deadline/reserve
failure produces a FAILED receipt. A final journal fsync/close failure cannot
reach final receipt creation. The new regression cases exercise the failed
terminal fsync and elapsed deadline after telemetry without any native job or
biological input. **23 controller, 8 runtime and 3 bridge tests pass.**

Independent read-only review of the repair found no remaining execution
blocker. It verified the full scientific `worker.fit` AST matches the preserved
attempt, unchanged input/pool/terminal/projection/calibration functions,
normalized runtime-provider AST parity, complete V3 bridge-function AST parity,
current-owner/source/input bindings, cleanup on telemetry exceptions and total
deadline propagation. It did not run tests, native calls, jobs or data reads.
Root ran the invented tests and source-only preparation separately.

The source generation includes the prior frozen retry generation, original
scientific dependencies, regular package parents, new runtime/bridge closures,
the actual interruption audit and proposed scope. No actual authorization,
request, source/input admission or attempt birth is created by preparation.
Actual execution remains contingent on a new explicit source-bound answer.

The user reports accidental drive disconnection and requests continued D: use.
This is permission to use that project location, not an inferred disk-repair
or additional scientific-attempt approval. Reconnection checks validate 543
prior source pins, all fixed admitted input/NPZ hashes, 69 preserved attempt
files and all 33 protected user files. Windows still reports Dirty / Full
Repair Needed; neither hash parity nor the toy diagnostic clears that warning.
All old failed/partial results, protected outcomes and scientific gates remain
unchanged. No spending, cloud, app closing or schedule is introduced.
