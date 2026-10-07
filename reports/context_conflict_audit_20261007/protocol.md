# Exact-menu context conflict audit

7 October 2026. Written after metadata-only overlap inspection and before outcome arithmetic. This is a descriptive calculation on exposed development measurements; it does not fit a model or consume protected labels.

Use only `results/probabilistic_ranking_20260928/candidate_index.csv` (SHA256 773d6145bbe4b17ff50597e47eba13f0b2977a3ddf541a1b238adcb7ff433e3d). Read metadata first. Compare CAD/Neuro-2a within Mikl, GFP/Firefly within Moffatt. A match requires the identical original parent sequence and entire identical set of original mutant sequences, one context per side, no duplicate mutant sequence within a context, and the same biological component. Do not force intersections or match near-identical alleles. Exclude metadata-ambiguous/duplicate/nonmatching contexts and report coverage. Then read only matched Mikl/Moffatt rows' measured_delta values, using selected physical rows and explicit columns. Require finite outcomes and positive spans in both contexts; report any failures rather than substitute a sequence/menu.

For menu m, context c, increasing choice j and decreasing choice k:

`r_up(c,j)=(max y_c-y_cj)/span_c`
`r_down(c,k)=(y_ck-min y_c)/span_c`
`R_m(j,k)=mean over two contexts and two directions of these regrets`.

Compute the empirical minimum over distinct choices j!=k. Exact ties in numerical losses use lexical mutant-sequence order and then lexical pair order. Constant-score lexical selection yields 0.5 pooled regret regardless of which ID is first; include it as an attainable tie case, but it cannot improve the distinct-choice minimum. Original decisions also use lexical intervention IDs for exact score ties; because constant scores select the same candidate for both directions, their pooled regret remains 0.5 in each informative context even if first IDs differ between contexts.

Compute intersections of exact observed maximum and minimum sets, and whether a distinct pair can realize zero regret in both contexts. Exact sets use equality of parsed float64 outcomes. Numerical zero/conflict tolerance is fixed at 1e-12 for accumulated regret arithmetic, not estimated from outcomes. Report exact and numerical categories separately. Outcome units and common reference shifts are normalized separately within each context; this is not a comparison of raw effect magnitudes.

Weight directions and the two contexts equally per menu; weight matched menus equally within biological component; then weight components equally within study. Report study-specific means, positive-conflict component/menu proportions and coverage; there is no pooled cross-study score when Moffatt has no complete identical menus. For 187 Mikl components, the matched subset covers all 187 but does not certify a population-wide conclusion.

This menu-wise independent optimization is a relaxed empirical lower bound for any global sequence-only utility constrained to the same choices. Independent menu orderings may not be simultaneously realizable if alleles appear in different menus, and a fixed linear/nonlinear representation may impose further restrictions. Report cross-menu repeated mutant alleles and repeated parent+mutant pairs. Do not call the result a Bayes bound, irreducible error, measurement noise ceiling, causal context effect, validation/generalization claim or fitted predictor. Noise, finite sampling and processed effects can generate observed conflicts. Moffatt menu mismatch is a coverage limitation, not proof of context conflict.

Save exact menu fingerprints and contexts, choices and all four regret contributions, excluded metadata contexts, study/component weighting and source/code hashes. Independently replay every finite menu by brute-force pair enumeration against source data, check constant-score arithmetic and exact optimality, reconstruct weighted summaries and compare saved outputs within 1e-12. Synthetic tests cover context agreement, reversed two-choice menus, partial overlap, affine normalization, distinct/tie handling and menu identity/exclusions. No current production inputs, frozen models or protected outcomes change.
