# Research checkpoint: 22 September 2026

AI-authored technical execution record, not a student-authored research report.
No money spent, scheduled tasks created, external messages sent, or historical
sealed datasets opened. Work remains on main. The project is not complete and
no completely novel, independently validated positive result is established.

## Project goal and current scientific direction

The original goal is to select RNA-localization interventions computationally,
ideally with small sequence changes and generalization to new biological contexts.
Historical universal zero-shot claims remain closed NO-GO. New work is isolated
in research_20260921 and evaluates narrower, measurable claims on public data.

Current evidence favors comparing biological context matching with small amounts
of calibration before adding model complexity. This is a resource-allocation
conclusion, not a new molecular mechanism or a claim to have invented transfer
learning. DeepLocRNA already uses domain-specific transfer learning; the 2022
source paper already establishes context dependence.

## What completed in this continuation

**Frozen context-calibration experiment.** Commit 281ddb2 froze source, tests,
data hashes, metadata grouping, partitions and gates before new outcome scoring.
After exclusions, 8,013 rows belong to 113 explicit gene/sequence groups. Whole
groups were separated: 61 source, eight calibration, 22 development and 22 reserved
confirmation. Exhaustive >=95% normalized global Levenshtein checks and shared
40-nt tract grouping found no additional cross-family merges. This does not
establish a complete paralog ontology.

The target budget was 64 attempted fragments. Actual usable target labels were
56 spliced, 47 unspliced, 47 circular and 59 SCRcircular, across all eight calibration
groups. Source models used only other contexts in the source groups; calibration
and evaluation gene groups never entered source fitting. Numeric outcome parsing
was restricted to admitted rows and four localization columns. This is a
retrospective budget simulation, not an assertion that only 64 labels exist.

Twenty development groups were evaluable in each context. Positive numbers below
mean lower normalized selection regret for the three-source calibration model.

| Baseline | Regret gain | Paired 95% component interval | Gate |
| --- | ---: | --- | --- |
| Target-only 1-3-mer Ridge | 0.04446 | [-0.00891, 0.09265] | Failed |
| Base composition Ridge | 0.08062 | [0.03850, 0.12524] | Passed |
| Three random compressed features | 0.07360 | [0.02570, 0.11792] | Passed |

The overall discovery gate FAILED because superiority to the stronger target-only
sequence baseline is uncertain. Circular-context gain was negative (-0.04258),
while SCRcircular contributed the largest gain (+0.15328). Thresholds were not
changed. The 22 confirmation groups remain closed; subsequent diagnostics cannot
authorize their opening or reverse this failure.

**Source-only learning-curve diagnostic.** Commit e3f22bf recorded the failure and
froze a separate exploratory diagnostic on the original 3,235 source rows only.
Five group folds, three fixed calibration panels and three nested budgets yielded
58 evaluable groups. Original calibration, development and confirmation groups
were excluded. All settings were fixed; no architecture or hyperparameter search.

| Attempted labels | Transfer regret | Target-only regret | Similar-context source, zero calibration labels |
| --- | ---: | ---: | ---: |
| 16 | 0.42735 | 0.46537 | 0.40457 |
| 64 | 0.39720 | 0.45084 | 0.40457 |
| 256 | 0.39152 | 0.42737 | 0.40457 |

At budget 64, transfer improved regret over target-only by 0.05364 (descriptive
component interval [0.02972, 0.07665]), with positive differences in all four
contexts. However, its advantage over the simple similar-context source was only
0.00736 [-0.00549, 0.02034]. At 16 labels the simple source performed better.
This demonstrates why the simple source is a necessary comparator. The intervals
do not include full training-sample uncertainty and these are reused-data
exploratory results. They are not independent confirmation or minimal-edit tests.

The figure context_calibration_summary_v2.png and its SVG show both analyses.
The first figure version is preserved; v2 moves a legend away from measured data.

**Nested regularization control.** Commit 701a6f9 froze a further source-only
diagnostic at budget 64. Leave-one-calibration-group-out selection chose among
six Ridge penalties, with all preprocessing fit inside each inner fold. The fixed
transfer model still beat the tuned target-only kmer model by 0.04149, descriptive
interval [0.02034, 0.06102]. Tuning both models gave a gain of 0.04525
[0.02282, 0.06626], positive in all four contexts. Tuned transfer beat tuned
composition by 0.06320 [0.03822, 0.08659]. Its advantage over the simple sibling
source remained uncertain: 0.01112 [-0.00320, 0.02617]. Thus baseline shrinkage
does not explain the entire observed source-information benefit, while a need
for calibration over a simple context-matched source remains unestablished.
These remain exploratory reused-source results; the original discovery still
failed and confirmation remains closed.

## New free public resources

**Wen et al. 2026 speckle-localization study.** Downloaded article XML (176,834
bytes) and supplementary archive (4,135,602 bytes) from Europe PMC. The article
specifies CC BY 4.0. Nested archives and workbooks passed CRC checks; no workbook
VBA/external links were detected. All 81 GenBank plasmids have valid DNA alphabets
and match their declared lengths (3,249-5,410 bp). There are 32 F, 44 M, three T7
and two U1 constructs. COLQ WT/mutant and SMN1/SMN2 each differ by exactly one
base in the provided plasmid sequence. Outcome values remain unexamined.

This is a useful small mechanistic resource, not 81 independent genes. Plasmid
DNA must not be scored as though it were expressed RNA. Transcript boundaries,
construct-to-measurement mapping and the appropriate mechanistic endpoint still
require resolution. Nuclear-speckle partition is not nuclear/cytoplasmic export.

**Yin et al. 2020 mutREL-seq, GSE107131.** Downloaded official GEO series/sample
metadata, the 10,240-byte processed TAR, publisher metadata and the 766,235-byte
free supplementary methods PDF. The processed member contains 401 substitution
entries, 96 deletion entries and one WT entry for a single NXF1 element, spanning
147 represented sites. Only identifier/site/mutation fields were examined;
numeric cell/cytoplasm/nucleus/chromatin counts remain unexamined. Reference bases
are internally consistent at represented sites, but the table does not supply
the complete WT sequence or replicate-specific columns. Isolated-mutant versus
co-occurring-mutation semantics and strand/coordinate conventions remain to be
verified before intervention scoring. Known U1 biology is prior art, not a new
finding here.

Subsequently, official Supplementary Table 9 (18,988 bytes) supplied PCR primers.
Using the documented 162-nt length, the metadata reference bases and primer ends
reconstruct every WT position with no missing/conflicting bases. An independent
internal primer matches exactly; the known U1 motif begins at position 37. The
reconstructed sequence and evidence are saved separately from the initial
inventory, which is preserved as a historical admission checkpoint.

The official ENA record for SRR6308285 lists paired FASTQ files totaling about
1.26 GB. Only the first 2 MiB of each mate were downloaded using verified HTTP
range responses; they are partial assets with SHA-256 receipts, not full-file
MD5-verified downloads. Of the first 2,000 read pairs, 649 passed an intentionally
limited exact-seed, ungapped alignment filter requiring >=40 shared Q30 bases
and no shared-base disagreement. Of those, 206 had >=2 substitutions supported
by both mates. This establishes co-occurrence in sampled molecules, not an
unbiased library-wide mutation rate. It does not establish whether the authors
filtered out such molecules before creating the published count table. No
compartment mapping or numeric localization-count outcomes were used. Resolve
that filtering question before treating each table row as an isolated SNV.

**SEERS:** the official current repository README names separate training and
A549 evaluation files but does not supply their download locations. It is not
currently an admitted processed-data source. No pretrained pickle/PyTorch model
was downloaded or deserialized.

Each downloaded asset has its URL, retrieval time, byte count and SHA-256 in a
receipt under data/external/research_20260921. Official provenance and checksums
establish source identity, not infallibility of measurements. Failed requests
are not evidence: Europe PMC mutREL XML returned HTTP 500, and the NCBI BioC URL
returned HTML rather than XML. The latter response is preserved with its receipt
but excluded from the admitted source set. One shell quoting error and one
console-encoding error affected text inspection only; neither produced results.

## Architecture of this continuation

- common.py: existing bundled runtime selection, hashes and immutable writes.
- resources.py: allowlisted free downloads and source receipts; frozen unchanged.
- context_calibration.py: sequence grouping, split/freeze, restricted outcome
  parsing, fixed source/calibration models, regret and conditional access gate.
- context_learning_curve.py: separate source-only, grouped budget diagnostic.
- context_regularization_audit.py: nested baseline tuning on calibration labels.
- context_figures.py: plots completed summaries without fitting or outcome access.
- new_resource_inventory.py and mutrel_inventory.py: outcome-free resource checks.
- mutrel_reference.py and mutrel_read_qc.py: reference reconstruction and bounded
  genotype co-occurrence inspection without compartment-outcome association.
- Existing pilots.py, robustness.py, raw_counts.py, raw_swap_consistency.py and
  sirloin_transfer.py preserve the previous exploratory/replication results.

The bundled Python ran all experiments. Matplotlib 3.10.8 and dependencies were
installed free in data/interim/research_20260921/plot_runtime; existing runtimes
and project requirements were not modified. Figure generation used NumPy 1.26.4.

## Verification and preservation

The 228-file original tracked-source snapshot remains byte-identical. All eight
new-research experiment freezes verify. The safe Mechanism-v2 test target passed
113 tests. The final research suite includes 21 tests, covering outcome-access
boundaries, unused-label isolation, nested-selection isolation, read orientation
and quality filtering; the final verification receipt records the run result.
No unfiltered pytest ran. The authorized legacy test command rewrites its test
XML report, as previously documented.

The historical preservation audit still fails at the pre-existing user-modified
src/analysis/analyze_finalshot_grouped_gates.py. No repair, restoration, verdict
change or historical model rerun was attempted. Other user edits remain intact.

## Next three tasks, in order

1. Resolve whether NXF1 processed counts excluded co-occurring mutations and how
   fractions were mapped to reads; match speckle constructs to expressed RNA and
   measurements. Reject unsuitable sources instead of inventing missing semantics.
2. If a compatible independent resource qualifies, freeze one narrow selection
   test with simple context-matched and short-motif baselines before opening its
   outcomes. Preserve every existing failed gate and closed confirmation set.
3. Consolidate the strongest supported contribution: composition-controlled
   within-assay edit selection and/or a calibrated-context benchmark with explicit
   transfer limits, complete reproduction and an updated prior-art comparison.

## Explicit do-not-touch list

- Astrocyte sequences, features, outcomes and downstream sealed data.
- N-zip outcomes and quarantined TDP EV5 stability.
- Historical FinalShot and Mechanism v2-v5 frozen sources, features, splits,
  manifests, caches, gates and negative verdicts; unrelated user changes.
- Arora replicates 3/4; SIRLOIN NucLibC replicates 3/4 and NucLibB outcomes.
- The 22 context-calibration confirmation groups and unused calibration rows.
- Any frozen new-research inputs, definitions or outputs; use separate records
  for later diagnostics. No spending or scheduled tasks.

## Confidence gaps

The limiting gaps are independent compatible validation, biological replication,
complete gene-family isolation, raw-count semantics, and a specific contribution
not already covered by prior work. Current numerical positives are real outputs
of the declared analyses, but do not establish generalization to minimal edits,
endogenous transcripts or unseen cell types. No new user permission is needed
for the next free computational steps, and no STS placement can be inferred.

Primary literature: [Ron and Ulitsky 2022](https://www.nature.com/articles/s41467-022-30183-0),
[DeepLocRNA 2024](https://doi.org/10.1093/bioinformatics/btae065),
[Wen et al. 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC12962856/),
[Yin et al. 2020](https://www.nature.com/articles/s41586-020-2105-3),
[official SEERS repository](https://github.com/gao-lab/SEERS).
