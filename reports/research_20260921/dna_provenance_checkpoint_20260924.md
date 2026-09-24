# Provenance checkpoint — 24 September 2026

AI-authored technical record. No money was spent, no scheduled task was created,
and no external message was sent. No new RNA-localization outcomes were used.
This checkpoint improves traceability; it does not claim new biological validation.

## 1. Project goal

Establish a useful computational RNA-localization selection result that survives
strong controls, reliable data provenance and a specific prior-art comparison.
The Faraway secondary positive remains limited; complete novelty and independent
generalization have not been established.

## 2. Complete versus in progress

### Full public DNA audit completed

The official [E-MTAB-13330 record](https://www.ebi.ac.uk/biostudies/arrayexpress/studies/E-MTAB-13330)
identifies ERR12019311 as plasmid DNA, separately from the RNA run. The complete
341,076,082-byte file passed official ENA MD5
`591291d31db03888856f11dbfb6d0981`, SHA-256, full gzip/FASTQ integrity, and archive
totals of 231,531 reads and 382,186,856 bases. The SHA-256 is
`51407474c6e357cef28f6e7802291e7d06916f4a19da848fe421eb93d8f75586`.
The DNA file and reproducible download chunks remain local and outside Git;
metadata and receipts are versioned.

The first 5,000 records were classified under the criteria committed in
3ff287f. The subsequent full-file extension retained those exact filters,
reused the pilot calls, and reproduced the full barcode inventory. It completed
during the interruption; no duplicate job was started afterward.

| Audit quantity | Observed |
|---|---:|
| Total DNA reads | 231,531 |
| Unique qualifying barcode occurrence with exact flanks and Q10 barcode | 11,898 reads |
| Eight segment calls passing alignment filters | 5,833 reads |
| Distinct barcode strings with passing calls | 5,381 |
| Distinct called genotypes | 4,606 |
| Barcode strings with conflicting genotype calls | 14 |
| Barcode associations supported by at least 3 calls and 90% agreement | 37 |
| Previously tested 8-hour genotypes with any passing call | 89 of 207 |
| Previously tested 8-hour genotypes with repeat-supported barcode | 2 of 207 |

Of the 5,381 barcode associations, 4,971 have one passing read, 373 have two,
32 have three, and five have four. Twenty-nine of the 37 repeat-supported
barcodes occur exactly in the deposited barcode list. Both repeat-supported
associations covering 8-hour target genotypes occur in that list.

These are **eight-segment genotype calls under declared filters**, not proof of
intact, error-free constructs. Alignment coverage is a reference span, including
deletions. The rules allow limited overlap and do not bound all intervening gaps.
Q10 barcode strings may contain sequencing errors, and read support may include
PCR duplicates. Conflicts are diagnostic flags, not proven assembly errors.
The conservative exact-flank screen discards many reads; lack of support in this
screen does not show that the remaining reported constructs are wrong.

An independent code review found no blocking orientation or scope defect and
identified these interpretation limits. Existing barcode-orientation, quality,
reference-recovery and truncation tests passed. They are software checks, not
estimates of real-read classification accuracy.

### Official processed formats agree

Header inspection and the deposited inventory show that the native TSV files
also lack a barcode-sequence-to-numeric-ID map. Numeric barcode IDs are assigned
within each assay in the author code; DNA list row numbers cannot substitute.

The official [E-MTAB-13329 archive](https://www.ebi.ac.uk/biostudies/arrayexpress/studies/E-MTAB-13329)
TSVs were downloaded with size and SHA-256 receipts. Numeric comparison was
restricted to the original development candidate rows and frozen 8-hour target
rows. Other rows were examined only for construct, time and replicate metadata.

| Comparison | Development | 8-hour target |
|---|---:|---:|
| Already-open rows compared | 1,104 | 726 |
| Rows matching log2 nucleus/cytoplasm ratio within 1e-10 | 1,104 | 726 |
| Maximum absolute log2-ratio difference | 1.31e-14 | 1.30e-14 |
| Metadata keys missing, extra or changing genotype | 0 | 0 |

All 32,310 first-experiment and 16,077 second-experiment metadata rows match the
workbook. The native second-experiment TSV also labels its later condition
`16 hr`; both deposited formats therefore share the discrepancy with the paper,
author script and sample metadata, which describe 24 hours. Later-condition
localization values were not parsed. Do not silently relabel or open them.

This is a useful format/provenance check. It is not independent experimental
replication and does not validate raw fraction counts. The earlier 8-hour
quadratic and categorical model regrets remain 0.42841 and 0.44186 against
0.50000 uniform choice. The failed original interaction gate remains failed.

### Resource decision

**Do not expand RNA downloads or tune Faraway selectors to compensate for the
missing mapping.** Under the current evidence, this route does not yet support
barcode-independent validation of the 207-construct test. Retain the secondary
positive as a processed-data result with these limits. Further raw validation
needs an authoritative assay-specific barcode map or a separately scoped,
auditable reconstruction that preserves all closed-outcome boundaries.

The bounded mutREL source review also remained unresolved: inspected material
does not establish whether multiply-mutated molecules were excluded or counted
marginally in the event table. See mutrel_provenance_review_20260924.md. The cached
PDF previously called methods is supplementary discussion, not full Methods.
No clean single-mutant interpretation is admitted on that basis.

### Implementation and preservation

faraway_dna_download.py handles the allowlisted file, range retries, checksums
and FASTQ verification. faraway_dna_audit.py performs the initial DNA inventory
and pilot classification. faraway_dna_full_audit.py applies unchanged rules to
the rest of the DNA file. faraway_processed_correspondence.py compares official
formats while guarding numeric outcome access. All work remains in the separate
research namespace on main; unrelated user edits remain untouched.

The DNA download specification was temporarily appended with the alignment
criteria after its receipt was generated. It was restored byte-for-byte to the
receipt's hash, and those criteria were preserved in faraway_dna_alignment_spec.md.
The full-audit specification and its source were written before execution and
hashed in the result, but had not been committed when execution began; this is
a DNA provenance follow-up, not a prospectively committed outcome test.

The verification_20260924_dna.json receipt records 53 passing scoped tests, all
228 unchanged original snapshot files, 14 verified experiment freezes, original source
preservation, all existing experiment freezes, DNA-audit dependencies and download
provenance. No unfiltered pytest was run. The old preservation-audit failure on
the pre-existing modified analyze_finalshot_grouped_gates.py remains unchanged.

The independent processed-file review found no observed whitelist violation.
It confirms ratio correspondence only, not equality of individual fraction CPMs.
A future standalone rerun must additionally verify the secondary eight-hour
freeze and its target manifest before reconstructing the allowed row keys;
this checkpoint verified that freeze separately. See
processed_correspondence_review_20260924.md.

The completed contribution review recommends the SRLE measured six-mer swap
benchmark as the clearest existing small-edit contribution, with short-motif
controls and explicit transfer failures. This does not establish a novel model
or mechanism. See contribution_review_20260924.md.

## 3. Next three tasks in order

1. Package the strongest already-supported computational claim for independent
   arithmetic replay, with its simple baselines and failed comparisons visible.
2. Resolve an authoritative measurement mapping before any further raw-based
   validation. Do not treat additional reads or software agreement as independent
   biological evidence.
3. Prepare a reproducible benchmark package and a claim-by-claim prior-art review;
   the student should independently reproduce and interpret the retained results.
   Independent compatible validation remains a scientific requirement, not a
   completed milestone.

## 4. Explicit do-not-touch list

- Astrocyte local sequences/features/outcomes, N-zip outcomes and TDP EV5 stability.
- Historical FinalShot and Mechanism v2-v5 artifacts, splits, models and verdicts.
- Reserved Arora and SIRLOIN replicates/libraries; Shukla replicates 4–6/raw runs.
- Original context-confirmation outcomes and unused calibration labels.
- All Faraway original confirmation GA outcomes, later-condition outcomes,
  doxycycline, CLK and stability values; the secondary result grants no access.
- Unadmitted mutREL and speckle outcome values; no assumption of clean mutations.
- All frozen/hash-pinned records and unrelated user changes. No purchases,
  scheduled tasks, author contact or unfiltered repository pytest.

## 5. Confidence gaps

Raw barcode-to-assay-ID correspondence remains absent from the inspected public
files. The DNA screen gives sparse repeat support and no independently measured
localization. Cross-format agreement shares a common data origin. Novelty and
cross-gene/context validity remain unproven; more favorable model scores would
not resolve those gaps.

A delegated new-dataset search was stopped after unsolicited protected-study
aggregate snippets, then blocked by automated content review citing potential
biological misuse. That discovery branch is incomplete. No returned protected
study was followed or used; see literature_scope_followup_20260924.md. No new
protected local outcome file was opened, but the exposure record must accompany
any future formal confirmation review.

DONE — this checkpoint is complete; the broader research objective is unfinished.
