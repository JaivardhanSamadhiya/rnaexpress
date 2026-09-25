# SRLE matched random-reference checkpoint — 24 September 2026

AI-authored technical evidence record, not student submission prose. This is a
post hoc comparison of previously saved choices and measurements. Its specification,
implementation, tests and dependencies were committed in `ba5845a` before the
reference was calculated. No new model, sequence recommendation, outcome opening
or biological experiment was created.

## 1. Project goal

Establish what a reproducible, composition-controlled computational benchmark can
show about choosing among measured RNA-localization alternatives. The present
positive is an improvement over an exactly matched random-choice expectation
within one reporter assay. Complete novelty, a new mechanism and generalization
to independent biological settings remain unestablished.

## 2. Complete versus in progress

### The missing comparison is now complete

A deterministic composition tie choice is not random choice. Neither 25% benefit
in both replicates nor 50% benefit in one replicate is automatically the relevant
chance level. The new audit enumerates the original measured candidates for each
retained parent and computes the exact expectation for choosing uniformly among
them. Each candidate retains its identity across the two replicates. Indicators
and the two-replicate minimum are computed before averaging, first over candidates
within a parent, then parents within a composition class, then the 60 classes
equally. No additional random choices or sequences were generated.

The eligible cohort remains 592 of the original 609 parents, in 60 composition
classes. Each retained parent has 2–7 candidates; their counts sum to 1,744 across
parents, with overlapping neighborhoods. This sum is not an independent sample
size. The audit reconstructed every saved choice's directed change and regret
gain within 2.78e-16, with unchanged choice identities and candidate counts.

| Fixed policy / reference | Better in both: decrease | Better in both: increase | Worse in both: decrease | Worse in both: increase |
| --- | ---: | ---: | ---: | ---: |
| Exact uniform expectation | 36.27% | 39.21% | 39.21% | 36.27% |
| Composition tie choice | 32.42% | 44.34% | 44.34% | 32.42% |
| Position additive | 43.56% | 47.17% | 30.10% | 31.30% |
| Short motifs (1–3-mers) | 50.94% | 54.47% | 25.13% | 22.11% |
| Position pairs | 50.96% | 56.98% | 20.78% | 23.57% |

All percentages are **equal-class averages of within-class decision fractions**,
not unweighted fractions of the 592 parents. Better/worse means movement of the
measured NRS score in/against the requested direction relative to the parent;
it does not measure biological safety, toxicity or cellular RNA percentages.
The remaining mass comprises opposite signs across replicates; no numerical
ties occurred at the fixed 1e-12 tolerance.

| Policy | Gain over uniform in better-in-both rate: decrease | Gain over uniform in better-in-both rate: increase |
| --- | ---: | ---: |
| Composition tie choice | −3.85 pp [−7.85, 0.44] | 5.13 pp [0.44, 9.84] |
| Position additive | 7.29 pp [3.27, 11.10] | 7.96 pp [2.97, 12.62] |
| Short motifs (1–3-mers) | 14.67 pp [11.53, 17.90] | 15.26 pp [10.81, 19.78] |
| Position pairs | 14.69 pp [11.25, 18.08] | 17.78 pp [14.08, 21.57] |

Here pp means percentage points. Brackets are descriptive 95% intervals from
2,000 paired composition-class bootstrap draws, conditional on the fitted models,
fixed choices and shared experiment. These are post hoc comparisons, not a new
confirmatory pass/fail gate. All four models, both directions, seven per-replicate
metrics and five paired metrics are preserved in the complete result.

For position pairs, the worse-in-both fraction falls by 18.43 pp
[15.01, 21.96] for decrease requests and 12.70 pp [9.24, 16.08] for increase
requests relative to uniform. These are reductions (uniform minus model) for
readability; the machine-readable result consistently stores model minus uniform.
Nevertheless, 20.78% and 23.57% of the pair model's decisions remain worse in both
replicates. The simple short-motif model also improves substantially on uniform.
This comparison does not establish pair-model superiority over that comparator.

The mean of the smaller observed directed change across the two replicates is
−0.08837/−0.09832 for uniform and 0.03678/0.01297 for position pairs, in
decrease/increase directions. The paired differences are 0.12515
[0.10360, 0.14700] and 0.11130 [0.09026, 0.13165] log2-score units. An observed
two-replicate minimum is not a confidence bound or a future-performance guarantee.

### Verification and artifacts

An independent implementation, using standard-library sums and quantiles with
the same bootstrap indices, reproduced all 190 estimates and 380 interval
endpoints. The maximum discrepancy was 1.11e-16. It also checked complete cohorts,
category sums, directional symmetry and paired probability bounds. This checks
anonymous aggregate arithmetic; it does not independently verify source biology.

The figure `results/research_20260921/srle_uniform_risk_20260924.png` (and SVG)
shows all models' paired outcomes and the matched benefit-rate contrasts.
It was visually checked for legibility, overlap and complete comparator coverage.
The standalone `srle_risk_replay_20260924.zip` packages anonymous summaries for
both fixed-choice risk and the exact uniform reference, with a standard-library
replay and integrity record. The original aggregate replay remains unchanged.

The new ZIP contains 13 members and is 181,591 bytes (SHA-256
`b4f79a6d3483dcdf4f56e0bfdb9bf5f8899c2337c07bcdc663c3dd00d6a179bd`).
Fresh explicit extraction and bundled Python `-I -S -B replay.py` reproduced
342 estimates and 684 interval endpoints, or 1,026 numerical comparisons,
with maximum discrepancy 3.33e-16. All 1,800 anonymous rows across 30 balanced
cohorts are retained. This verifies aggregation only, not candidate construction,
training or the original measurements.

New modules and their roles:

- `srle_uniform_risk.py`: verifies the committed freeze, reconstructs the original
  measured candidate roster, checks the archived decisions, and computes the
  exact uniform reference and class-paired contrasts.
- `test_srle_uniform_risk.py`: five synthetic checks covering candidate semantics,
  order of averaging, replicate identity and nonfinite archived values.
- `srle_uniform_risk_figure.py`: plots only the completed anonymous summaries.
- `srle_risk_replay.py` / `srle_risk_package.py`: portable arithmetic replay and
  packaging; no fitting, raw-data processing or sequence output.

All 65 scoped research tests passed with bundled Codex Python. Preservation
verification and package execution details are recorded in
`results/research_20260921/verification_20260924_srle_uniform.json`.
All 16 experiment freezes and all 228 original snapshot files remain byte-identical
to their recorded hashes.
No unrestricted pytest was run. The historical preservation mismatch at
`analyze_finalshot_grouped_gates.py` remains a pre-existing user modification.
Work remains on `main`; unrelated user edits stay outside research commits.

### What is still in progress

The score table's exact count/sample/normalization/export chain remains unresolved.
The inspected public code/documentation differences do not prove the published
measurements are wrong. The provenance dossier and concrete unsent author
questions remain available; no external message was sent.

These two constituent replicates contributed to the source aggregate used for
training. The original holdout excludes exact test sequences from fitting, but
related sequences, composition classes and the experiment are shared. Candidate
sets contain only eligible test neighbors, omit the unchanged-parent option,
and retain the original nonzero-range and complete-coverage restrictions. No
independent gene, sequence-neighborhood, biological-context or experiment test
has been supplied by this diagnostic. Earlier failed transfer gates remain failed.

The missing comparator is now resolved. Do not start more model, split, sign,
threshold or favorable-subgroup searches on these measurements merely to make
the positive look stronger. The claim-to-evidence map's stop rule remains in force.

## 3. Next three tasks in order

1. Independently replay and explain the bounded result, including simple-model
   performance and individual failures. Use the figure, portable replay and
   evidence map to support the student's own analysis and writing, with AI
   assistance disclosed.
2. Resolve the original Table 5 processing provenance if an authoritative record
   becomes available. The unsent provenance questions specify the missing sample,
   replicate, count, normalization and export details; more outcome analysis
   cannot answer them.
3. Pursue independent confirmation only when an authorized compatible resource
   has established provenance and an untouched evaluation scope. If unavailable,
   finish the reproducible single-assay benchmark with its explicit limits and
   failures. Do not replace failed gates or promise a competition outcome.

No background experiment or scheduled task is running. No money was spent.

## 4. Explicit do-not-touch list

- Astrocyte local sequences, features, outcomes and downstream records; N-zip
  outcomes; quarantined TDP EV5 stability.
- Historical FinalShot and Mechanism v2–v5 artifacts, representations, splits,
  models, selection rules and negative gates; no same-data v6 rescue.
- Arora replicates 3/4; SIRLOIN NucLibC 3/4 and all NucLibB; Shukla Nuclei/Total
  4–6 and reserved raw runs; the 22 context confirmation groups and unused labels.
- Faraway original 25 confirmation patterns across assays, later-condition
  numeric outcomes, doxycycline/CLK/stability outcomes; unadmitted mutREL and
  speckle outcomes.
- Every frozen research record and unrelated user modification. The comparator
  does not authorize reopening any protected outcome or rewriting prior evidence.
- Purchases, scheduled tasks, external messages and unfiltered repository pytest.

## 5. Confidence gaps

Arithmetic and cohort preservation are well supported. The positive comparison
is conditional, retrospective and assay-specific; substantial individual failure
persists. Missing authoritative table provenance, independent compatible
measurements and broader prior-art evidence prevent claims of complete novelty,
a new mechanism, generally reliable RNA control or STS-finalist competitiveness.
The zero-cost, computational-only constraint is clear and needs no clarification.

The earlier automatic approval review rejected new-dataset discovery because it
cited potential biological misuse. That action remains unperformed; this
continuation used admitted saved measurements and anonymous arithmetic only.

DONE — this comparator checkpoint is complete; the broader research goal remains unfinished.
