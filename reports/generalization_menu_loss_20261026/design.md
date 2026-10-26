# A distinct next hypothesis: train for the cost of a menu choice

Status: mathematical prototype, ten invented tests passed. No biological
fitting, dataset admission, execution permission or positive research result.
The completed known-cell generation remains NO-GO. Its consumed permission
does not authorize another FIT or a different study.

## Why this is worth a controlled test

The completed study improved its training objectives without useful held-gene
selection. Its loss averages sampled pairwise preferences; its primary metric
evaluates the chosen maximum and minimum of a complete candidate menu. These
objectives can prefer different predictors. That is a possible missing link,
not an established cause of the biological failures.

Three historical implementation lineages were checked directly at the
post-closeout repository state: `src/cross_assay_20260927/models.py`,
`src/probabilistic_ranking_20260928/models.py`, and
`src/generalization_20261007/engine.py`. They use signed or soft pairwise
objectives and/or select those models by source regret. The current fixed
numeric objective is also pairwise. This bounded inspection does not establish
that no related loss exists anywhere in the repository. A broader partial-clone
history search did not complete and is not counted as evidence of absence.

Longer motifs, frequency interactions, rich BERT/RBP/structure stacks and
uncertainty supervision already have project precedents. Repeating these under
a new name would not isolate a distinct question. This prototype holds the
linear score and existing features fixed and changes the training criterion.

## Invented counterexample

Use twenty candidates with true effects 0/19, 1/19, ..., 19/19. Predictor A
keeps all middle candidates in order but swaps the two endpoints. Predictor B
keeps the endpoints correct but reverses the middle candidates. Both score
vectors have the same multiset, magnitude and squared norm. All 190 pairs fit
below the historical 256-pair cap.

A has better pairwise ordering accuracy and lower pairwise logistic loss, yet
its two-direction selection regret is 1. B has regret 0. The prototype menu
loss prefers B in this constructed example. Exact numbers are saved in
`results/generalization_menu_loss_20261026/invented_example.json`.

This is a mathematical witness of objective mismatch, not RNA evidence,
a model trained on RNA, an explanation proven on the existing cohort, or a
guarantee that the new objective will generalize. Source-only selection by
regret already partially addresses mismatch; changing the training loss may
provide no additional benefit.

## Implemented scalar kernel

For direction d in {+1,-1}, observed normalized regret of candidate i is

`r_di = (max_j(d*y_j) - d*y_i) / (max(y)-min(y))`.

Let B_d be the exact set of best-effect candidates and `b_d` the mean of their
predicted scores. With fixed smoothing temperature tau = 0.25, the kernel is

`L_d = tau * log sum_i exp((r_di + d*(s_i-b_d))/tau)`.

Average both directions equally. All candidates participate. Best-effect ties
receive equal reference mass. No uninformative span is silently removed: a
nonfinite or zero span rejects the supplied menu. No input loader or optimizer
is implemented.

For a predicted extremum j, `d*s_j >= d*b_d`, so its term is at least its
observed regret. Log-sum-exp is at least its largest term; therefore L_d
upper-bounds that selected regret, including arbitrary prediction ties. The
loss is convex in the score vector, hence in a linear coefficient vector.
The gradient is `d*(p_i - 1[i in B_d]/|B_d|)` in each direction, where p is the
softmax of the augmented scores. Averaging gives the two-direction gradient.
These are algebraic properties of this surrogate, not guarantees of statistical
consistency under arbitrary measurement noise or biological domain shift.

The kernel is invariant to an additive common score, a positive affine
transformation of observed effects, and candidate permutation. Negating both
effects and scores swaps directions. Multiplying scores is not an invariance:
smoothing temperature, feature scaling and regularization must be fixed.
No claim is made that this is exactly the SPO+ loss or a new algorithm.

## Proposed controlled biological comparison: not admitted

The intended new development question is whether a menu-cost loss improves
leave-one-assay-out candidate selection over the matched pairwise loss on the
four already exposed/admitted assays. It cannot create untouched confirmation.
No new biological resource, reserved outcome or unexposed replicate is added.

Hold the existing 26,258-row roster, 246-column interaction representation,
global component/exact-allele purge, both directions and full menus fixed. Use
one pooled linear score without target assay identity or absolute-parent-only
ranking features. Compare exactly two arms: original signed-preference logistic
and the new menu-cost surrogate. Use the same source-only pair RMS scaler,
zero unsupported coefficients, regularization grid 0.005/0.05/0.5, zero start,
L-BFGS-B settings and canonical exact score/ID evaluation. Train menu loss with
equal source-assay/component/context/direction mass; preserve the baseline's
original pair-within-context weighting. Do not introduce soft targets,
new embeddings, a cell-deviation head or temperature search simultaneously.

Reuse the four outer assay exclusions and three source-only inner assay
exclusions. Three penalties imply 36 inner plus four outer fits per arm, 80
optimizer calls total, if all original pools are eligible. Each arm selects
its penalty by the unchanged mean source-assay regret rule, first grid element
within 1e-12. No outer result selects an arm, penalty, sign, tie band or cohort.
Independent numerical replay must cover every fit and choice before evaluation.

A final source/data/runtime/metric manifest and complete gate are still needed
before this design can become executable. A proposed useful development bar is
macro regret <=0.48, >=0.01 macro gain over the matched baseline, benefit in all
four assays, a positive shared-component bootstrap lower endpoint, positive
gain after best-assay removal, and the declared harm limits. Thresholds, exact
weights, decision rosters, endpoints, exclusion handling and bootstrap details
must be finalized and committed before any new fit; this draft is not that
complete scientific freeze. Failure must remain a new negative, with no search
over temperatures, representations or favorable assay subsets to rescue it.

## Missing prerequisites and risks

1. Confirm the exact previously admitted four-assay label/feature artifacts
   and valid current-runtime parsing route. The current C: known-cell admission
   covers Mikl; it does not admit all other assays. Do not reopen CORE or use a
   legacy loader merely because its code exists. No biological input was opened
   to prepare this prototype.
2. Complete independent source/gradient/metric review, a separate frozen
   scientific manifest, current-native input admissions and a bounded owned
   execution controller. Actual full-data memory/time is unmeasured. Existing
   scientific guards and consumed FIT permissions remain unchanged.
3. Freeze the independent-confirmation route. Current assays and known-cell
   outer folds are exposed development. A favorable rerun cannot establish
   independent generalization, causal mechanism or first-ever novelty.

Noise in measured extrema may make this loss worse, especially with few
replicates. Magnitude normalization does not remove that noise. Better surrogate
alignment cannot recover missing context or unavailable sequence information.
No large architecture, new encoder download or protected outcome is justified
by the invented example. No money, schedule or new dataset is required for the
present mathematical work.

## Primary-source basis and novelty limit

[Tsochantaridis et al. (2005)](https://www.jmlr.org/beta/papers/v6/tsochantaridis05a.html)
establish structured large-margin methods. The implemented menu formulation
uses that established family of cost-augmented surrogates; its simple bound and
tie handling are derived explicitly above.

[Mandi et al. (2022)](https://proceedings.mlr.press/v162/mandi22a.html)
study decision-focused learning through ranking losses. This supports testing
the connection between training criteria and final decisions; it does not
establish RNA-edit transfer.

[Schutte et al. (2024)](https://arxiv.org/abs/2310.04328)
show why empirical decision regret can be unreliable under uncertainty. This
is a reason to retain measurement limitations and competitive controls, rather
than expect objective alignment alone to solve the project.

The method family has prior art. Any novel contribution would need to be the
specific RNA edit-decision result and its validated biological exclusion scope.
No claim of novelty or biological success follows from these ten tests.
