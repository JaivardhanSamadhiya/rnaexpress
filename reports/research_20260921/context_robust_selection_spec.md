# One source-only test of selection across four reporter contexts

AI-authored, 23 September 2026 local date. This is a new exploratory question
using already-opened source data. It cannot reopen failed confirmation gates.

Question: can a fixed rule select one fragment that remains useful in the least
favorable of four measured reporter contexts? Use only the 3,235 original source
rows in 61 components. Exclude original calibration, development and confirmation.
Reuse the five component folds from context_learning_curve.py (hash prefix
curve-fold|). Fit four independent standardized 1–3-mer Ridge models, alpha 100,
on the other folds, one per context. Fit preprocessing only on training rows.
Use the identical procedure for four-base composition controls. No tuning.

Candidate sets are component/gene/library groups with at least ten candidates
having finite values in all four contexts, and nonconstant values in every
context. Use identical complete-case candidate sets for every policy. Report all
excluded sets and missingness; this population is limited by assay detectability.

For each direction (nuclear enrichment and depletion), rank signed predictions
separately within each context/candidate set. Use average ranks for ties and
(rank-1)/(n-1) to put percentiles on [0,1]. The primary maximin policy selects
the highest minimum predicted percentile across contexts. Baselines select by
the average percentile, each of four individual context percentiles, or maximin
composition percentiles. Average outcomes over all exactly tied selections.

Measured candidate utility is its lowest signed measured percentile over the
four contexts. Robust regret is best available utility minus selected utility.
Uniform random regret is calculated exactly by averaging all candidate utilities;
it is not assumed to be 0.5. Report the fraction of decision sets with any
candidate at or above percentile 0.75 in all four contexts, and the fraction
achieved by each policy, separately for both directions.

Average directions, then gene/library decisions within component, then components
equally. Report primary gains against every comparator, with 5,000 paired
component bootstrap draws, seed 20260924. Intervals are descriptive: overlapping
training folds, reused source data, and prior research choices are not accounted
for. Also report both directions separately. A promising source-only result
requires >=20 eligible components, gain >=0.03 over every comparator, and every
descriptive lower bound >0. This is a resource-allocation criterion only; it does
not authorize additional labels. Preserve all outcomes and do not retune.

Maximin optimization is established methodology. RNA context dependence is prior
art, including Ron and Ulitsky 2022 (10.1038/s41467-022-30183-0); models targeting
consistent localization in two cell lines appear in Mikl et al. 2022
(10.1093/nar/gkac806). The study tests a specific decision objective, not discovery
of context dependence, a novel algorithm, minimal-edit effects, or external validity.
