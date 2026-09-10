# Outcome-independent delta representation

Status: complete cached development blocks; inner-only localization fitting has
started under a committed recipe freeze. Outer evaluation remains unexecuted.
The bounded Parnet audit did not recover an admissible paper-matching checkpoint.

The certified outcome-free table contains 62,665 interventions, with contiguous
`feature_row` identifiers. New cached matrices are tied to its exact file hash.
The 103-checkpoint RBPNet matrix and the 3UTRBERT matrix were rehashed before reuse.
No old cache was edited or re-inferred. Per-profile rehashing will be required if
those lower-level profiles are later consumed, but this stage consumes only the
already verified matrix. A subsequent separately recorded reconstruction verified
all 103 lower-level profile shards and produced paired absolute summaries for
negative controls; no profile was modified or re-inferred.

## RBPNet signed delta block

412 columns: for each of 103 human HepG2 tasks, signed mutant-minus-reference
target-profile mass within the edit span expanded by 10, 25 and 50 nt, plus the
mixing-coefficient difference. The old representation's parent mass, parent mixing,
absolute perturbation maximum, gained mass and lost mass are absent from this
primary block. Geometry is not concatenated into it.

Normalized probability profiles sum to one. Their total positive and negative
perturbation masses are therefore approximately equal; treating those as distinct
signed mechanisms would duplicate information. Symmetric magnitudes may be tested
as separately labeled comparators, not relabeled signed deltas. There is no TARDBP
checkpoint. These are human-trained sequence priors, not validated mouse binding.

## 3UTRBERT contextual delta comparator

The archived array has **384**, not 256, columns: 128 projected parent-absolute,
128 mutant-absolute and 128 contextual token-delta columns. Only columns 256–383
are extracted. Source-code inspection verified that the last block is projected
from reference/mutant token differences pooled over the sequence, edited region
and local neighborhood. It is not interchangeable with the mutant absolute block.
The same frozen encoder and fixed projection act on both alleles. Existing mixed
Torch/OpenVINO inference provenance and its equivalence limitations remain visible.

This contextual block is a general sequence prior, not an RBP-specific measurement.
It is kept separate so a future model comparison cannot falsely attribute all
sequence benefit to RBP mechanism. The committed primary grid instead uses the
128-column **pooled allele delta**, calculated as archived columns 128–255 minus
0–127. Both absolute blocks use the identical fixed-projection CLS+mean allele
function. This choice and the distinct contextual comparator were documented
before localization fitting in `model_selection.md`.

Both outputs and source-code/schema hashes are recorded under
`results/mechanism_v2/features/`. The primary loader does not admit source IDs,
parent IDs, outcome-derived features or sealed data as mechanistic inputs.

The pooled BERT and RBP signed delta blocks form M1 (540 columns). M6 adds local
structure, processing nuisance and motif/exposure deltas; M7 adds four externally
aligned trans interactions. All available cells map explicitly to CAD or N2A.
Only 98 RBP channels with eligible external measurements in both cells contribute
to trans interactions; five unsupported channels are omitted, not zero-filled.
The same 103 RBP checkpoints remain in the cis-delta representation.
