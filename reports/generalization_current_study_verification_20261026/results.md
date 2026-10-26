# Completed known-cell study: NO-GO

The fixed joint model did not meet its original benefit criteria. The complete
execution, numerical replay and evaluation closed successfully. This result
tests the frozen 102-feature linear ranking study on held genes in represented
CAD and Neuro-2a cells. It does not test all predictors or demonstrate that RNA
localization is intrinsically unpredictable.

## Primary result

Lower normalized selection regret is better; the uniform reference is 0.5.
Equal cell/component/context/direction weights are unchanged.

| Frozen arm | Macro regret | CAD | Neuro-2a |
|---|---:|---:|---:|
| Pooled control | 0.5027738054 | 0.4914674289 | 0.5140801818 |
| Independent control | 0.5068243315 | 0.5157451926 | 0.4979034704 |
| Joint shrinkage 10, primary | 0.5005789239 | 0.4939904253 | 0.5071674226 |

| Joint improvement over control | Pooled | Independent |
|---|---:|---:|
| Macro gain | 0.0021948814 | 0.0062454076 |
| CAD gain | -0.0025229964 | 0.0217547673 |
| Neuro-2a gain | 0.0069127593 | -0.0092639522 |
| Shared component-bootstrap 95% interval | [-0.0132321087, 0.0171055349] | [-0.0116635210, 0.0237228794] |
| Gain after removing best fold | -0.0044190378 | -0.0048249914 |
| Macro increase in wrong-direction harm | -0.0062727261 | 0.0025639959 |

Ten of fourteen original primary checks fail: absolute macro regret, both-cell
performance below 0.5, and all four benefit conditions against each control
(macro gain, both-cell gain, positive bootstrap lower endpoint, and positive
gain after best-fold removal). All four harm checks pass. Passing harm limits
does not establish benefit. Neither small positive macro gain has an interval
excluding zero. The cells disagree about which control is improved upon.

All 13,781 rows occur exactly once per arm across nine outer records. Primary
analysis has 9,632 directional decisions in 187 components; unmatched candidates
remain in the secondary coverage rather than being silently dropped. The
original 5,000 shared exponential bootstrap draws, seed 20261007, score/ID ties,
source-only selections, gates and folds were retained. Secondary outcomes do
not replace the failed primary.

## What was verified

The approved corrected prefit and single fresh FIT were executed exactly once.
The FIT produced all 63 checkpoints, 84 optimizer units and 191 campaign files,
including genuine campaign, worker and supervisor closure. This new completed
study has new current-runtime provenance. Historical interrupted campaigns and
their missing completion records remain unchanged.

The subsequent separately owned read-only replay verified all 63 checkpoints
and nine source-only selections. Maximum differences were 3.553e-14 for scaling,
3.331e-16 for objective, 7.516e-17 for recorded gradient norm and 7.105e-15 for
scalar scores; canonical scores matched exactly. Replay and evaluation exposed
no optimizer callable and performed no refits. Evaluation retained the original
mathematical body and thresholds. This is numerical verification of the same
study, not independent biological replication.

| Closed stage | Elapsed seconds |
|---|---:|
| Corrected prefit | 70.563 |
| Fresh fixed FIT | 494.734 |
| Complete numerical replay | 501.734 |
| Fixed evaluation | 19.954 |

The replay peaked at 563.7 MiB private memory and evaluation at 239.6 MiB.
Both closed below the approved process/Job/resident limits with zero owned
active processes in final native accounting. Evaluation's parent independently
recomputed the gate booleans. The root then rehashed closed reports, receipts,
telemetry, runtime proofs and all 364 pinned verification source/static files,
and verified preservation of the 33 pre-existing user modifications.

## Post-gate diagnosis: limited, exposed evidence

All 63 saved optimizations reported success. Their penalized training objectives
improved over the zero-vector objective log(2); the smallest improvement was
0.01316 and maximum recorded absolute gradient norm was 2.471e-6. Together with
the independent arithmetic replay, this argues against a trivial unfitted or
corrupted-model explanation. It does not identify a unique biological cause,
prove the fitted optimum is useful, or turn penalized training objectives into
generalization evidence.

A deliberately restricted post-hoc check picks one globally fixed existing arm
per cell: pooled for CAD and independent for Neuro-2a. Even this selection has
macro regret 0.4946854496, above the original 0.48 absolute criterion. This only
bounds that restricted choice among the three already fitted arms. It is not a
bound on per-gene selectors, new representations, new models, other assays or
biology. It is not a new primary result or prospective selector.

The diagnostic opened only already saved model/optimizer summaries and the
exposed evaluation. It made zero new optimizer calls and did not reopen original
biological feature or label inputs.

## Research implication and next work

More runtime repair or another identical fit cannot supply the missing positive
evidence. The next development hypothesis must explain what biological or
sequence context the existing representation loses, be distinct from the
already failed uncertainty-supervision and shared-shrinkage hypotheses, and
have a fixed falsifiable test. These folds are now exposed development data.
No selection on them can create a fresh confirmatory benchmark.

The separate primary-source novelty review is
`reports/generalization_literature_recheck_20261026/novelty_boundary.md`.
Localization prediction and shared-plus-task-deviation learning have prior art.
The precise edit-decision task still needs comparison with prior evaluation
units. Novelty, unseen-cell transfer, causal mechanism and independent
confirmation remain unestablished.

## Evidence anchors

- Completed producer FIT commit: `c76ace84b752e2601e68563ef66b8d8a7b64a880`.
- Accepted replay commit: `04e82b8b17e4ed6d41ff272b89217d139e618d8e`.
- Verification source manifest: `0656490251eb928609cf3b7f531d4bb0c8fd75937ced63db531eeb851dec3f2b`.
- Evaluation report SHA-256: `be53e8c02be6ae444ec67bd231532571bd97d00a4c92b4f52bc8ec15969f462a`.
- Evaluation supervisor SHA-256: `5d1f36bab81e39e03de62409c4fad56d68191b4995816d074b92f6f28d4a7ac8`.
- Saved-record closeout SHA-256: `0f571a2fe269a86b4d6a0d66caa20bb0bd5766d9d57ff40669a09dbd5f0f062a`.

Raw evidence is under
`results/generalization_current_study_verification_20261026/`.
No FIT/retry/resume remains authorized by the consumed single-attempt scope.
No protected outcomes, CORE reconstruction, old freezes, original user changes,
drive repair, paid resource or scheduled task was used for this closeout.
