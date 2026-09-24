# Verified evidence-package checkpoint — 24 September 2026

AI-authored technical record. This continuation adds reproducibility and a bounded
prior-art comparison; it introduces no new model fit, localization outcome,
sequence design or biological experiment. No spending, scheduling or external
message occurred. The research objective remains unfinished.

## 1. Project goal

Establish a useful, reproducible computational RNA-localization selection result
with an accurately bounded contribution. The strongest existing small-edit result
is a benchmark of fixed choices among already-measured, composition-preserving
six-mer alternatives. The published exhaustive screen already measured those
alternatives. This is not a newly performed intervention experiment.

## 2. Complete versus in progress

The prior checkpoint is committed as f80a753 on main: full public plasmid DNA
screen, scoped Faraway processed-format ratio correspondence, contribution review
and unresolved measurement issues. Earlier 3ff287f added the public DNA downloader
and pilot; 2f2d876 preserved the bounded Faraway secondary positive and failed
robust-context superiority test. These leave the historical negatives unchanged.

This checkpoint creates a compact, self-contained arithmetic replay package:

- results/research_20260921/srle_aggregate_replay_20260924.zip: 145,042 bytes,
  SHA-256 d81cdcd9f6ecdbbd9d98806514de5931bfec0b0f8bcbbaea808af06cd3c1a7f3.
- Eight explicit members: standalone replay.py, 960 anonymized aggregate rows,
  the original 2,000 bootstrap index draws, expected summary, provenance and
  integrity records, README and evidence ledger. No sequence identifiers or
  source outcome tables are packaged.
- The independent standard-library calculation reproduces all 54 statistical
  values with maximum absolute difference 1.1102230246251565e-16, below 1e-12.
  Three additional cohort metadata numbers are compared; the excluded-parent
  count 17 is carried metadata, not independently derived from these aggregates.
- Fresh extraction and bundled Python with `-I -S -B` also pass. This disables
  site packages and avoids dependence on the project runtime for replay.
- Independent code review found the equal-composition weighting, combination of
  directions and paired bootstrap preserved, with no blocking issue.

The positive within-assay result remains: pair-model regret gains over uniform
choice are 0.23103 and 0.25342; short motifs give 0.21991 and 0.22129. Pair-minus-
short-motif intervals include zero in both constituent replicates. Directed
pair-model NRS changes are about 0.116 and 0.120 log2 assay-score units. These
values do not measure a corresponding percentage-point change in cellular RNA
localization. Training aggregates already incorporated these experiments;
recounting them is not independent biological validation.

The figure srle_aggregate_summary_20260924_v3.png (and editable SVG) shows the
retained signal and the uncertain advantage over the strong simple comparator.
Visual inspection passed. Version 1 overlapped a legend with data; version 2
fixed placement but introduced an encoding defect in one label. Both are retained
as superseded presentation attempts. Version 3 changes presentation only.

The admitted-paper review, srle_prior_art_scope_20260924.md, checks cached primary
article text and captions. The paper reports composition enrichment, motif
validation and NRS-guided prediction controls. No explicit exact-composition swap
decision benchmark was found in the inspected text. This identifies a possible
evaluation contribution, not proof of novelty across all prior work. No broad
dataset search was resumed. Source: [SRLE-seq, DOI 10.34133/csbj.0107](https://doi.org/10.34133/csbj.0107).

The original raw-swap freeze omitted robustness_predictions.csv and imported
modules. The later checkpoint records the prediction file's hash, which still
verifies. This is documented as an incomplete historical freeze; it is not
retroactively repaired or advertised as full prospective confirmation.

### Architecture and verification

- srle_aggregate_package.py: verifies archived hashes, reads only saved aggregate
  metric fields, drops sequence identifiers, emits the explicit release allowlist.
- srle_aggregate_replay.py: pure-standard-library integrity, cohort balance,
  equal-class means, paired bootstrap and comparison with the archived summary.
- test_srle_aggregate_replay.py: synthetic unequal-class-size weighting,
  mismatched comparison cohort rejection and tamper detection.
- srle_summary_figure_v3.py: plots only the verified saved summary; no fits or
  raw-data access. Older versions remain recorded for visual audit.

All 56 scoped research tests pass. All 14 existing experiment freezes and all
228 original snapshot files verify unchanged. Receipts:
verification_20260924_srle_replay.json, srle_standalone_verification_20260924.json,
srle_aggregate_package_receipt_20260924.json. No unrestricted pytest ran. The
earlier 113-test safe Mechanism-v2 result is retained; its pre-existing historical
preservation mismatch at analyze_finalshot_grouped_gates.py remains unresolved
and was not modified to force a pass. The 33 unrelated tracked changes and five
unrelated untracked items remain outside this checkpoint's staging scope.

## 3. Next three tasks in order

1. Have the student independently run and explain the replay, its regret metric,
   weighting, simple comparator and training/replicate dependence. Use the full
   evidence ledger to choose the narrow research claim for the remaining month.
2. Complete a claim-by-claim comparison within the already-admitted primary
   literature and its existing supplements/code, concentrating on the exact
   measured-choice benchmark. Document uninspected material and unresolved
   table-generation or barcode-to-measurement provenance explicitly.
3. Pursue independent confirmation only if a compatible, verified measurement
   chain and a genuinely untouched admissible evaluation become available. Freeze
   the complete test before use. If those conditions cannot be met, present this
   as a limited computational benchmark with negative transfer results rather
   than claim novel biological control or validated generalization.

These are ordered research tasks, not scheduled jobs. No background experiment
is running at this checkpoint. More architecture searching on the same data
would not resolve the identified independence or novelty gaps.

## 4. Explicit do-not-touch list

- Astrocyte local sequences, features and outcomes; N-zip outcomes; TDP EV5 stability.
- Frozen FinalShot and Mechanism v2-v5 artifacts, splits, models and NO-GO verdicts.
- Reserved Arora replicates 3/4; SIRLOIN NucLibC 3/4 and NucLibB; Shukla 4-6/raw runs.
- The 22 context confirmation groups and unused calibration labels.
- Faraway original confirmation patterns, later-condition, doxycycline, CLK and
  stability outcomes. Secondary positives grant no additional access.
- Unadmitted mutREL and speckle outcome values; all existing freezes and unrelated
  user work. No purchases, scheduled tasks, external messages or unfiltered pytest.

## 5. Confidence gaps

The aggregate replay validates arithmetic, not fitting, candidate construction,
measurement mapping, independent biology, complete novelty or award prospects.
Raw-data checks share source experiments with training; neighborhood dependence
and incomplete training uncertainty remain. Public table-generation provenance
and the Faraway assay-specific barcode map remain unresolved. No further budget
or wet-lab clarification is needed; zero-cost computational work is the constraint.

Automatic content review previously rejected the delegated new-dataset search,
citing potential biological misuse. That branch remains incomplete and was not
resubmitted. Permitted work here was limited to existing-result arithmetic,
provenance and documentation. The literature exposure records remain attached
to future confirmation review; they preclude a claim of perfect ignorance of
published protected-study aggregates.

DONE — this reproducibility checkpoint is complete; the broader research goal is not.
