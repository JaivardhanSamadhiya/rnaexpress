# Exact-menu observed context conflict

7 October 2026. Model-free descriptive calculation, independently replayed. The [fixed protocol](D:/rnaexpress/reports/context_conflict_audit_20261007/protocol.md) and [plan manifest](D:/rnaexpress/results/context_conflict_audit_20261007/plan_manifest.json) preceded outcome arithmetic. Only exact shared menus' exposed Mikl effects were read; Moffatt outcomes, all other studies' effects, protected data and model fits were excluded.

**The same sequence-only extreme choices cannot recover both observed cell-specific extrema in 1,527 of 2,408 identical Mikl menus. The relaxed menu-wise empirical minimum, averaged equally over biological components, is 0.2107026211 normalized regret. This is an observed-data limitation, not an irreducible biological/noise bound.**

| Quantity | Mikl CAD/Neuro-2a |
|---|---:|
| Exact shared original parent+candidate menus | 2,408 |
| Candidate measurements covered | 13,760 / 13,781 |
| Cell-specific contexts covered | 4,816 / 4,825 |
| Biological components covered | 187 / 187 |
| Menus allowing simultaneous exact zero regret | 881 |
| Menus with positive minimum beyond fixed 1e-12 arithmetic tolerance | 1,527 |
| Components with at least one such menu | 171 / 187 |
| Component-weighted fraction of conflict menus | 0.5773254673 |
| Component-weighted minimum pooled regret | 0.2107026211 |
| CAD regret at the selected shared pair | 0.2116852438 |
| Neuro-2a regret at the selected shared pair | 0.2097199983 |
| Constant-score lexical-choice regret | 0.5 |
| Largest per-menu minimum regret | 0.5 |

All matched menus have finite outcomes, informative positive spans and 2–10 unique mutant sequences. Every pair has identical original parent and mutant sequences across cells and the same biological component. Nine nonmatching cell contexts (21 measurements) were excluded, without forcing a candidate intersection. No duplicate candidate sequences or ambiguous exact signatures appeared in the admitted matched subset. The complete [exclusion roster](D:/rnaexpress/results/context_conflict_audit_20261007/excluded_contexts.csv) and [menu decisions/four regret contributions](D:/rnaexpress/results/context_conflict_audit_20261007/menus.csv) are retained.

For each context, normalize increasing-choice regret by `(max y-y_selected)/span` and decreasing-choice regret by `(y_selected-min y)/span`. The menu objective equally averages two contexts and two directions. Minimize it over a distinct increasing/decreasing candidate pair. Any such pair can be realized as the unique extrema of an unrestricted shared score on that menu. A constant score selects a lexical candidate for both directions and has mean regret 0.5 in every informative context. It cannot improve the reported minimum. Multiple equally optimal pairs use deterministic lexical sequence order; exact truth extrema use parsed float64 equality, while numerical-zero classification uses a predeclared 1e-12 accumulation tolerance.

Average menus equally within each component and then 187 components equally. Thus large candidate libraries or genes with many menus cannot dominate the summary. An equivalent analytic expression for one menu is `(1-range(mean_context((y-min y)/span)))/2`; outcome-free tests checked agreement with the distinct-pair minimization.

The result is a **relaxed empirical lower bound for a constrained global sequence-only utility**, because optimization is independent by menu and does not enforce representation/regularization constraints. Cross-menu repetition was explicitly checked: the 6,880 mutant sequences and 6,880 parent+mutant pairs each occur in exactly one matched menu. Therefore repeated-allele consistency does not add a constraint in this particular subset; a fixed learned feature map still can. The choices are outcome-informed arithmetic witnesses, not a predictor, deployable recommendation or source-trained performance estimate.

Observed conflicts are consistent with missing cell/assay state, but also with measurement noise, sampling variation, processed estimators, barcode effects or residual experimental context. This audit does not distinguish those explanations, establish causal context dependence, estimate a Bayes/noise ceiling or show transfer impossibility. Common WT reference shifts cancel in within-context extrema/spans. Construct-specific nonlinear effects may remain. All data are previously exposed development measurements.

Moffatt has **zero complete exact shared GFP/firefly menus**. All six parent menus have different admitted candidate sets across reporters, although they have substantial intersections. The 12 contexts and 6,749 rows are excluded; no Moffatt outcome arithmetic was performed. That coverage limit is not evidence of reporter conflict. A separately declared intersection-menu question would change the estimand and is outside this audit.

Verification: seven scoped outcome-free synthetic tests PASS. An independent scalar brute-force replay reconstructed all 2,408 selected menus, original identities, exact-zero classifications, all four regret contributions and component-weighted summary. Maximum arithmetic discrepancy was 5.551115123125783e-17, below the fixed 1e-12 threshold. [Replay receipt](D:/rnaexpress/results/context_conflict_audit_20261007/replay.json), [machine summary](D:/rnaexpress/results/context_conflict_audit_20261007/summary.json), [audit source](D:/rnaexpress/src/context_conflict_audit_20261007/audit.py).

No current feature matrix, frozen model, earlier gate or protected outcome changed. These findings support explicitly testing or measuring context dependence before asserting universal sequence-only edit choices; they do not themselves supply a positive biological generalization claim.
