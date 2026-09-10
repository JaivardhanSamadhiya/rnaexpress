# Local structure delta features

Status: full outcome-free extraction completed and independently hash-verified.

ViennaRNA 2.7.2 uses Turner 2004 parameters, 37 °C, dangles=2 and noLP=0. The
native library SHA-256, complete configuration and input sequence digest define
each cache key. A transactional SQLite cache stores finite feature values with
payload hashes. Completed cache entries are checked before reuse. Full extraction
uses three worker processes; it never reads localization outcome columns.

For each intervention, the edited span is expanded by ±20, ±50 and ±100 nt and
clipped to each allele's boundaries. Equal-length assay edits use direct aligned
coordinates. Indels use a deterministic global minimum-edit alignment with an
explicit tie convention and independent half-open reference/mutant intervals.
Repetitive indels can admit alternative valid alignments; this coordinate choice
is not a claim about mutation history. An insertion-only reference edit interval
is anchored at the consumed-base boundary, not an invented reference nucleotide.

Each local sequence produces six summaries: MFE/nt, ensemble free energy/nt,
mean marginal unpaired probability, mean nucleotide partner entropy, mean base-
pair distance/nt, and MFE paired fraction. Each feature is mutant minus reference,
giving 18 columns in radius-major order. Extensive energy is normalized by the
allele window length. Window length and geometry are not appended to the block.

The probability summaries use a symmetric base-pair matrix and include the
unpaired state in entropy. Marginal unpaired probability is **not** the joint
probability that an entire motif is accessible. These features describe an
equilibrium local folding prior, not measured intracellular structure. A full
motif-accessibility block would require additional justified calculations.

Tests cover known hairpin behavior, a non-pairing homopolymer, exact repeated
inference, finite probabilities, paired delta arithmetic and insertion/deletion
boundaries. The pilot completed 729 distinct windows and wrote a hashed manifest.
This proves the extraction path runs, not that structure improves localization.
The full extraction completed all 212,979 unique windows and produced a finite
62,665 × 18 float32 array, SHA-256
`d8a33188a89dbfd7adb9c236323cc242bbf699d4121e9ddf2c30be2edbc19f90`.
Window/model selection and biological necessity remain untested.
