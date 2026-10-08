# Completed SpliceBERT follow-up and current execution state
Prepared 8 October 2026 after the frozen comparative gate completed. Lower normalized regret is better. This report does not change any gate, historical verdict or protected outcome policy.

## SpliceBERT result
All six fixed tracks are **NO-GO**. The strongest historical simple comparator has macro regret 0.496868. The encoder and encoder-plus-structure tracks do not establish generalization.

| Track | Macro regret | Gain over simple | Descriptive 95% gain interval | Verdict |
|---|---:|---:|---|---|
| base | 0.512255 | -0.015387 | [-0.035618, +0.005478] | NO-GO |
| raw | 0.500327 | -0.003459 | [-0.025774, +0.019182] | NO-GO |
| structure | 0.516485 | -0.019617 | [-0.034863, -0.005780] | NO-GO |
| lookup | 0.527664 | -0.030796 | [-0.045173, -0.015889] | NO-GO |
| splicebert | 0.500791 | -0.003923 | [-0.022771, +0.015010] | NO-GO |
| combined | 0.512644 | -0.015776 | [-0.034387, +0.002135] | NO-GO |

SpliceBERT's gain over base is +0.011464. Its per-assay gains are {"astrocyte_gse330741": 0.1097344064699522, "mikl_gse173098": -0.002754859162169221, "moffatt_gse334718": -0.02450756264847659, "srle": -0.036617968397443024}. Removing Astrocyte leaves mean gain -0.021293. Thus the favorable difference is concentrated in Astrocyte; the other three assays worsen against base. Adding structure to the encoder worsens macro regret by 0.011852. The underlying algorithm may remain useful elsewhere; this tested representation failed its declared candidate-ranking gate.

All 240 checkpoints completed. The independent arithmetic/source-selection/decision replay passed: 216 inner and 24 outer checkpoints, 1,401,318 inner candidate scores, 157,548 outer candidate scores and 65,232 decisions. Maximum independent inner error was 8.881784197001252e-15; maximum independent outer error was 5.329070518200751e-15, and saved canonical outer scores matched exactly. Replay created zero fits. The source envelope of any other experiment is not certified by this check.

The prefit SHA is ad5f8a0893edee849d4b54b0954dd45dd6302f32d48eb720aae771e0c223a98e. The verification receipt SHA is f43353d84ea6e04ca399eefbbebbb2dbeef3438bd7836dcf7bd1d15ed74f2cef and gate receipt SHA is ec705a7216a32b594b09d46c4fae58072864f388ed76e308aa85eb8f777e6918. Shared base/raw/structure controls replicate previous matrices on the same exposed cohort; they are not new independent evidence. SRLE retains its certified 46-nt local context, shorter than the author's stated 64-nt training minimum. No assay was removed or padded after results.

## Conservation progress
All 3,003 fixed UCSC requests were visited; 20 pre-admitted pilot responses were reused and 2,983 remaining fixed requests were executed. All intervals admitted the fixed ordered dual-track response. Preserved total acquisition, including schemas and pilots, is 3,730,773 bytes. Extraction and independently reconstructed site joins/whole-parent availability passed for 15,132 exact edited genomic sites. The additive provenance audit bound each score and missing reason to its original chromosome/position/query and preserved response bytes. The strict envelope parser is shared; no independent envelope-parser certification is claimed.

The feature formulas and controls were frozen in commit 030b092 before their production. They use static parent-reference phyloP/phastCons covariates, not mutation-induced conservation changes. Both native and raw-position blocks receive the same complete-parent availability mask; no candidate menu is filtered. Feature-only production waits for the unchanged fresh 3-GiB memory floor. No conservation model has been fit; matrix, comparator, runtime and prefit admission remain necessary.

A PowerShell Tee-Object logging parameter error occurred after the provenance audit passed. The audit receipt exists and was rehashed. The separate resumed launcher preserves that failure and uses direct stdout redirection; source files, numerical settings and memory floors are unchanged.

## Other active routes
The native masked-likelihood synthetic backend waits in the existing sequential launcher for at least 3.3 GiB caller RAM and a fresh 3-GiB backend check. It has not started. G-quadruplex and joint-accessibility downstream fits, and the old RBP/joint cell-axis matrices/fits, remain pending their resource and freeze requirements. No result is inferred from a pending run.

Earlier nonlinear crossed-cell combined regret 0.475819 was promising relative to its model baseline, but its required strongest-simple-comparator gain interval crossed zero. The same method's represented-cell regret 0.489933 worsened against its matched nonlinear simple comparator. These remain NO-GO.

No positive generalization result or completely novel biological finding is established. Current evidence supports continued controlled testing of distinct physical/annotation features and a narrowly defined represented-cell training hypothesis, with every prior negative retained.
