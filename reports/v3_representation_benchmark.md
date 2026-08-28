# RNAddress v3 representation benchmark

**Analysis class:** DEVELOPMENT

**Frozen protocol commits:** `ca5d826b6a695c7add147d9de83bd35ad0f254e4`, corrected before scoring at `d62aec29a00d1dfaf322e43ca8a05d0cbca004a2`

**Primary dataset:** 4,395 exact N-zip SNVs in 15 parent RNAs

## Decision

The prespecified representation benchmark selects **3UTRBERT 3-mer** for Candidates 1–4. Its frozen composite representation score was `0.482005`, compared with `0.447238` for SpliceBERT. The difference (`0.034767`) is far outside the `0.002` simplicity tie margin.

This result does not show that direct magnitude learning has succeeded. 3UTRBERT's contextual rank head was strong, but its direct magnitude and extreme heads were weak. Phase 3 therefore proceeds with 3UTRBERT as the contextual representation while retaining the requirement that the later stacked candidate materially improve regret and extreme recovery.

## Matched evaluation

Both representations received the same outcome-free 590-dimensional v2 edit block and the same downstream procedures:

* outer leave-one-parent-out evaluation;
* inner leave-one-training-parent-out tuning;
* training-fold `StandardScaler`;
* Ridge alpha factors `{0.1d, d, 10d}` for rank percentile and raw magnitude;
* balanced L2 logistic regression with `C={0.1,1,10}` for direction-specific training-parent top-10% extreme membership;
* frozen representation score `0.45 × rank percentile + 0.35 × (1 - magnitude regret) + 0.20 × extreme top-5`.

| Representation | Selection score | Rank percentile | Rank regret | Magnitude rank | Magnitude regret | Extreme rank | Extreme regret | Extreme top-5 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 3UTRBERT 3-mer | **0.482005** | **0.678263** | **0.390439** | 0.530753 | 0.494896 | **0.539270** | **0.461567** | 0/30 |
| SpliceBERT.1024nt | 0.447238 | 0.575857 | 0.433660 | **0.553408** | **0.462563** | 0.448558 | 0.518202 | 0/30 |

The SpliceBERT rank head recovered the exact oracle in its top five for 3/30 decisions, whereas 3UTRBERT's rank head did so for 1/30. This top-k result belongs to the rank head and is not the extreme-head term used in representation selection. Both explicit extreme heads recovered 0/30 exact oracles in the top five. The selected 3UTRBERT rank head nevertheless improved mean directional rank percentile by `0.102406` and rank-head normalized regret by `0.043221` relative to the matched SpliceBERT head.

The 3UTRBERT direct magnitude head selected only 2/30 near-oracle edits (`0.066667`) and recovered 1/30 oracles in its top five. The representation result therefore reinforces the Phase 2 diagnosis: a strong broad ranking representation does not automatically identify the most beneficial intervention.

## Tuning behavior

Inner tuning was active rather than degenerate. For 3UTRBERT, the rank head selected `d` for 9/15 outer folds and `10d` for 6/15. Its magnitude head selected `0.1d`, `d`, and `10d` in 4, 3, and 8 folds. Direction-specific logistic selections also used all three C values. Complete outer-fold selections are in `results/v3_phase3/representation_inner_selections.csv`.

## Representation provenance

3UTRBERT used the author-hosted `yangheng/3utrbert` checkpoint at immutable Hugging Face revision `220d80829deb077d1d640463a4267a96e9e70b1d`. The implementation used final-layer mutant-minus-parent CLS, global valid-3-mer mean, affected-3-mer, and fixed radius-10 local pools. Exact checkpoint, tokenizer, sequence, cache, and output hashes are recorded in the source manifest and representation manifest.

HydraRNA was not performance-tested. Its official extraction stack is incompatible with this Windows CPU-only host without substituting an unverified implementation, so its exclusion is technical and makes no claim about model quality.

## Implementation and numerical notes

The preregistered logistic model did not prescribe a numerical optimizer. A preliminary serial run showed that `liblinear` was impractically slow for the 3,662-feature matrix. A one-split timing check found `newton-cg` converged to the same fixed balanced L2 logistic objective in about 3.4 seconds, while `saga` exceeded 88 seconds and failed to converge at 500 iterations. The definitive benchmark therefore used `newton-cg`; labels, C grid, class weights, nesting, tolerance policy, and selection metric were unchanged.

During the definitive run, exact duplicate inner fits were identified: outer A/inner B and outer B/inner A train on the identical rows. The implementation was changed before completion to fit each unordered excluded-parent pair once, predict both excluded groups, and reuse the corresponding held-group predictions. Four bounded threads evaluated independent pairs. A unit test reconstructs every ordered prediction and requires exact equality. Previously observed Ridge tuning choices were reproduced exactly after the optimization.

These are computational/numerical implementation decisions, not changes to the frozen scientific search space.

## Integrity

* Astrocyte outcomes were not opened, inspected, analyzed, recorded or used. The inherited historical complete-worksheet programmatic load remains disclosed.
* The sealed Moffatt archive was not listed, opened, extracted or used.
* 3UTRBERT and all N-zip data are development resources; this benchmark is not external validation.
* Extreme labels and all tuning choices were constructed from training parents only.

## Machine-readable artifacts

* `results/v3_phase3/representation_outer_predictions.csv.gz`
* `results/v3_phase3/representation_parent_direction_metrics.csv`
* `results/v3_phase3/representation_comparison.csv`
* `results/v3_phase3/representation_inner_selections.csv`
* `results/v3_phase3/representation_selection.json`
* `results/v3_phase3/representation_manifest.json`

The next prespecified step is the five-candidate magnitude/mechanism comparison using 3UTRBERT as the selected contextual representation.
