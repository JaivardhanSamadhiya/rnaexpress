# RNAddress v4 Phase B representation benchmark

## Frozen comparison and decision

The outcome-blind benchmark cohort and model procedure were frozen before these metrics were calculated. The cohort contains every one of the 445 eligible decision sets, capped at 64 candidates per set by deterministic hash and round-robin edit-band coverage: 18,393 assay rows representing 12,495 unique parent-mutant pairs. Held biological units were assigned to deterministic five-fold splits; all variants and outcomes from a held gene or exact parent sequence remained outside training. Moffatt labels with identical exact parent sequence were co-held. Scaling was fit on training rows only. Training and selection weights equalized source, biological unit, decision set, and candidate count.

The matched downstream learner was `StandardScaler + Ridge(alpha=100)`. Both directions were evaluated separately. The prespecified selection score was the equal-weight mean of directional rank percentile and selected normalized utility (`1 - normalized regret`) over the three sources and two directions.

| Representation | Directional rank | Selected normalized utility | Frozen selection score |
|---|---:|---:|---:|
| 3UTRBERT | 0.6237 | 0.6135 | **0.6186** |
| SpliceBERT | 0.5809 | 0.5949 | 0.5879 |

The difference is 0.0307, larger than the frozen 0.01 tie margin. **3UTRBERT is therefore selected for every definitive Phase B model.** This is a new v4 development-only result and does not rely on the historical N-zip representation comparison.

## Source- and direction-specific results

| Representation | Source | Direction | Biological units | Rank percentile | Normalized regret | Good@1 | Good@3 | Good@5 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 3UTRBERT | Mikl | increase | 189 | 0.5213 | 0.4673 | 0.0635 | 0.1984 | 0.3095 |
| 3UTRBERT | Mikl | decrease | 189 | 0.4923 | 0.5279 | 0.0661 | 0.2328 | 0.3254 |
| 3UTRBERT | TDP-43 | increase | 16 | 0.5916 | 0.3059 | 0.1875 | 0.3125 | 0.5000 |
| 3UTRBERT | TDP-43 | decrease | 16 | 0.7391 | 0.3793 | 0.1875 | 0.2500 | 0.4375 |
| 3UTRBERT | Moffatt | increase | 8 exact-sequence units | 0.6478 | 0.4450 | 0.0760 | 0.2399 | 0.3244 |
| 3UTRBERT | Moffatt | decrease | 8 exact-sequence units | 0.7499 | 0.1936 | 0.3298 | 0.4804 | 0.5478 |
| SpliceBERT | Mikl | increase | 189 | 0.4961 | 0.4686 | 0.0820 | 0.2354 | 0.3492 |
| SpliceBERT | Mikl | decrease | 189 | 0.5209 | 0.5071 | 0.0820 | 0.2460 | 0.3757 |
| SpliceBERT | TDP-43 | increase | 16 | 0.5569 | 0.3355 | 0.2500 | 0.4375 | 0.4375 |
| SpliceBERT | TDP-43 | decrease | 16 | 0.6531 | 0.4349 | 0.1875 | 0.3125 | 0.3750 |
| SpliceBERT | Moffatt | increase | 8 exact-sequence units | 0.5227 | 0.4666 | 0.0992 | 0.3127 | 0.3583 |
| SpliceBERT | Moffatt | decrease | 8 exact-sequence units | 0.7357 | 0.2175 | 0.3133 | 0.5036 | 0.5452 |

The selected representation is not uniformly strong. Mikl held-gene ranking is close to chance in this simple comparator, especially for decrease. The aggregate win is driven by clear TDP-43 and Moffatt signal and a large Moffatt-increase advantage over SpliceBERT. This benchmark selects a contextual representation; it does not itself pass the definitive compiler gates.

## Feature construction and integrity

For each exact pair the frozen encoder produced parent absolute, mutant absolute, and contextual intervention-delta blocks. The delta includes global, edited-region, and radius-10 local changes aligned to the exact modified positions. Each semantic block was projected independently to 128 dimensions with seed 41017. Explicit operation geometry was then appended. No sequence was silently truncated.

- 3UTRBERT: `yangheng/3utrbert`, revision `220d80829deb077d1d640463a4267a96e9e70b1d`; local checkpoint SHA-256 `7aca71823ab74771006be1030d9e7239220bba40a16858575929a02e6d2a7471`; benchmark cache SHA-256 `a44e52f6c666454f3804d605db0dda0f71f9d42f23ccef042e2f0ed9397b2396`.
- SpliceBERT: official `SpliceBERT.1024nt`, Zenodo archive 7995778; local checkpoint SHA-256 `2ad91428c318e6c49233154073ca7a35f5f7899c9f4be3444775bae3dba0149d`; benchmark cache SHA-256 `bd154827420d5b36fa19108839b794cd27edcbae006023db257da1ce3ab56880`.
- RiNALMo was prospectively excluded before results: the official model is approximately 650 million parameters, this host has no CUDA/GPU and no pinned local checkpoint, and CPU extraction would not be operationally comparable. This is a computational exclusion, not evidence against RiNALMo.

N-zip outcomes were not used. Astrocyte outcomes and labels were not opened. The machine-readable predictions, set metrics, aggregate metrics, cache identities, and selection record are under `results/v4_phaseB/`.
