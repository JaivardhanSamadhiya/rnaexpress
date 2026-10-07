# Author-verified frozen encoder: resource and synthetic admission

No biological encoding or supervised fitting has run. The isolated runtime,
checkpoint identity, tokenizer, IR weight lineage, synthetic numerical checks,
and CPU feasibility were audited before full-core feature production.

The authors' [3UTRBERT repository](https://github.com/yangyn533/3UTRBERT) links
[Figshare release22847354](https://figshare.com/articles/software/Pre-trained_3mer_model/22847354),
a public free CC BY4.0 release. Its322,227,069-byte archive matches the published
MD5 `5ec828f9f3a58639af05545a611eac69` and actual SHA256
`9ee988021ae34168dfb06bb24950b090f1a86d8b47e213bdf7c5c60da01db325`.
The original checkpoint is byte-identical to the cached public community upload:
346,827,305bytes, SHA256
`7aca71823ab74771006be1030d9e7239220bba40a16858575929a02e6d2a7471`.
The community revision is220d80829deb077d1d640463a4267a96e9e70b1d.
The original weights require CC BY attribution; the GitHub code's MIT license
and community card's MIT tag are recorded separately. No downloaded code or
pickle was executed. Safe ZIP/storage hashes establish exact checkpoint identity.

The vocabulary, tokenizer configuration and special-token files are also
byte-identical. The only configuration difference is generation `max_length`
20→10, unused because encoding supplies explicit sequences and never calls
generation or truncation. The author vocabulary has64 overlapping RNA3mers plus
five special tokens. All synthetic tokenizer outputs match manual token IDs,
include CLS/SEP, and contain no unknown tokens.

The cached FP32 OpenVINO IR matches the exact hashes in the prior admitted
Torch/OpenVINO equivalence receipt: XML
`a7783057679ab1f4259e043c3c36e22bf8a9100dd20cd0ab2a0acc6809d29d34`,
BIN `63e177acf4dd90bff703cb67b719eae8f3ed2afb130f3399d46ead32980b4680`.
All197 nonscalar FP32 IR constants match original checkpoint storages directly
or after matrix transpose. This confirms constant lineage, not the entire
computation graph by itself. Fresh Torch equivalence was not rerun because this
bundled environment has no compatible Torch runtime; prior numerical support is
inherited and exact-hash pinned.

Only the new namespace was repaired. Official free Apache2.0
[OpenVINO2026.3.1](https://pypi.org/project/openvino/2026.3.1/) and
[Tokenizers0.19.1](https://pypi.org/project/tokenizers/0.19.1/) wheels were checked
against authoritative PyPI SHA256s and safely extracted into its runtime.
No system package, old runtime, model file or prior result was changed. The
initial tokenizer CPython3.12 incompatibility was recorded before repair. The
IR attention-mask input has both `attention_mask` and numeric `29` aliases;
the new encoder resolves explicit canonical names instead of `get_any_name()`.
No telemetry package was installed.

Ten synthetic edit pairs were tested at46/150/190/260nt. The46nt inputs use the
certified SRLE20+6+20 construction window, not a full mature HBB transcript.
Last-layer global means exclude CLS/SEP/padding. Changed-site pooling includes
exactly the overlapping3mers affected by any substitution, using corresponding
parent/mutant positions. Native1536-dimensional deltas were finite and nonzero.
Repeat error was0; mixed-length padding hidden error was2.05e-5 and native paired
feature error4.35e-6, both inside the fixed tolerances.

The follow-up benchmark grouped synthetic inputs by length and ran three fixed
timing repetitions for every setting. All hidden outputs equaled two-thread
singleton reference outputs exactly. One compiled model was alive at a time.

| Threads | Batch | Estimated core inference min | Observed RSS MiB |
|---:|---:|---:|---:|
|2|1|130.08|1009.54|
|2|4|127.62|1069.63|
|2|8|125.33|1113.36|
|4|1|74.85|1014.99|
|4|4|68.86|1073.43|
|4|8|65.37|1117.29|

The fixed production choice is four CPU threads and batches of eight within
length groups. Peak process working set was1131.01MiB. The estimate covers
18,220 unique available-context alleles:742at46nt,9318at150nt,3991at190nt,
4169at260nt. A20% planning margin gives78.44minutes before additional contention,
row assembly and IO. Concurrent structure workers can increase elapsed time.
No additional model replica is permitted.

Production uses two independent Gaussian768×128 matrices, NumPy default_rng
seed20261007, global then local order, float64 draws/division bysqrt128 followed
by float32 storage. Exact matrices and hashes are saved before extraction. The
256-column BERT block and matched vocabulary-ordered one-hot lookup block use
the same matrices, positions and pools; each lookup pool has information rank
at most64. Only projected global vectors and requested projected token positions
are cached in immutable256-allele shards, with a hash-verified resume path.

Four synthetic analytic tests passed: projection commutes with pooling; no-edit
zeros and edit reversal; exact one-hot control; boundary/special-token handling.
The producer refuses to run before a committed feature-production manifest.
Full features and the separate comparative prefit manifest must precede fitting.
All four core assays remain development-exposed; pretraining sequence overlap,
unknown reporter context and inherited conversion limitations remain explicit.

Receipts: `bert_checkpoint_provenance.json`, `bert_tokenizer_ir_audit.json`,
`openvino_resource.json`, `tokenizers_resource.json`,
`bert_synthetic_benchmark.json`, `bert_synthetic_throughput.json`,
`bert_feature_spec.json` in the new results namespace. Large runtime, wheels,
original archive and compact inference caches are workspace resources, not Git
objects; their hashes preserve provenance.
