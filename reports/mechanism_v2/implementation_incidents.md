# Mechanism-v2 implementation incident ledger

## Missing gene sentinel — pre-model forensic probes

The first probe grouping treated literal `missing` as a shared gene identifier,
joining unrelated Moffatt units. It was detected by inspection of full component
membership, before any Mechanism-v2 localization model fitting. All first-run
probe artifacts remain preserved with an explicit withdrawal record; corrected
results occupy `forensics/probes_v2`. Regression tests cover missing sentinels.

## Absolute-allele cache reader — sequence digest encoding

The first absolute-RBP-summary extraction stopped before producing a shard:
the archived sequence digests are NumPy `S64` byte strings, while reconstructed
digests were `U64` Unicode strings. Direct `array_equal` rejected them despite
identical digest contents. Fresh inspection verified every normalized digest
and length equals the expected order in the first shard, whose file hash passed.

The fix explicitly admits only S64/U64 arrays, validates every 64-character
lowercase hexadecimal digest, and then compares decoded contents and lengths.
Malformed or reordered digests still fail. A regression test covers both
encodings and rejects malformed values. No pre-fix predictions or absolute
feature shards existed; no scientific result is being overwritten or rerun.
The original RBP cache is untouched. Subsequent extraction still rehashes every
source shard and checks reconstructed deltas against the frozen signed matrix.
