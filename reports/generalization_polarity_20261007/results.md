# Fixed endpoint polarity results

**NO-GO under the unchanged generalization gate.**

The known endpoint orientation lowered equal-assay macro normalized regret from 0.512255 to 0.473306. The incremental gain is 0.038949, with a descriptive shared-component interval [0.022053, 0.057139]. Three assays improve; Moffatt worsens. Uniform expected regret is 0.5.

| held assay | matched unflipped | fixed polarity | regret improvement | polarity avoidable wrong |
| --- | ---: | ---: | ---: | ---: |
| Astrocyte | 0.557162 | 0.477775 | +0.079388 | 0.500000 |
| Mikl | 0.515635 | 0.474277 | +0.041358 | 0.182099 |
| Moffatt | 0.445513 | 0.471880 | -0.026367 | 0.541667 |
| SRLE | 0.530709 | 0.469291 | +0.061418 | 0.228041 |

Failed unchanged criteria: `each_avoidable_harm_at_most_0_05_vs_both`, `macro_regret_at_most_0_468`, `three_assays_gain_vs_H0_at_least_0_01`.

This supports endpoint alignment as a development hypothesis, without establishing reliable four-assay generalization. The orientation is fixed from known endpoint metadata; no sign or penalty was selected using an outer assay outcome. For held SRLE, projection-only training is identical across arms and the nuclear scores are exactly inverted. Endpoint class remains confounded with source; cytoplasmic export and distal transport are different biological quantities.

Independent verification passed for 80 checkpoints, including 72 inner validation replays, 52,516 candidate scores and 21,744 decisions. Maximum score error was 0. All 33 preexisting modified files and the older evidence bundles were preserved.

A separately frozen factorial follow-up may test the fixed alignment with the already declared structure and encoder features. It must retain matched unflipped controls and the original strict gate; this result does not authorize changing a failed threshold. All comparisons use repeatedly exposed development data, and no independent biological confirmation or calibrated benefit probability is claimed.
