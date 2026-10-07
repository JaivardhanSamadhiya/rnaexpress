# Representation feasibility, 7 October 2026

This is a prospective development design, informed by exposed historical
failures. It does not withdraw any old numerical result, certify its scientific
interpretation, or claim untouched validation. No biological fit was run during
this review. The new runner must freeze code, data hashes, splits, grid, and
evaluation rules before any new biological fitting.

## What is locally available

The current admitted roster has 26,258 rows and 18,220 unique available alleles:

| study | rows | available sequence length |
| --- | ---: | ---: |
| Astrocyte GSE330741 | 3,984 | 190 nt |
| Mikl GSE173098 | 13,781 | 150 nt |
| Moffatt GSE334718 | 6,749 | 260 nt |
| SRLE | 1,744 | 6 nt |

This inventory used only dataset and parent/mutant sequence columns of the
already-admitted `results/probabilistic_ranking_20260928/candidate_index.csv.gz`.
SRLE's six bases are an insert, not an entire HBB reporter. Available-sequence
features must not be described as full biological context. No present allele
exceeds the local 3UTRBERT checkpoint's 512-position limit.

The original `interaction_3` has 246 columns: metadata, overlapping 1--3-mer
mutant-minus-parent counts, and products between composition change and local
parent mono/dinucleotide frequencies. An expanded frequency window cannot
restore ordered motif identity. The old full-window interaction comparison was
negative. Older Mechanism-v2/v3/v4/v5 studies also tried rich RBP/BERT/structure
stacks, nonlinear estimators, or longer k-mers under different targets and data
rosters; adding an undifferentiated stack would not be a clean new hypothesis.
Their conclusions that no higher-order signal can be recovered go beyond what
those specific finite experiments logically establish.

Existing free local resources:

- SciPy 1.14.1 and scikit-learn 1.5.2 in the mechanism-v2 runtime.
- ViennaRNA 2.7.2, including the native CPython 3.12 Windows module.
- 3UTRBERT checkpoint at
  `data/external/3utrbert/yangheng-3utrbert/pytorch_model.bin`, 346,827,305 bytes,
  SHA-256 `7aca71823ab74771006be1030d9e7239220bba40a16858575929a02e6d2a7471`.
  Architecture: 12 layers, 768-dimensional states, 512 positions.
- The admitted frozen pooled BERT cache covers 20,474 core rows: 13,725 Mikl and
  6,749 Moffatt. It covers neither Astrocyte nor SRLE. Prior provenance records
  mixed Torch/OpenVINO inference and inherited equivalence limitations.
- Archived mechanism-v2 local structure summaries and motif accessibility
  caches. Exact row/sequence/hash coverage needs a new read-only join; no
  positional row assumptions and no changes to the immutable caches.

## Route A: exact ordered motif differences, ready to run

Question: does the three-base cutoff discard transferable local sequence
information? The SRLE paper explicitly screens six-base elements, and the
Moffatt study reports multipartite elements with both order-sensitive and
composition-sensitive subsequences. These findings motivate the comparison;
they do not establish that a universal coefficient vector exists.
Sources: [SRLE study](https://pubmed.ncbi.nlm.nih.gov/42179915/),
[Moffatt preprint](https://pubmed.ncbi.nlm.nih.gov/42327238/).

The implemented API in `src/generalization_20261007/route_representation.py`
adds all exact overlapping mutant-minus-parent 4-, 5-, and 6-mer counts to the
same 246 baseline columns, producing 5,622 columns. Only start positions whose
motif overlaps a substitution are counted. This optimization is mathematically
equal to subtracting full-sequence counts. The representation remains sparse
and supports every admitted row, including SRLE's available six-base insert.
It does not encode longer-range motif spacing or unknown reporter flanks.

Use the same historical sampled pair roster, source/component/context weights,
linear latent utility, training-only pair RMS scaling, and optimizer as the
matched route-A baseline. Three frozen L2 values are 0.005, 0.05, and 0.5,
selected using source-only inner holdouts. The held assay never selects a
penalty. Training-unsupported columns receive coefficient exactly zero.

Controls: identical 246-column model with pair RMS scaling and the same penalty
grid; AU/composition and uniform comparators; same candidate IDs, component
purge, directions, and outcome estimators; explicit per-study and per-component
results. A training label permutation or whole-intervention bijection can be
added only if frozen in the common design before fitting. Random column
renaming is not a valid necessity test of a freely learned linear ranker.

Eight scoped synthetic tests pass: brute full-count equivalence, antisymmetry,
unchanged distant flank invariance, count/schema checks, bad-input rejection,
loss-gradient correctness, dense/sparse optimization parity, and cancellation
of parent-constant features. No biological outcomes are loaded by these tests.

Compute estimate, not a benchmark: extraction is linear in the number of edits
times motif length and should take seconds to a few minutes for this roster.
Sparse storage avoids a 1.18-GB dense float64 allele matrix and another large
pair matrix. Fitting should be minutes per source-fold comparison on local CPU;
measure the first frozen job and record actual time rather than guaranteeing
an end time. No data download or spending is required.

## Route B: consistent frozen contextual BERT, prepared conceptually

Question: does the existing pretrained comparison miss transferable contextual
information because of limited source coverage, pooling, or backend differences?
The original [3UTRBERT paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC11497048/)
describes frozen contextual embeddings and downstream localization prediction.
The [official repository](https://github.com/yangyn533/3UTRBERT) publishes
checkpoints and feature-extraction code under MIT. This is a reusable resource;
its published results are not small-edit held-assay validation for this project.

First freeze one checkpoint, tokenizer, inference backend, and equal padding
convention. Audit token alignment and batch-padding invariance on synthetic
sequences and compare Torch/OpenVINO on the same sequence and batch before
admitting either backend. Run identical paired alleles through a single backend;
extract fixed CLS, global, affected-token, and radius-10 contextual differences.
Apply an outcome-blind fixed projection, or PCA fit only to training alleles.
Do not reuse a mixed-backend vector as if it were newly verified.

Compare matched pair-RMS baseline, baseline plus contextual difference, and
baseline plus pooled allele difference on complete four-core coverage. Preserve
the three-penalty source-only selection and same ranking/evaluation rules.
Absolute parent-only embeddings are a named control; they cannot alter ranking
within a parent unless used in a declared edit interaction. No encoder
fine-tuning, target-label calibration, or sign flipping is part of this route.

All currently supplied sequences are native-length eligible, but encoding SRLE
six-mers still does not provide the HBB reporter context. The missing rows for
new inference are at least 3,984 Astrocyte, 1,744 SRLE, and 56 Mikl. A uniform
backend re-extraction may require every unique available allele. CPU extraction
could range from hours to days; this estimate needs a synthetic timing probe.
The already-local checkpoint avoids download costs. Do not download a much
larger RNA encoder before local inference and equivalence are demonstrated.

## Route C: motif accessibility in reconstructed available context

Question: is ordered motif accessibility, rather than global folding summaries,
the missing context variable? ViennaRNA's
[RNAplfold manual](https://www.tbi.univie.ac.at/RNA/ViennaRNA/doc/html/man/RNAplfold.html)
documents local unpaired-stretch probabilities useful for possible binding
sites, with O(n L squared) time and O(n plus L squared) memory. A probability
that an entire motif is unpaired is not the product of single-base unpaired
probabilities.

Freeze one local partition window and one maximum pairing span before fitting.
For each fixed 4--6-mer, sum its motif-specific unpaired-stretch probability in
each allele and take mutant minus parent. Compare base246 plus exact counts,
base246 plus accessibility-weighted counts, and their declared combination.
Record the count-only and structure-only controls; retain matched source-only
preprocessing and downstream capacity. Feature extraction accepts no outcomes.

This is distinct from the old six whole-window summary statistics. However,
full four-core physical-context coverage is currently incomplete: reconstruct
and provenance-check the actual SRLE reporter flanks before folding it. Until
then this route is eligible only for the three projection studies, with SRLE
explicitly missing; it cannot pass a four-study universality gate by zero filling.
The available 150--260-nt allele folding should fit local CPU resources, likely
hours rather than weeks with sequence caching, but needs a synthetic timing
probe and an exact-count cache inventory. No new external outcome is needed.

## Cross-route interpretation and limits

Context-conditional utility is biologically plausible: the
[linear/circular RNA study](https://pmc.ncbi.nlm.nih.gov/articles/PMC9072321/)
reports substantial differences between host-RNA forms and discusses splicing,
polyadenylation, transcript length, and protein interactions. With the current
core roster, SRLE is the only nuclear/cytoplasmic source. Its whole-study holdout
also holds out that endpoint class. A learned nuclear-specific head then has no
training support. Arbitrary assay IDs or a zero residual do not solve that
identifiability gap. A future contextual model must use externally defined,
available biological descriptors and enough independent training contexts.

Worst-source risk optimization, implemented separately by the shared experiment,
is a distinct objective route rather than a representation. The
[original group-DRO paper](https://arxiv.org/abs/1911.08731) motivates balancing
worst-group training loss with regularization, but offers no guarantee of
generalization to an entirely new biological mechanism. The three parallel
routes should therefore be reported with their controls and all failures.

All current four-core studies are exposed development data. A pass would be
development evidence and would still need a separately frozen untouched test.
N-zip outcomes, TDP EV5/quarantined stability, reserved SIRLOIN replicates 3/4
and NucLibB, reserved Arora/Shukla outcomes, historical frozen namespaces, and
unrelated user edits remain outside this work. No spending, scheduled tasks,
unfiltered pytest, or unsupported zero-filled context is authorized.
