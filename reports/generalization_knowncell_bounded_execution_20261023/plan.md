# Proposed bounded execution of the fixed known-cell study

This is an operational proposal awaiting a separate, exact human approval.
No authorization file exists during preparation. No biological metadata,
numerical array, label vector or project model is opened to prepare it.
The 23 October original-floor metadata startup failure and all frozen source,
results and gates remain preserved.

The scientific objective is a controlled development comparison on represented
CAD and Neuro-2a cells with held genes. A pass cannot establish unseen-cell or
unseen-study transfer, a new modeling method, independent biological confirmation
or a transport mechanism. The fixed design still requires all 63 arm checkpoints,
84 optimizer units and both control comparisons. The PRELib binding experiment
remains a verified NO-GO under its declared gate.

## Why a separate approval is required

The frozen [known-cell protocol](../generalization_knowncell_joint_design_20261009/protocol.md)
requires fresh 3 GiB free physical RAM, 1 GiB workspace disk and one numerical
thread before imports, loads and fits. It explicitly says that the PUM-only
resource exception does not apply. The subsequent human PRELib exception was
also limited to its five named stages. Neither approval permits changing this
known-cell policy. Installed 16 GiB RAM does not imply 3 GiB currently available.

The proposed exception changes the resource policy only for these seven stages:
metadata admission/reconstruction, exact simple102 array admission, original
pandas label admission, prefit preparation, the fixed 63-checkpoint/84-unit fit,
independent checkpoint/source-selection replay, and complete outer evaluation.
No alternate model, feature set, dataset, replicate, tuning grid, cohort, tie
rule, effect orientation, split, tolerance, uncertainty method or success gate
is authorized by this operational exception.

## Exact proposed safeguards

| Constraint | Fixed proposed value |
|---|---|
| Free physical RAM before starting the owned stage | At least 512 MiB |
| Free physical RAM during the owned stage | Stop owned job below 256 MiB, sampled every 100 ms nominally |
| Worker private committed memory hard cap | 768 MiB |
| Entire owned job committed memory hard cap | 896 MiB |
| Free global system commit before startup | Job cap plus 1 GiB, 1,920 MiB total |
| Free global system commit during work | At least 1 GiB |
| Free workspace disk at startup and during work | At least 1 GiB |
| Scientific workers / numerical threads | One / one |
| Active processes in owned job | At most two, allowing one pinned direct-Git helper |
| Stage deadline | 30 minutes, no automatic retry or partial resume |
| Spending / cloud / scheduled tasks | None |

Polling is sampled protection, not an instantaneous physical-RAM guarantee.
The parent records minimum observed reserves and maximum monitor gap. Hard
Windows job caps apply independently of polling. The parent also consumes some
RAM outside the scientific job; system free-RAM and commit sampling includes it.
Paging or UI slowdown remains possible. The full-data memory peak is unknown.
The invented native compatibility profile peaked near 126 MiB; that is software
evidence and does not establish the real-data peak.

## Reviewable implementation and limits

The new controller uses the unchanged tested Windows job helper. The parent
assigns a suspended child to its exact job and verifies hard limits and
membership before resume. The child checks parent PID, immutable stage birth,
committed manifest/authorization and actual job membership. The child membership
query alone means membership in a job; exact ownership comes from the pinned
parent creation/resume code. Failure terminates the owned job, preserves partial
output and consumes the one stage opportunity.

The interpreter starts with `-S -B` and the shared, absent source-cache prefix.
Current executable/DLL bytes and all selected source/software evidence are
bound to the execution manifest. Actual scientific import origins must still
be checked by the separately frozen runtime provider at the relevant stages.
The current interpreter is not misrepresented as the old interpreter.
Full source-closure hashing runs at admission and completion boundaries, outside
the parent's resource-polling loop. It is not a continuous source-write monitor.
The parent polling loop performs only resource/process/job queries and records
sampling gaps; it cannot promise a precise real-time deadline on Windows.

A process-local context replaces exactly five named `require_resources`
bindings: the loader guard, array validator, engine adapter, arithmetic replay
and outer evaluation. The original pure admission function, original files and
all other workers remain unchanged. Each replacement validates the supplied
resource snapshot and immediately obtains a fresh actual native physical,
system-commit and disk snapshot. One-thread settings remain mandatory. The
context restores the exact original functions on exit, including failure, and
rejects nested/replaced bindings.

New calibrated outputs must explicitly set literal original-floor claims false
and bind the actual policy/manifest/authorization. Metadata rows, split/menu
contracts and their hashes stay exact. A later bridge that requires a literal
original-floor label flag must gain a separately reviewed, explicit calibrated
integration; it must not receive a false statement that the original floor ran.

Only the metadata entrypoint is implemented in this proposed controller.
Other stage names are refused here. Approval of the seven-stage resource scope
does not manufacture missing scientific input admissions or executable stage
controllers. Each later controller, source/runtime binding and required
predecessor evidence must be reviewed and frozen before its stage starts.
The resource adapter also refuses every nonmetadata stage without its fixed-path,
separately committed stage-controller admission: exact stage, current resource
manifest, controller source, declared source closure and independent review
hashes, bound into the same immutable attempt birth and child owner evidence.
No such nonmetadata admission exists now. Byte verification of a declared source
closure does not automatically prove arbitrary dynamic-import completeness;
that remains part of the independent source review.
Actual metadata must be independently reconstructed and committed before array
admission; the array and original-parser labels must be admitted before prefit;
an actual immutable FIT prefit must be committed before any fit. A new controller
cannot broaden the approved five-alias resource exception or scientific study.

The root will record the actual approval question, answer and item identifier
only after a human response, bound to the exact execution-manifest SHA. The
controller refuses to run without that separately committed authorization.
An invented unit-test approval dictionary is not a project authorization.

No protected outcomes, historical model reruns, frozen-artifact edits, package
installs, paid resources or automatic scheduling are admitted. A fit or gate
failure remains a failure. No positive result is promised.
