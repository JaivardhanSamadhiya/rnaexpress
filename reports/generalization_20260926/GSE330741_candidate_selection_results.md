# Candidate-edit selection: promising secondary result

The frozen held-parent primary chose lower-regret edits than uniform choice for **all seven parents**, averaging both directions. Regret was **0.371947 [0.316664, 0.413107]**, versus simple baseline 0.488527 and uniform 0.500000. Wrong-direction selections fell from 8/14 for the simple baseline to **5/14** for the primary (uniform expectation 7/14). This is a predeclared secondary result; the failed rank-advantage primary criterion remains failed.

All external results use 3,984 verified SNPs, seven 190-nt parents, five nonoverlap components and two genes (Slc1a2 and Sparc). The author-retained design has 14 matched biological replicate labels (three-cortex pools), with 11–14 positive matched pairs per admitted variant. Technical sequencing lanes are not biological replicates. Intervals below are descriptive 95% component-bootstrap intervals, not evidence of thousands of independent biological contexts. Historical exposure is PARTIALLY EXPOSED.

Every QC-eligible SNP is ranked for each held parent. The 14 decisions per model are seven parents × two directions, not 14 independent biological experiments. Five nonoverlap components determine uncertainty. Predictions are formed without that parent's measurements in fitting or selection; no outcome-selected candidate subset or abstention is used. Ties use lexical element ID.

## All baselines and sequence models

| stage | model | regret | regret_ci_low | regret_ci_high | wrong_direction | best_recovery | top5_best_recovery |
| --- | --- | --- | --- | --- | --- | --- | --- |
| test_a | no_change | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 0.000000 | 0.071429 |
| test_a | srle_2mer_full | 0.446733 | 0.403957 | 0.488083 | 0.500000 | 0.000000 | 0.000000 |
| test_a | srle_2mer_order_only | 0.544295 | 0.506402 | 0.585848 | 0.500000 | 0.000000 | 0.000000 |
| test_a | srle_3mer_full | 0.557098 | 0.508152 | 0.587968 | 0.500000 | 0.000000 | 0.000000 |
| test_a | srle_composition | 0.478435 | 0.417382 | 0.545010 | 0.428571 | 0.000000 | 0.000000 |
| test_a | srle_delta_AU | 0.550335 | 0.504198 | 0.592236 | 0.500000 | 0.000000 | 0.071429 |
| test_a | srle_kmer123_full | 0.536383 | 0.467477 | 0.576958 | 0.500000 | 0.000000 | 0.000000 |
| test_a | srle_substitution | 0.478435 | 0.417382 | 0.545010 | 0.428571 | 0.000000 | 0.000000 |
| test_a | uniform | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 0.001757 | 0.008785 |
| test_b | delta1 | 0.522136 | 0.465770 | 0.604982 | 0.500000 | 0.000000 | 0.000000 |
| test_b | delta2 | 0.510240 | 0.457658 | 0.572881 | 0.500000 | 0.000000 | 0.000000 |
| test_b | delta3 | 0.502351 | 0.447659 | 0.547861 | 0.500000 | 0.000000 | 0.000000 |
| test_b | delta_AU | 0.550335 | 0.504198 | 0.592236 | 0.500000 | 0.000000 | 0.071429 |
| test_b | kmer123 | 0.502351 | 0.447659 | 0.547861 | 0.500000 | 0.000000 | 0.000000 |
| test_b | no_change | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 0.000000 | 0.071429 |
| test_b | position | 0.473052 | 0.438030 | 0.537338 | 0.500000 | 0.071429 | 0.071429 |
| test_b | simple_full | 0.488527 | 0.431504 | 0.538498 | 0.571429 | 0.071429 | 0.071429 |
| test_b | simple_full_delta2 | 0.371947 | 0.316664 | 0.413107 | 0.357143 | 0.000000 | 0.000000 |
| test_b | simple_full_delta2_delta3 | 0.485300 | 0.438009 | 0.528541 | 0.500000 | 0.000000 | 0.071429 |
| test_b | substitution | 0.470643 | 0.402839 | 0.544257 | 0.428571 | 0.000000 | 0.000000 |
| test_b | substitution_composition | 0.470643 | 0.402839 | 0.544257 | 0.428571 | 0.000000 | 0.000000 |
| test_b | substitution_position | 0.488527 | 0.431504 | 0.538498 | 0.571429 | 0.071429 | 0.071429 |
| test_b | training_mean | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 0.000000 | 0.071429 |
| test_b | uniform | 0.500000 | 0.500000 | 0.500000 | 0.500000 | 0.001757 | 0.008785 |

Uniform expectations are exact, not a lucky random seed. Averaging symmetric increase/decrease tasks makes uniform normalized regret exactly 0.5 and uniform wrong direction 0.5 when no candidate is zero. These values are not a universal single-direction biological baseline.

For B, paired regret gain versus uniform is 0.128053 [0.086893, 0.183336], exact block p=0.03125. Gain versus simple_full is 0.116581 [0.047518, 0.193414], but exact block p=0.0625. The positive bootstrap interval and non-significant exact comparison differ because only five blocks exist; report both. The prespecified candidate gate did not require this latter p-value, but that choice cannot justify a stronger confirmatory claim. Five of seven parents beat simple_full. The primary recovered no exact measured best edit, including within top-five shortlists (0/14 for both).

## Every frozen primary choice, including failures

| stage | parent_id | direction | selected | predicted_delta | observed_delta | regret | wrong_direction |
| --- | --- | --- | --- | --- | --- | --- | --- |
| test_a | slc1a2.1_3281_3381 | -1 | slc1a2.1_3281_3381_g96t | -0.326998 | 0.111657 | 0.532249 | 1.000000 |
| test_a | slc1a2.1_3281_3381 | 1 | slc1a2.1_3281_3381_t12g | 0.326998 | 0.325433 | 0.269661 | 0.000000 |
| test_a | slc1a2.1_3641_3721 | -1 | slc1a2.1_3641_3721_g82t | -0.326998 | 0.284810 | 0.652159 | 1.000000 |
| test_a | slc1a2.1_3641_3721 | 1 | slc1a2.1_3641_3721_t121g | 0.326998 | 0.365968 | 0.283893 | 0.000000 |
| test_a | slc1a2.1_3781_3841 | -1 | slc1a2.1_3781_3841_g130t | -0.326998 | 0.363614 | 0.546405 | 1.000000 |
| test_a | slc1a2.1_3781_3841 | 1 | slc1a2.1_3781_3841_t117g | 0.326998 | 0.310858 | 0.496867 | 0.000000 |
| test_a | slc1a2.1_4181_4281 | -1 | slc1a2.1_4181_4281_c15a | -0.285185 | 0.265036 | 0.697563 | 1.000000 |
| test_a | slc1a2.1_4181_4281 | 1 | slc1a2.1_4181_4281_t119g | 0.326998 | 0.287462 | 0.285635 | 0.000000 |
| test_a | sparc_1041_1121 | -1 | sparc_1041_1121_c82a | -0.285185 | 0.069791 | 0.630249 | 1.000000 |
| test_a | sparc_1041_1121 | 1 | sparc_1041_1121_a27c | 0.285185 | 0.288272 | 0.258064 | 0.000000 |
| test_a | sparc_661_761 | -1 | sparc_661_761_g44a | -0.268510 | 0.279259 | 0.779505 | 1.000000 |
| test_a | sparc_661_761 | 1 | sparc_661_761_t159g | 0.326998 | 0.385732 | 0.148572 | 0.000000 |
| test_a | sparc_901_981 | -1 | sparc_901_981_g173a | -0.268510 | 0.194890 | 0.470955 | 1.000000 |
| test_a | sparc_901_981 | 1 | sparc_901_981_t3g | 0.326998 | 0.384669 | 0.202485 | 0.000000 |
| test_b | slc1a2.1_3281_3381 | -1 | slc1a2.1_3281_3381_g96c | 0.174134 | -0.058346 | 0.374721 | 0.000000 |
| test_b | slc1a2.1_3281_3381 | 1 | slc1a2.1_3281_3381_t1g | 0.383106 | 0.251841 | 0.337852 | 0.000000 |
| test_b | slc1a2.1_3641_3721 | -1 | slc1a2.1_3641_3721_g82c | 0.084543 | 0.381566 | 0.728397 | 1.000000 |
| test_b | slc1a2.1_3641_3721 | 1 | slc1a2.1_3641_3721_t5g | 0.347409 | 0.483650 | 0.191168 | 0.000000 |
| test_b | slc1a2.1_3781_3841 | -1 | slc1a2.1_3781_3841_g130c | 0.095743 | 0.271075 | 0.470502 | 1.000000 |
| test_b | slc1a2.1_3781_3841 | 1 | slc1a2.1_3781_3841_g187c | 0.350845 | 0.850420 | 0.054300 | 0.000000 |
| test_b | slc1a2.1_4181_4281 | -1 | slc1a2.1_4181_4281_a80g | 0.209892 | -0.006231 | 0.494331 | 0.000000 |
| test_b | slc1a2.1_4181_4281 | 1 | slc1a2.1_4181_4281_t190a | 0.406924 | 0.641326 | 0.020521 | 0.000000 |
| test_b | sparc_1041_1121 | -1 | sparc_1041_1121_t1c | 0.167364 | 0.133667 | 0.662902 | 1.000000 |
| test_b | sparc_1041_1121 | 1 | sparc_1041_1121_c190a | 0.578518 | 0.359698 | 0.221552 | 0.000000 |
| test_b | sparc_661_761 | -1 | sparc_661_761_c113g | 0.183838 | 0.112848 | 0.667093 | 1.000000 |
| test_b | sparc_661_761 | 1 | sparc_661_761_c190a | 0.420110 | 0.356445 | 0.168355 | 0.000000 |
| test_b | sparc_901_981 | -1 | sparc_901_981_a1c | 0.187189 | 0.289716 | 0.634124 | 1.000000 |
| test_b | sparc_901_981 | 1 | sparc_901_981_t190a | 0.560492 | 0.396901 | 0.181437 | 0.000000 |

Direction +1 seeks increased SN/cortex enrichment; −1 seeks decreased enrichment. Wrong direction concerns the sign of the selected author's mutant-minus-WT effect. It is **not** the SRLE metric “wrong in both constituent replicates,” and those rates must not be equated. Replicate contrast columns are retained for transparent inspection, not used to choose candidates after reveal.

## Observed candidate feasibility (descriptive only)

| parent_id | min_effect | max_effect | positive_fraction | negative_fraction |
| --- | --- | --- | --- | --- |
| slc1a2.1_3281_3381 | -0.462740 | 0.616447 | 0.966667 | 0.033333 |
| slc1a2.1_3641_3721 | -0.542871 | 0.726268 | 0.987719 | 0.012281 |
| slc1a2.1_3781_3841 | -0.302544 | 0.916620 | 0.950877 | 0.049123 |
| slc1a2.1_4181_4281 | -0.666046 | 0.668717 | 0.857895 | 0.142105 |
| sparc_1041_1121 | -1.163106 | 0.793099 | 0.726316 | 0.273684 |
| sparc_661_761 | -0.874701 | 0.605674 | 0.982394 | 0.017606 |
| sparc_901_981 | -0.078803 | 0.502342 | 0.998233 | 0.001767 |

The candidate effects are mostly positive relative to WT, so predicting positive signs can yield high variant sign accuracy without strong ranking or a reliable decrease recommendation. Shared WT measurement error can shift all effects for a parent. This explains why high sign accuracy and lower regret cannot substitute for comparison against the fixed simple controls. No outcome-centering or new abstention rule was introduced.

`GSE330741_candidate_rankings.csv` contains all 175,296 parent/model/direction/candidate rows for A and B. The unchanged prefit A predictions and held-parent B predictions are separately preserved. The result supports a bounded candidate-ranking signal in this exposed, small-parent setting; it does not establish a generally reliable RNA-edit design tool.
