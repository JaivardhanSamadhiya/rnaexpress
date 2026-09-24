# Computational contribution review, 24 September 2026

AI-authored technical synthesis of existing records, not competition-submission
prose. No new data, outcome access, search, fitting or biological sequence design.
The student must independently assess, reproduce and interpret the work.

**Recommended centerpiece: a reproducible benchmark for choosing measured,
composition-preserving six-mer swaps, with raw-count reconstruction, competitive
short-motif controls and explicit transfer limits.** This is the strongest result
aligned with the original small-edit objective. The contribution currently rests
on the decision formulation, controlled evaluation and provenance work; neither
a novel predictor nor a novel biological mechanism is established.

The strongest numerical support is within SRLE. Fixed swap choices over 592
parents in 60 composition classes improved normalized regret over uniform choice
by 0.231 and 0.253 in the two reconstructed constituent replicates. Their intervals
were [0.164, 0.289] and [0.196, 0.307]. However, ordinary 1-3-mer features also
improved regret by 0.220 and 0.221; the pair-model advantage over that comparator
was uncertain in both replicates. At the prediction level, error reduction beyond
composition was 27.04% for the pair model and 27.37% for short-motif counts.
The defensible finding is useful sequence-order information in this measured
landscape, not superiority of interaction modeling. Directed assay changes were
modest, about 0.12 log2-score units for the pair model.

| Evidence track | Supported narrower conclusion | Strong comparator and inference boundary |
| --- | --- | --- |
| SRLE composition-preserving swaps | Fixed choices show benefit over uniform selection and consistency after raw reconstruction. | Short-motif counts perform similarly. Aggregate training labels already incorporated these experiments; the raw work is an independent implementation, not independent biological validation. Candidate neighborhoods overlap. |
| Context calibration | Reused-source diagnostics suggest other-context information helps relative to a target-only kmer fit at 64 attempted labels, even after nested regularization. | Tuned-stack gain over tuned target-only was 0.04525 [0.02282, 0.06626], but gain over an uncalibrated sibling-context source was 0.01112 [-0.00320, 0.02617]. Calibration necessity is unestablished; original discovery failed. |
| Four-context robust selection | Sequence-based policies can beat uniform choice on the declared worst-context rank objective in reused-source evaluation. | Maximin regret 0.40564 versus simple averaging 0.37745; maximin-minus-averaging benefit -0.02819 [-0.06382, 0.00537]. The all-comparator criterion failed. This does not demonstrate consistent top-quartile control. |
| Faraway configuration selection | A secondary, frozen policy assessment retained benefit over uniform choice at an 8-hour collection. Quadratic and categorical policies gained 0.07159 and 0.05814 with positive descriptive intervals. | Additive introns had numerically lower regret, 0.42484, than quadratic 0.42841 or categorical 0.44186. The primary sequence-interaction gate failed. The secondary result establishes neither complexity superiority nor new-construct generalization. |

Faraway is an independently produced public study relative to SRLE, but it tests
a different intervention and is not a replication of six-mer swap selection.
Its 8-hour target contains 207 genotypes already present in its earlier collection:
162 training and 45 development genotypes. It is repeated collection/time transfer
within one study and protein context. Reconstructed insert exons match within
panels, but expressed 3-prime UTR barcodes differ; most target genotypes have only
one barcode. Intron identity, length and placement are bundled. The quadratic
policy's measured directional gains were approximately 2% and 5% geometric
ratio changes, not a 7% biological localization change. Keep the count-selection,
time-label and raw/processed correspondence limitations visible.

All cited intervals are descriptive group-resampling intervals with their stated
dependence and training-uncertainty limitations. None is evidence of independent
confirmation of the full proposed method. The negative Arora transfer result
(-0.146 regret gain against A/G, interval [-0.232, -0.060]) directly limits a
cross-compartment generalization claim. Failed gates and closed confirmation sets
remain unchanged; a favorable secondary analysis cannot reverse them.

**Claims to exclude:** complete novelty; first sequence-based RNA localization
design; superior pairwise/interaction or maximin methodology; causal intron-position
effects; identical complete mature transcripts in Faraway; general control of
endogenous transcripts, new genes or cell types; therapeutic utility; finalist-level
competitiveness. The existing prior-art review identifies earlier motif prediction,
pairwise RNA models, context dependence, intron-position analysis and designed
localization constructs. No new novelty search was performed here.

Consolidate these as separately scoped benchmark tasks, preserving their different
endpoints and units; do not pool them into one success rate or biological effect.
The unresolved priority is an authoritative sequence-to-measurement chain and an
independent compatible validation of the same decision task, followed by a precise
prior-art comparison. More complex modeling is not currently the missing evidence.

Sources: `checkpoint_20260921.md`, `checkpoint_20260922.md`,
`faraway_and_robust_context_checkpoint.md`, and `novelty_and_claims.md` in this
reports directory. This synthesis does not incorporate subsequent unreviewed
provenance results or change any original specification.
