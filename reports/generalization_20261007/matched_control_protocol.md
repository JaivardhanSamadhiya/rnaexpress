# Additive matched control: postfit descriptive comparison

Written 7 October 2026 after the primary parallel route outputs existed, before
any fit in this diagnostic. This protocol is explicitly postfit and descriptive.
It does not revise the 45-file main prefit freeze, add a primary route, change
the gate, select a winning method, or create independent confirmation.

## Reason for the diagnostic

The primary scaling route selects among both candidate-normalized and
pair-normalized 246-column baselines. The ordered-motif and mechanism routes
select only among pair-normalized representations. Comparing each enriched
route with the primary scaling winner therefore mixes normalization choice
with the effect of its representation. A family-matched baseline is needed to
describe the incremental representation comparison correctly.

## Fixed reuse and selection

Use the exact admitted 26,258 rows, original 246 interaction_3 columns, historical
outcome-blind sampled pair roster, source/component/context loss weights,
training-only weighted pair RMS normalization, unsupported-column coefficient
zero rule, and signed-preference logistic utility objective. Reuse the existing
frozen `route_scaling.py` fitter and its three pair configs in their original
order: `pair_005`, `pair_05`, `pair_5`, with penalties 0.005, 0.05, 0.5.

For each outer held assay, read only the corresponding already-computed source
inner regret entries from `scaling/inner_selection.csv`. Each pair config must
have exactly one entry for each of the three source inner assays. Verify the
inner training ID hash, training row count, and validation row count against
the unchanged global component/exact-allele purging logic. Compute the equal
mean of those three source inner macro regrets. Choose the first config within
1e-12 of the minimum in the fixed original order. No outer assay outcome,
outer prediction, representation result, or mechanism result selects a config.

No inner model is fit again. Fit that one source-selected config on the outer
training pool and predict the excluded assay. This requires exactly four new
outer fits; partial checkpoints are immutable and resumable. No new grid,
feature, loss, seed, target transformation, direction flip, or gate is added.

## Freeze and execution

The `prepare` command requires complete scaling, representation, and mechanism
receipts. It creates `results/generalization_20261007/matched_control/input_manifest.json`
pinning this protocol, diagnostic code, original source dependencies, main
prefit manifest, baseline features, scaling inner results, and both enriched
routes' complete prediction/decision/summary files. Commit that manifest and
the new code/protocol before calling `run`. The runner verifies both the main
freeze and this separately committed additive manifest before fitting.

Use bundled Codex Python, UTF-8, no bytecode writes, and two BLAS/OMP threads:

```powershell
python -u -m src.generalization_20261007.matched_control prepare
# Commit the additive source, protocol, and input manifest before this command.
python -u -m src.generalization_20261007.matched_control run
```

Here `python` denotes the full bundled executable at
`C:/Users/jaisa/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`.
No fitting occurs during preparation or module import.

## Outputs and interpretation

Write only under the new `matched_control` result subdirectory. Preserve every
model/scaler, source-only inner selection, train/test IDs, candidate prediction,
selected decision, per-study summary, and model arithmetic replay error.

Before comparison, require identical dataset/intervention prediction rosters
and identical dataset/component/context/direction decision keys, candidate
counts, and feasibility status for each enriched route. Report per-study and
equal-study differences in regret and avoidable error relative to this matched
pair-only baseline. Preserve all unfavorable comparisons. These are descriptive
representation-family comparisons; they are not new prospective primary tests
and cannot rescue a failed frozen generalization gate. Existing historical and
primary generation outputs remain unchanged.
