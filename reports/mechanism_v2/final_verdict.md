# Mechanism-v2 final development verdict

Generated from the committed outer freeze at `04155604d201`. Gate thresholds: `a57dd77f6b13`.

## Verdict

**NO-GO - END UNIVERSAL ZERO-SHOT RNADDRESS**

At least one pre-registered development gate did not pass, so universal zero-shot intervention selection is not supported. A post-hoc restricted domain is forbidden by the frozen protocol, so PARTIAL GO is unavailable unless the single prospectively named restricted domain passes every gate on its own, which it does not when the shared gates fail.

## Pre-registered gate outcomes

| gate | status |
| --- | --- |
| g10_hard_harm | fail |
| g1_useful_selection | pass |
| g2_distributed_benefit | fail |
| g3_matched_edits | pass |
| g4_leave_source | fail |
| g5_cross_context | fail |
| g6_small_edits | pass |
| g7_mechanistic_necessity | fail |
| g8_shortcut_resistance | pass |
| g9_stability_and_integrity | fail |

## Boundaries preserved

* FinalShot: NO-GO - END ZERO-SHOT RNADDRESS (commit 98ffc02, unchanged).
* Astrocyte holdout: sealed; the pre-holdout freeze conditions are not satisfied. No Astrocyte sequence, label, outcome, feature row or metric was loaded at any point in this evaluation.
* N-zip outcomes and quarantined TDP EV5 stability data were never accessed.
* N10 is not applicable: independent stability admission failed and the block is absent, not zero-filled.

## Evidence provenance

```json
{
  "results/mechanism_v2/outer/development_evidence.json": "c16a9c1a939bb398d85486ed891c5847b38014401e8a555f29e76553886b5a0c",
  "results/mechanism_v2/controls/control_evidence.json": "7beec2785f4dc8da1ec7245d5544311c4dc30890d5ad8a8a514d79b7a5bca52d",
  "results/mechanism_v2/controls/seed_replication.json": "096ca3fcdf251c8e59222aa99e98f50b3cdf8e3d2f458b5ac995b145ca8856bc",
  "results/mechanism_v2/transfer/transfer_evidence.json": "0518db6a9f0e884826f7241a309658b85705b78d8a2308769f60b6bd8c7c4c36",
  "results/mechanism_v2/outer/shortcut_probes.json": "f2b45734288c8eb272cf8fe62a5f30ffa0ad5532d780128491f0db48c46925b3",
  "results/mechanism_v2/outer/uncertainty.json": "240fed6b5821dc76807ad467b1322b0d50a609668c12349f8f47bda046f2192c"
}
```

## Honest scope

* these development datasets have been examined repeatedly in earlier RNAddress experiments; nested estimates on a reused benchmark are not fresh independent confirmation
* Predictive necessity tests do not establish that any RBP mediates localization.
* A negative development result is a valid scientific outcome and is reported as such.
