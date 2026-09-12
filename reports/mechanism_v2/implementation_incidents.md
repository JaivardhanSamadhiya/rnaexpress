# Mechanism-v2 implementation incident ledger

## Report-writer KeyError on compact N0 evidence — post-score formatting only

After the frozen outer evaluation, controls, transfer, uncertainty, probes and
seed replication had all completed and `final_verdict.json` had been written,
`report` failed while formatting `controls_and_necessity.md`. The N0 geometry
baseline is recorded as identically zero gain against itself and intentionally
omits the full `paired_evidence` decision-count field. The markdown row helper
assumed every eligible evidence object carried `decisions`, raising `KeyError`.

No score, model, gate threshold, split, recipe or evidence digest was changed.
The report helper now tolerates compact eligible evidence, a regression test
covers that case, and report assembly may finish from the already-written
verdict JSON when evidence digests still match. The outer freeze continues to
refuse any change that would alter evaluation code before scores exist.

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
