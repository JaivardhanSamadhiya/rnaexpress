# Locked internal freeze

Code commit: `6585544e8ce1433c757bb46b69088f68bd59e2eb`.

The selected method is pairwise ranking over explicit parent/edit features. It was trained on 3,540 SNVs from 12 development parents using C=1 and 300 deterministic training pairs per parent. Raw margins are monotonically calibrated to localization-effect units using only cross-fitted development predictions (RMSE 1.202 log2).

All twelve baselines/ablations were fit on the same development parents. The frozen file contains 855 candidates from Cdc42_2, Cflar_1 and Ndufa2 with increase/decrease ranks and no measured outcomes.

Model SHA256: `fbe9a46c6f8ca722382a6f35d2b0804d4e2ef47f49d869609ff70e1a17f5d337`.

Prediction SHA256: `3b1fb0d494052fa6001615c3cbc257ff627e3464454457c846ab6cb153d37ad8`.

Locked N-zip outcomes and all astrocyte outcomes were not accessed by this pipeline.
