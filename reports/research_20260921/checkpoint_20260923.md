# Computational research checkpoint — 23 September 2026

AI-authored operational research notes and analysis/code attribution. These are
not student-authored competition prose. The student must understand and independently
interpret the analyses and follow the competition's applicable disclosure rules.
No money was spent, no scheduled task was created, and no external message sent.

## 1. Project goal

Find a reproducible, useful and specifically novel computational result about
selecting RNA-localization interventions. The current defensible question is
whether sequence-based selection survives composition controls and transfers
between experimental contexts. Neither universal transfer nor STS placement is
established. Historical FinalShot and Mechanism v2-v5 negative verdicts stand.

## 2. Complete versus in progress

Previously completed positives remain limited to within-assay composition-controlled
selection and source-only calibrated-context diagnostics. The nested calibration
comparison showed regret improvement 0.04525 over a tuned target-only baseline,
but no clear improvement over the strongest sibling-context predictor. The locked
external/development gates did not pass. See checkpoint_20260922.md for details.

The HeLa fragment-selection pilot was frozen in commit 3978c48 and failed:
205 eligible fragments, 12 genes, 11 families; source-model regret 0.56930,
composition 0.51826, CCC 0.48303, random 0.5. The required 12 families were absent.
The separately frozen repeatability diagnostic (709d371) found mean cross-replicate
Spearman -0.00417 and selection regret 0.50218. This is not a formal noise ceiling.

A post-hoc correspondence audit found that 31 previously opened GEO Total1 zeros
had 6-760 exact high-quality reads in the first 16 MiB of the documented Total1
run SRR5528987. The author repository's four-replicate raw table is also not
related to the final six-replicate GEO table by a common positive column scale
on the 277 already-open identifiers. The relation between these tables remains
unresolved; this does not establish the cause or an error in the paper. Do not
interpret the failed pilot as clean evidence about biological transfer.

The complete 581,039,199-byte Total1 raw file has now been downloaded from official
ENA, verified against archive MD5 d3660208a08420ee2f0e65f48f478032, and verified
byte-identical to the earlier prefix. Across all 9,603,871 FASTQ records, all 31
GEO zero rows have 157-22,579 exact Q30-barcode/Q20-insert reads. Spearman between
full exact-read counts and GEO Total1 is 0.13114. The audit examines only the
previously opened identifiers and Total1; replicates 4-6 remain closed. Full
results are shukla2018_total1_count_audit.json and the companion CSV.

The new SEERS resource is explicitly open access at the official GSA-Human
archive. One L6 biological sample contains the numbered runs, so R1-R4 are not
treated as four biological replicates. Its 2024 release predates updated manuscript
methods and processed-data filenames. The relevant processed CSVs were absent
from the inspected official GitHub tree and releases.

SEERS raw files use concatenated gzip members. The new decoder reads every member
and discards an incomplete final FASTQ record. Tests cover concatenation, truncation,
CRC corruption, orientation, quality and outcome-scope boundaries. The earlier
HeLa and mutREL prefixes have one member and were not affected by this issue.

DNA-only expansion to 16 MiB per mate yielded 104,437 concordant Q30 pairs,
2,927 inserts supported by at least five pairs, and 45 exact-composition groups
containing 241 candidates. Six high-quality mate disagreements were discarded.
This is partial-file QC, not full-archive MD5 verification.

The exploratory RNA screen was frozen and committed as ff42592 before RNA access.
Only R1 cytoplasmic and nuclear runs, 16 MiB per mate, were examined. Fixed Q30
filters and at least ten reads per fraction left only five groups (25 candidates),
below the required twenty. Source kmer regret was 0.44949, CCC 0.55810, CCTCCC
and random 0.5; the source position-pair secondary model was 0.50789. Primary
gain over random was 0.05051, descriptive group CI [-0.14354, 0.28447]. The screen
is **inconclusive and did not pass**, not a positive result. No post-result
filter adjustment or expansion was performed. This one-sample, older-protocol
screen cannot establish independent biological generalization.

Current modules: seers_dna_qc.py handles partial multi-member gzip and paired
genotype QC; seers_dna_expand.py expands DNA-only coverage; seers_prefix_transfer.py
freezes predictions and implements the scoped RNA screen. shukla_raw_download.py
retrieves and verifies one documented Total1 file; shukla_count_audit.py reconciles
its counts with previously opened processed values. Existing source modeling,
raw SRLE analysis, context calibration, and historical pipelines remain unchanged.

The latest isolated research suite passed 38 tests. All 11 research freezes and
all 228 original snapshot files verified unchanged. Earlier this session the
safe Mechanism-v2 test target passed 113 tests. Its preservation audit still fails
on the pre-existing modified analyze_finalshot_grouped_gates.py; no repair or
reinterpretation was attempted. Unfiltered pytest was never run. Unrelated user
changes remain unstaged. Work is on main; ff42592 follows 709d371 and 3978c48.

## 3. Next three tasks, in order

1. Determine whether a documented mapping can reconcile Total1, using already-open
   data only; otherwise mark that endpoint unsuitable and stop spending effort on it.
2. Resolve SEERS archive/protocol provenance and locate the updated public processed
   data. If a deeper old-archive follow-up is warranted, preregister a new question
   and complete read-depth analysis; do not relabel this failed screen or treat
   additional technical runs as independent biology.
3. Consolidate the strongest reproducible contribution with explicit transfer
   limits, competitive baselines and a specific prior-art comparison. Prioritize
   a credible bounded claim over further unrestricted model searches. Independent
   compatible validation remains required for the proposed broader claim.

## 4. Explicit do-not-touch list

- Astrocyte sequences, features, labels, outcomes and downstream sealed files.
- N-zip outcomes and quarantined TDP EV5 stability.
- Historical FinalShot and Mechanism v2-v5 frozen artifacts, gates, splits,
  representations, caches and negative verdicts; no v6 rerun on the same data.
- Arora replicates 3/4; SIRLOIN NucLibC replicates 3/4 and all NucLibB outcomes.
- The 22 context-calibration confirmation groups and unused calibration labels.
- Shukla Nuclei4-6 / Total4-6 and corresponding reserved raw runs.
- All experiment freezes and their hashed files; create separate diagnostics.
- SEERS runs outside the explicitly frozen R1 scope within this screen.
- Unrelated user edits; paid services, purchases, and scheduled tasks.

## 5. Confidence gaps

The limiting gaps are reliable raw/processed correspondence, updated SEERS
protocol provenance, adequate read depth for composition-matched groups,
independent biological replication, and a contribution demonstrably distinct
from established motif-based localization modeling. Fragment selection is not
proof about minimal edits or endogenous RNA. Current positive within-assay
results do not establish the broader requested novel result. No further user
permission is needed for free, scoped computational work already authorized.

Primary references: [Shukla 2018](https://doi.org/10.15252/embj.201798452),
[SEERS archive](https://ngdc.cncb.ac.cn/gsa-human/browse/HRA008408),
[L6 sample metadata](https://ngdc.cncb.ac.cn/biosample/browse/SAMC4114749),
[SEERS preprint](https://www.biorxiv.org/content/10.1101/2025.06.09.658412v2.full),
[official SEERS repository](https://github.com/gao-lab/SEERS).
