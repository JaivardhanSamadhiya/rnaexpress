# A full-roster metadata route that does not reopen CORE

The initial readiness record identified a missing C: full-roster metadata
bundle. A concrete alternative is now implemented as a pure stream parser;
eight invented tests pass. No actual archive or CORE table has been opened.
This supplements, and does not rewrite, the frozen scalar-core readiness.

The existing frozen four-column row index defines candidate order. The existing
replicate-measurement archive repeats each candidate's ID, dataset, component,
context, parent/mutant alleles and feature-row index. These metadata fields can
be joined exactly without loading CORE, numerical feature values or numerical
replicate values. The historical source writer was inspected to establish this
route; archive schema/content identity is still unmeasured.

The future caller must admit exactly:

- `results/generalization_20261007/row_index.csv.gz`, historical SHA-256
  `0f343712dfc90abd1c6033f29f10e3eef63c1e7977a7fef9ef5c5ee6680fc58f`.
- `artifacts/probabilistic_ranking_20260928/replicate_candidate_measurements.csv.gz`,
  historical SHA-256
  `593505e5112e2b06b397af8c66c4f7505bf271777e9759886d97c6177a3c4172`.

These are declarations from historical frozen manifests, not freshly verified
input bytes. Both paths were found by file metadata on D:, absent on C:. A
future resource-gated owner must verify exact compressed bytes, traverse to
EOF, enforce decompression bounds, pin actual origins and durably close before
any returned bundle can become admitted. No such worker was launched here.

`parse_streams` accepts supplied text streams only. The row index must contain
exactly the four outcome-free fields. Feature-row positions must be dense and
match that index's ID/study/context/component order. Repeated candidate metadata
must be identical, and each recorded replicate slot/ID must match the source
writer's fixed catalog: Astrocyte 14, Mikl 3, Moffatt 4, SRLE 2. Missing, duplicate
or unexpected slots reject. Slot counts are metadata consistency checks, not
claims of independent biological replication or finite measurements.

The actual future admission must fix 26,258 candidates: Astrocyte 3,984,
Mikl 13,781, Moffatt 6,749, SRLE 1,744. The corresponding declared archive has
127,603 records. The pure parser accepts smaller counts for invented testing;
that is not a way to admit a reduced actual cohort. It validates metadata via
the existing six-field comparison contract and returns no numerical outcomes,
features or fit authority.

CSV tokenization traverses unused outcome strings. This is explicitly not
annotation-only byte I/O. Tests deliberately supply nonnumeric and quoted
multiline outcome fields; parsing succeeds without numeric conversion or
returning those fields. No actual reserved replicate is accessed: rejection
tests use invented aliases only.

The eight tests cover full four-assay recovery, ID/index mismatch, changed
repeated alleles, unexpected replicate aliases, missing/duplicate records,
invalid feature positions, duplicate headers/count mismatch, and an outcome
column illicitly added to the metadata-only row index.

This solves the source-design part of the metadata gap. It does not solve the
aggregate-label gap. The archive's constituent measurements must not be
averaged as a substitute for the original aggregate endpoint, particularly
because Moffatt's paired contrast values are missing in this admission. Sampled
pair differences likewise cannot silently substitute for the full endpoint or
its absolute-zero harm semantics. Exact aggregate-label access remains a
separate unresolved prerequisite.

The original resource gates, known-cell single-attempt scope, old freezes and
33 user modifications remain unchanged. No array/label admission, native
scientific import, optimizer, drive repair, paid resource or scheduled task
occurred. The completed known-cell verdict remains NO-GO.
