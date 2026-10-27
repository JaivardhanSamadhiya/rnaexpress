# Three-arm comparison: scalar core ready, biological execution not admitted

The new data-free core has fourteen passing invented tests. It supplies a
metadata planner, exact complete-menu hierarchy, source-pair contract,
source-only RMS/mean reference, and scalar objectives/gradients. It imports
only Python standard-library modules and the unchanged mathematical menu-loss
prototype. There is no loader, scientific-library import, optimizer call,
execution controller or project-data command.

## Why the initial two-arm draft is insufficient

`reports/generalization_menu_loss_20261026/design.md` is the preserved initial
mathematical prototype and two-arm development draft. The post-gate saved-report
diagnostic found 70.5670% binary primary weight in the completed known-cell
study. On such menus the proposed loss is exactly a shifted/temperature-scaled
logistic loss. A matched control is required before attributing any improvement
to costs among multiple alternatives. That diagnostic was done without fitting
or opening CORE, original arrays or new biological outcomes.

## Fixed mathematical comparison implemented here

Keep the original pooled linear utility, existing 246-column representation,
source-only pair RMS and supported-coordinate rule, full menus, global
components and assay exclusions. The three arms are:

1. `pairwise`: original weighted `log(1+exp(-m))` on signed pair margins.
2. `margin_pair`: the same sampled pairs and weights with
   `0.25*log(1+exp((1-m)/0.25))`.
3. `menu_cost`: the previous smooth full-menu normalized-regret upper bound,
   temperature 0.25 and both directions equally weighted.

The paired margin control exactly equals menu-cost loss and gradient on
two-candidate menus. It differs on larger menus. No new temperature grid,
features, source identity score, target calibration or cell-deviation head is
introduced. The fixed penalty order is 0.005, 0.05, 0.5. A future actual study
must still pin its full source/data/runtime/gate manifest before fitting.

Four outer assay exclusions, three source inner exclusions and three penalties
produce 36 inner plus four outer tasks per arm: 108 inner/12 outer, 120 total.
Outer tasks have an explicit source-only-selection placeholder, not a penalty
selected here. This planner evaluates no regret or labels. It checks original
component exclusion then rejects exact-allele overlap rather than silently
trimming source rows. Each retained context must remain complete, and each
required source assay must remain represented.

Metadata dictionaries accept exactly six outcome-free fields. Numeric effects
are supplied separately to the scalar arithmetic. Source menus must partition
every supplied feature/effect row; extra held/unused rows reject. Pair sampling
is an external input to be certified: the kernel does not replace the original
NumPy seeded sampler with Python randomness. Supplied pairs must have the exact
capped roster size, valid indices and no duplicates; only exact target ties
are omitted. If no informative sampled preference remains, stop instead of
silently dropping the context and renormalizing. Whether that stricter stop is
ever triggered on the actual data is unmeasured.

Each source assay/component/context has equal hierarchical mass. Pair loss
divides context mass over valid sampled pairs, menu loss averages its two
directions. A common weighted source-candidate mean cancels within menus.
Columns below 1e-8 weighted pair RMS have scale1 and coefficients fixed exactly
zero. Unsupported nonzero coefficients, bad pair signs, nonfinite data and
incomplete source menus reject. The scalar reference is for independent
arithmetic checking of a future numerical implementation; it does not certify
a future NumPy/SciPy implementation or actual source roster.

## Existing input availability: metadata inspection only

The immutable historical prefit manifest pins the existing all-assay
`artifacts/generalization_20261007/scaling_features.npz` at
`038a64c83c7427cb1b5775e216148c90e6b67260fa4544aae2b6afbae6450a72`.
It also pins the outcome-free four-column row index. Those files exist on D:
(3,160,928 and 461,214 bytes respectively), but are absent from the C: recovery
workspace. Only file metadata was queried; their contents were not opened,
copied, hashed, parsed or admitted in this preparation.

The historical probabilistic `data.npz` and replicate-measurement archive also
exist on D:, absent on C:. Their existence does not admit their contents.
The old loader opens CORE and loads replicate arrays unnecessarily for this
comparison; it was not called. The earlier cross-assay canonical source also
contains other cohorts, so it is not a safe substitute to open blindly.
Replicate means or sampled pair differences must not be silently substituted
for the frozen aggregate-label endpoint.

The current certified C: metadata/features/persisted labels cover only Mikl.
The other three aggregate-label admissions and a safe full-roster metadata
route remain missing. No new four-assay input is certified by stat sizes,
declared historical hashes or these invented tests.

The observed resource check had 981,868,544 bytes available physical RAM,
below the unchanged 3 GiB default scientific-input/import gate. No scientific
package, original biological array or label input was loaded. The narrowly
approved known-cell FIT resource exception remains tied to its completed
study; it is not reused for this proposed comparison.

## Tests and remaining work

Fourteen invented tests cover the entire 120-task roster, held-assay exclusion,
global component removal, exact-allele rejection, unequal hierarchy weights,
complete-menu/source-only boundaries, sampled-pair/tie handling, RMS/unsupported
columns, finite-difference gradients for all three arms, original logistic
formula equality, centering cancellation, convexity, wrong pair signs, and
binary margin/menu equality versus larger-menu differences. No invented test
is a biological result or full-data memory profile. Independent source review
has not been completed for this new core.

Before actual fitting: resolve the permitted four-assay input route; independently
review the math/implementation; finish native vectorized training and numerical
replay; freeze exact rosters, endpoints, gates and runtime; implement/review the
bounded owner; and obtain any required distinct resource/execution authority.
The prior single known-cell FIT permission is consumed and no retry is allowed.
No actual study prefit, FIT birth, optimizer unit or gate evaluation exists here.

All current outcomes are exposed development. The comparison can test an
incremental hypothesis, not establish fresh confirmation or a novel algorithm.
No reserved outcome, new dataset, paid resource, drive repair or scheduled
task is part of this preparation. The original 33 user modifications remain
protected.
