# RNAddress FinalShot measurement-head randomization

The five fitted M3 head parameter blocks were reassigned with a deterministic
seed-42017 complete derangement. The shared latent scores were not recomputed
or modified. All 15 outer-fold/seed latent arrays had identical pre/post byte
hashes, so the pre-head ranking was bitwise unchanged as required.

| Calibration aggregation | Baseline MSE | Randomized MSE | Baseline Spearman | Randomized Spearman |
|---|---:|---:|---:|---:|
| Pooled held-out rows | 1.23272 | 1.78938 | 0.31724 | 0.06888 |
| Equal head macro-average | 0.87173 | 1.33770 | 0.15504 | 0.20490 |

Randomization clearly degraded pooled MSE and pooled Spearman, and degraded
equal-head MSE. It did not degrade equal-head Spearman. Under the strict
preimplemented audit requiring degradation in both pooled and equal-head views,
the control does not pass. The divergent Spearman result is interpretable:
each fitted head is monotone, so swapping heads chiefly disrupts cross-assay
offset/scale calibration rather than necessarily reversing within-assay ranks.
No post-result criterion was relaxed.

This control does not rescue M3: Gate J had already failed because more than
one leave-source-out task suffered regret worsening greater than 0.020 versus
direct M2.

No N-zip outcome was accessed and no Astrocyte outcome or sequence data was
accessed. The complete mapping and per-head diagnostics are archived in
`results/finalshot/measurement_head_randomization_summary.json`.
