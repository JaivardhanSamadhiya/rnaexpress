# Direction-specific SRLE audit — 24 September 2026

AI-authored technical evidence record, not student submission prose. No new
sequence choice, model fit, source outcome or biological experiment was created.
The audit was specified and committed at f9219b1 before its diagnostic execution,
but uses previously examined outcomes and is explicitly post hoc.

## 1. Project goal

Determine what can defensibly be claimed about computational choices among
already-measured RNA-localization alternatives. The useful candidate contribution
is a composition-controlled decision benchmark with reproducibility, simple
comparators and explicit failure rates. A new mechanism, generally reliable
selector or completely novel biological result has not been established.

## 2. Complete versus in progress

### New diagnostic result

The methods review identified that the earlier mean of upward and downward
parent-relative changes cancels the parent score algebraically. A positive
bidirectional average alone therefore cannot show improvement over the parent
in each direction. The new diagnostic separates the directions while preserving
every original choice, model, cohort and replicate.

Both direction-specific mean changes are positive for the pair model and the
ordinary short-motif model in both constituent replicates. Their descriptive
intervals exclude zero. However, many individual decisions move the measured
score away from the requested direction.

| Model | Requested direction | Mean directed NRS change, replicate 1 / 2 | Wrong-direction rate, replicate 1 / 2 | Better in both replicates | Worse in both replicates |
| --- | --- | ---: | ---: | ---: | ---: |
| Composition tie choice | Decrease | -0.03123 / -0.03898 | 56.42% / 55.50% | 32.42% | 44.34% |
| Composition tie choice | Increase | 0.03123 / 0.03898 | 43.58% / 44.50% | 44.34% | 32.42% |
| Position additive | Decrease | 0.07192 / 0.05852 | 40.76% / 45.78% | 43.56% | 30.10% |
| Position additive | Increase | 0.04403 / 0.05106 | 41.86% / 42.27% | 47.17% | 31.30% |
| Short motifs | Decrease | 0.12617 / 0.11045 | 34.97% / 39.21% | 50.94% | 25.13% |
| Short motifs | Increase | 0.10607 / 0.10922 | 33.92% / 33.72% | 54.47% | 22.11% |
| Position pairs | Decrease | 0.13154 / 0.12426 | 33.54% / 36.28% | 50.96% | 20.78% |
| Position pairs | Increase | 0.09990 / 0.11498 | 33.96% / 32.63% | 56.98% | 23.57% |

All percentages are **equal-composition-class averages of within-class decision
fractions**, not unweighted percentages of the 592 parents. There are 60 classes;
neighborhoods overlap. "Worse" means movement of the assay score away from the
requested direction, not biological toxicity or an adverse cellular phenotype.
NRS is a log2 normalized abundance-ratio score, not a cellular RNA percentage.

For the pair model, the fraction better in both replicates has intervals
[45.08%, 56.87%] for decrease requests and [51.47%, 62.42%] for increase requests.
The corresponding fractions worse in both have intervals [16.22%, 25.61%] and
[19.25%, 28.41%]. Opposite signs across replicates account for 28.26% and 19.45%.
There are no numerical ties at the fixed 1e-12 tolerance.

At the fixed descriptive scale of 0.1 log2-score units, pair-model wrong-direction
changes occur at rates of 22.22% / 19.65% for decrease requests and 23.92% / 22.38%
for increase requests in replicates 1 / 2. The 0.1 value is not a validated
biological-importance threshold or a new gate. Every model's complete estimates
and intervals are retained in srle_fixed_choice_risk_result_20260924.json.

The class-weighted mean of the smaller observed change across the two replicates
is 0.03678 [0.00250, 0.07823] for decreasing NRS, and 0.01297
[-0.03851, 0.05661] for increasing it. This is a descriptive two-replicate minimum,
not a lower confidence bound or guarantee for a future experiment. No favorable
subset, threshold, abstention rule or additional model was selected from it.

The sixteen direction-specific means recombine to the eight archived symmetric means
within 2.78e-17. The prior positive was not purely a direction-averaging artifact,
but it cannot be presented as reliable improvement for every parent. Pair-model
superiority over short motifs remains unestablished by the original comparison.

### Independent verification and provenance

An independent implementation reproduced 152 statistics and 304 interval endpoints
from the anonymous class exports, maximum difference 3.33e-16. It checked cohort
balance, sign partitions and paired bounds. This validates exported arithmetic,
not the biological independence of the experiments. The model training aggregate
already incorporated these constituent measurements.

The methods review found no direct held-out-label leakage into the reviewed
composition means, scaler or Ridge fits. It did identify limits: exact-sequence
holdout within shared neighborhoods, a restricted test-only candidate set,
outcome-dependent nonzero-range eligibility, complete-coverage filtering, no
unchanged-parent option, conditional uncertainty and an incomplete historical
raw-swap dependency freeze. These remain explicit; no original file was rewritten.

The author-linked public repository README, configuration, license and four
upstream source files were downloaded as pinned Git blobs into the authorized
project folder. Each receipt records official URL, size, SHA-256 and verified
Git blob ID. They are freely accessible, and the included repository license is
MIT. Source identity does not prove measurement correctness. No downloaded code
was executed. No new dataset discovery or outcome download was attempted.

The exact Table 5 production route remains unresolved. The paper's NRS definition
and three-replicate DESeq2 description do not specify how the single table score
was exported. Inspected documentation and counting code disagree on several
normalization, QC and naming details. These observations do not prove the workbook
was produced by that code or that published measurements are wrong. See
srle_measurement_provenance_review_20260924.md for scope and source hashes.

The unsent srle_provenance_questions_20260924.md contains the concrete computational
questions that would help resolve the chain. No message was sent; author contact
would require the user's explicit instruction. No wet-lab request or purchase is
included.

### What each new module does

- srle_fixed_choice_risk.py verifies the committed diagnostic freeze, checks
  fixed-choice pairing and balanced cohorts, then computes direction-specific
  summaries and paired-replicate consistency with common composition bootstraps.
- test_srle_fixed_choice_risk.py tests sign/tie semantics, replicate disagreement,
  immutable choice identity, missing replicates and equal-class weighting.
- srle_risk_figure.py plots only the completed summaries. The PNG and SVG were
  visually checked; intervals remain in the full result rather than the stacked
  point-estimate chart.

The diagnostic does not load the source workbook or raw reads. Outputs contain
anonymous class IDs and metrics, not recommended sequences. All four models and
both directions are retained. verification_20260924_srle_risk.json records 60
passing scoped tests, 228 unchanged original snapshot files and 15 verified
experiment freezes. All seven downloaded source files (49,986 bytes total) passed
size, SHA-256 and Git blob identity checks. No unfiltered pytest ran.
The old preservation mismatch at analyze_finalshot_grouped_gates.py remains
unmodified. Work stays on main; unrelated user changes stay outside these commits.

## 3. Next three tasks in order

1. The student should independently reproduce and explain the distinction between
   positive mean utility, individual wrong-direction rates and shared-experiment
   consistency, using the saved figures and full comparator record.
2. Resolve the exact Table 5 sample/count/normalization/export provenance if an
   authoritative processing record becomes available. The unsent questions make
   the missing information concrete; inspecting more scores cannot substitute.
3. Pursue independent confirmation only after a compatible resource's provenance
   and untouched evaluation scope qualify. Otherwise retain the limited benchmark
   claim and its failures in the final research account; do not redesign gates
   or claim universally reliable RNA control.

No background experiment or scheduled task is running. No money was spent.

## 4. Explicit do-not-touch list

- Astrocyte local sequences/features/outcomes; N-zip outcomes; TDP EV5 stability.
- Historical FinalShot and Mechanism v2-v5 artifacts, splits, models and negatives.
- Arora replicates 3/4; SIRLOIN NucLibC 3/4 and all NucLibB; Shukla 4-6/raw runs.
- Context confirmation groups and unused calibration labels.
- Faraway original confirmation patterns; later-condition, doxycycline, CLK and
  stability outcomes. No secondary result grants new access.
- Unadmitted mutREL and speckle outcomes; frozen research records; unrelated edits.
- Purchases, scheduled tasks, external messages and unfiltered repository pytest.

## 5. Confidence gaps

The evidence supports retrospective mean benefit in a single measured reporter
landscape, with substantial per-decision failures and competitive simple models.
It does not establish independent validation, a new biological mechanism, broad
generalization, complete novelty or finalist-level competitiveness. Exact
published table generation remains unresolved. No clarification of the zero-cost,
computational-only resource constraint is needed.

The earlier automatic-review rejection of new-dataset discovery, citing potential
biological misuse, remains respected. This continuation used already-admitted
results and exact source-code provenance only. The prior literature-exposure
records remain part of any future confirmation review.

DONE — this diagnostic checkpoint is complete; the broader research goal remains unfinished.
