# Synthetic structure parallel benchmark and cache producer

Two and four spawned processes use one numerical thread each. Only the same forty synthetic alleles were folded. All three summary vectors and ensemble energies must be exactly identical to serial results. Worker imports need only NumPy and ViennaRNA; dense pairing matrices are transient and never persisted.

Current serial forty-allele time: 9.835 seconds. Production is fixed to two workers so another CPU representation route can run concurrently on the four-core machine.

| Workers | Wall seconds including spawn | Observed speedup | Summed worker peak MiB | Estimated full-core folding minutes |
|---:|---:|---:|---:|---:|
| 2 | 6.594 | 1.49 | 104.2 | 46.9 |
| 4 | 4.197 | 2.34 | 207.5 | 25.9 |

Timing estimates use ten alleles per length; they exclude per-file storage and validation overhead. They are planning estimates rather than runtime guarantees. Exact feature choices, context arms, and physics remain those in structure_config.json.

The producer stores one compressed NPZ per SHA-256 of the exact encoded sequence, under its configuration SHA-256 directory. Each contains only the exact sequence, identity/config hashes, three per-nucleotide summary vectors, and ensemble energy. Completed files are validated and skipped on restart. Writes use a temporary file and publish only after validation, preserving completed entries.

Core production requires the committed feature_production_manifest.json certificate pinning configuration, code, runtime, context metadata and core sequence input and protocol.md. Exactly26,258 rows/18,220 alleles, two workers, and one thread per worker are asserted by the producer. It reads only dataset/parent_sequence/mutant_sequence columns. Its command does no supervised fitting or full-core feature-matrix construction. Five accessibility-off motif deltas use identical masks/normalization with every weight1; correctedbase246+raw5+ensemble11 gives262 columns.
