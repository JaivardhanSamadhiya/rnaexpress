# Independent review of the exact uniform-risk reference

24 September 2026. AI-authored technical verification of completed anonymous
exports, not a new experiment or student submission prose. No source sequences,
candidate-level outcomes, protected files or external resources were opened.
No experiment, model fit, candidate reconstruction or choice selection was rerun.
No file was committed by this review.

## Scope and result

The review used only `srle_uniform_risk_result_20260924.json`, its anonymous
`groups` and `pairs` CSVs, and the earlier anonymous fixed-choice risk `groups`
and `pairs` CSVs, all under `results/research_20260921`.

**PASS:** all 190 point estimates and 380 interval endpoints were independently
recomputed, for 570 numerical comparisons. This covers every uniform-reference
summary and every model-minus-uniform summary for all four policies, both
directions, both constituent replicates and paired-replicate metrics.

The largest absolute discrepancy was **1.1102230246251565e-16**, within the fixed
1e-12 tolerance. One entry attaining this discrepancy was the uniform-reference
negative-change fraction for the decrease direction in replicate 1: independent
estimate 0.5054543560734532 versus reported estimate 0.5054543560734533.

The bundled Python imported `common` before NumPy. NumPy 1.26.4 was used only to
recreate `default_rng(20260921)` indices with shape (2000, 60). All aggregation
used independent standard-library `math.fsum` means and an explicit sorted-value
linear-interpolation quantile implementation. Identical bootstrap indices were
used for reference summaries and paired model-minus-reference class differences.

## Structural and mathematical checks

- The uniform exports have 240 per-replicate class rows and 120 paired-class
  rows; the earlier policy exports have 960 and 480 rows. All keys are unique
  and cover their complete expected combinations.
- Sixty class IDs occur. Parent counts match across all directions, replicates
  and models, and sum to 592. Every class has positive representation.
- Both new export hashes match the completed result JSON. Both earlier export
  hashes match those recorded in the preceding independent review.
- Sign-category fractions sum to one and lie in [0, 1]. Thresholded benefit and
  wrong-direction fractions do not exceed their corresponding sign fractions;
  mean losses are nonnegative.
- Paired positive/negative fractions obey both the lower and upper Frechet
  bounds from their replicate margins. The paired-minimum mean does not exceed
  either individual-replicate mean.
- Uniform direction reversal negates mean change, swaps positive/negative and
  benefit/harm threshold fractions, and preserves tie fractions. Its mean-loss
  difference has the expected relation to directed mean change.
- For paired uniform metrics, reversal swaps positive-both and negative-both,
  while preserving disagreement and tie-involving fractions. The sum of the
  two direction-specific paired-minimum means is nonpositive.

The exact input hashes, all independently recomputed summaries and verification
metadata are saved in
`results/research_20260921/srle_uniform_risk_independent_verification_20260924.json`.

## Interpretation check

Uniform candidate choice has class-weighted positive-in-both-replicates fractions
of 36.27% for decrease requests and 39.21% for increase requests. The reference
is therefore not a 25% independent-sign chance model.

The position-pair policy exceeds those exact uniform expectations by 14.69 and
17.78 percentage points, respectively, with descriptive paired intervals
[11.25, 18.08] and [14.08, 21.57] percentage points. Ordinary short-motif policy
contrasts are also positive: 14.67 and 15.26 percentage points, with intervals
[11.53, 17.90] and [10.81, 19.78]. These comparisons address the missing random
choice reference; they do not establish superiority of the pair policy over
the short-motif policy.

All rates and contrasts weight composition classes equally, after averaging
within class; they are not unweighted percentages of all parents. Differences
are always model minus uniform. Negative differences in wrong-direction rate
or mean loss favor the model; positive differences in benefit rate or directed
mean favor the model. Wrong-direction score movement is not biological harm
or toxicity, and NRS is not a cellular RNA percentage.

The reference averages over the same measured candidate identity in both
replicates. It still forces a swap and provides no comparison against choosing
to leave the parent unchanged. The paired minimum is a descriptive observed
minimum, not a confidence bound or future-performance guarantee. Intervals
remain conditional on previously fitted models, fixed choices and a shared
experimental source; no biological independence or new confirmation is implied.

This aggregate review cannot independently establish the candidate roster,
original identity matching or the Table 5 production chain. Those require the
separate frozen reconstruction and provenance evidence. It verifies exported
arithmetic and internal consistency only, and changes no gate or closed outcome.
