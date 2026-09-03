# FinalShot frozen RBPNet output-space representation

Reconstruction date: 2026-09-02

Protocol commit: `30c89a3`

Implementation/technical-clarification commit: `ac0443e`

## Result

The outcome-blind RBP representation reconstruction completed successfully for
all 103 official RBPNet HepG2 checkpoints. It covers 62,665 certified v4
interventions and 72,998 exact unique sequences: 17,567 are 150 nt and 55,431
are 260 nt. No sequence was padded or cropped.

This is the fallback authorized prospectively after the resource audit showed
that no released Parnet checkpoint matches the published Parnet architecture.
Parnet output-space and hidden-embedding representations remain excluded and
will be reported as not evaluated.

## Frozen software and checkpoints

- RBPNet repository commit:
  `8ee000dcdb897e0eeed6a46a855604299e914ca7`;
- package version: `0.10.0`;
- official 103-checkpoint archive SHA-256:
  `dc182e51d7b3ffe046ec7de56ab7e98a9ec0bd2f789d8e6bd61168b3718c355d`;
- runtime: Python 3.11.9, TensorFlow 2.15.1, TensorFlow Probability 0.23.0,
  `igrads` commit `a19c5e2aaa323d001389f9e6a6d2d3cfd05001d2`;
- individual model hashes: `results/finalshot/rbpnet_checkpoint_manifest.csv`.

OpenVINO 2026.3.1 was tested outcome-blind on QKI and rejected before the full
run because its measured throughput was about 98 sequences/second versus about
350 sequences/second for TensorFlow. TensorFlow graph/XLA execution did not
improve throughput. The official TensorFlow implementation was therefore used.

## Output interpretation

For every exact sequence and checkpoint, the protein-specific target-profile
logits were transformed with positional softmax. The serialized mixing head is
an unconstrained logit; it was transformed with sigmoid exactly as in official
`rbpnet.prediction._to_probs`. A first full-cohort QKI pilot intentionally
failed closed when raw mixing logits exceeded `[0,1]`; it wrote no shard. The
official sigmoid interpretation was documented and committed before the
successful cache and before localization evaluation.

The exact nine summaries per RBP are:

1. signed target-profile delta in the edit span plus/minus 10 nt;
2. signed delta in the edit span plus/minus 25 nt;
3. signed delta in the edit span plus/minus 50 nt;
4. maximum absolute delta in the plus/minus-25-nt region;
5. global binding probability gained;
6. global binding probability lost;
7. parent target-profile mass in the plus/minus-25-nt region;
8. sigmoid-transformed parent mixing coefficient;
9. mutant-minus-parent transformed mixing coefficient.

The R2 mechanistic block is therefore 927 dimensions before geometry. M1 uses
all 103 channel groups. M2/M3 may expression-condition only the 98 channels
with the frozen canonical mouse mapping; the other five remain valid sequence
features but receive no fabricated trans value.

## Cache and integrity

Profiles are keyed by exact ASCII-sequence SHA-256 and checkpoint SHA-256. The
ignored resumable cache contains:

- 103 profile shards, 8,345,967,842 total bytes;
- 103 intervention-feature shards, 258,352,634 total bytes;
- a deterministic sequence index and intervention index.

The tracked machine manifest is
`results/finalshot/rbp_signature_manifest.json`. It records every ignored cache
path and SHA-256, checkpoint hash, inference duration, normalization error,
mixing range, and conservation error. An independent post-run pass rehashed all
206 shards (8.60 GB); all hashes matched. Every feature shard has shape
`62,665 × 9`, complete feature-row order, identical feature names, and finite
values.

Across checkpoints:

- total checkpoint inference time: 23,004.86 seconds (6.39 hours);
- median checkpoint inference time: 218.69 seconds;
- maximum target-profile normalization error: `3.58e-7`;
- maximum absolute global signed-delta error: `4.77e-7`;
- maximum gain/loss conservation error: `5.36e-7`;
- transformed mixing range: `8.73e-27` to `0.9973883`.

The maximum values slightly above one in parent local mass (`1.0000002`) are
floating-point summation tolerance, not probability-model failure.

## Biological limitations

All models were trained on human HepG2 eCLIP. Applying them to mouse reporter
sequences is cross-species prior inference, not validation of calibrated mouse
binding. Critical absent channels include TARDBP, ELAVL-family, MBNL-family,
PUM1/2, FMR1, FXR1, and IGF2BP2. In particular, FinalShot cannot claim direct
TDP-43 binding prediction. The model can only test whether the available RBP
regulatory-state perturbations add transferable information.

No localization outcome was read by the reconstruction script. N-zip outcomes
and all Astrocyte data remained untouched. This report establishes a valid
mechanistic feature layer; it makes no performance or GO claim.

## Frozen matched-head representation result

After the representation and benchmark implementation were committed, all
three preregistered representations were evaluated with identical five-fold
biological holdouts, hierarchical weights, within-training-set effect midranks,
and `StandardScaler + Ridge(alpha=100)` heads. There was no unit overlap in any
fold and every one of 93,208 rows received one held-out score.

Equal-weighted over three sources and two directions, relative to R0 geometry:

| representation | rank ContextValue | regret ContextValue | positive rank tasks | positive regret tasks |
|---|---:|---:|---:|---:|
| R1 3UTRBERT | +0.03316 | +0.03114 | 5/6 | 6/6 |
| R2 RBPNet output space | **+0.04379** | +0.02514 | **6/6** | **6/6** |

R2's rank increment is larger than R1's, while R1's regret increment is larger.
This is the first evidence in the project that the frozen RBP output space has
broad incremental held-unit value: R2's rank and regret gains are positive in
every source×direction task. The smallest R2 gains are still positive (Mikl
decrease rank `+0.01513`; Mikl decrease regret `+0.01297`). The largest rank
gain is Moffatt increase (`+0.12953`).

This benchmark passes the numerical magnitude of Gate A, but it is **not a
FinalShot verdict**. It is within-source biological holdout using a matched
Ridge head. The required sparse M1/M2/M3 evaluation, distributed-unit checks,
Mikl matching, leave-source-out, cell/reporter transfer, 2-10-nt bridge, and
mechanism-breaking controls can still invalidate the hypothesis.

Machine outputs are `representation_benchmark.json`,
`representation_predictions.csv.gz`, `representation_set_metrics.csv.gz`,
`representation_unit_metrics.csv`, `representation_source_metrics.csv`,
`representation_context_values.csv`, and `representation_fold_audit.csv` under
`results/finalshot/`.
