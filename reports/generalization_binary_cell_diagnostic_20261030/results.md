# Opposite measured rankings in paired binary menus

This post-gate analysis uses only the closed, already exposed known-cell report
(`be53e8c02be6ae444ec67bd231532571bd97d00a4c92b4f52bc8ec15969f462a`).
It opens no original feature/label archive, fits no model and changes no gate.
All three saved arms independently reproduce the same truth-discordance totals.

Among 2,408 paired CAD/Neuro-2a contexts, 1,343 have exactly two candidates.
For 610 of those binary pairs (45.42% by raw count), the same two mutant
sequences have opposite measured aggregate-effect rankings in the two cells.
Under the original equal-cell/component/context hierarchy, discordance is
**46.9459% of binary weight**. Binary contexts retain 70.5670% of primary weight.

For a predictor constrained to assign the **same ordering in both cells**, an
outcome-informed oracle must get at least one cell wrong on every discordant
binary pair. The resulting conditional binary regret floor is 0.234730, or a
conditional ordering-accuracy ceiling of 76.5270%. The binary contribution alone
imposes a 0.165641 floor on the complete primary regret if every other menu is
optimistically perfect. These are restricted mathematical bounds for this
observed endpoint, not an achievable algorithm, all-model impossibility result,
biological noise ceiling, population parameter or independent confirmation.

The pooled saved arm orders all 1,343 binary pairs identically across cells;
the joint arm does so on 1,110, and the independent arm on 760. Their binary
primary regret contributions are respectively 0.355648, 0.354425 and 0.357438.
Allowing different cell rankings in the completed fixed feature/model study did
not produce useful held-gene performance. The new bounds leave ample room below
the original 0.48 gate, so disagreement does not by itself explain the failure
or prove that generalization is impossible.

What this changes in the research interpretation: a cell-independent universal
ordering cannot match both observed cell rankings everywhere. The relevant
future target must state whether it seeks a transferable average preference or
a cell-conditioned preference. The existing menu-loss comparison tests the
former training-objective hypothesis; changing its architecture or endpoint
after outcomes would require a distinct study. Aggregate-effect discordance may
also reflect sampling noise; this report contains no admitted replicate-level
uncertainty analysis that could distinguish that explanation from biology.

Five invented tests check concordant/conflicting cells, the half-regret bound,
effect-magnitude invariance, hierarchical versus raw-count weighting, missing
cells, changed candidate alleles and unrecoverable constant-score menus. The
first test invocation had one assertion expecting the wrong rejection message
(`unpaired` versus the earlier `both cells required` check); only that test
expectation was corrected. The analyzer and saved biological diagnostic were
unchanged. This is a test assertion repair, not a biological rerun or model retry.

The historical known-cell result remains **NO-GO**. No positive generalization
or novelty result is claimed by this descriptive diagnosis.
