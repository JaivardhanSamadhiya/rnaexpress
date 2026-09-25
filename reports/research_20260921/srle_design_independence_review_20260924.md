# SRLE design and independence review, 24 September 2026

AI-authored independent methods audit of existing source and specifications.
No measurement tables, sequence rows, protected datasets or new outcomes were
opened. No fitting, numerical re-evaluation, new sequence recommendation or
external search was performed. Frozen files and conclusions remain unchanged.

Reviewed sources: `src/research_20260921/pilots.py`, `robustness.py`, and
`raw_swap_consistency.py`; reviewed specifications: `pilot_execution_spec.md`,
`followup_spec.md`, `raw_replication_spec.md`, and `raw_swap_spec.md` under
`reports/research_20260921`. Findings below concern the implemented estimand and
its interpretation; code inspection alone cannot certify historical execution
order or the absence of all prior outcome exposure.

## Overall assessment

No direct test-label leakage into the fitted composition means, feature scaling
or Ridge coefficients is evident in the reviewed code. The evaluation is a
sequence-level interpolation exercise in one exhaustive six-mer landscape, with
closely related training and test sequences. It is not a holdout of composition
classes, mutational neighborhoods, reporter contexts, genes or experiments.
The baseline and swap follow-ups reuse a test set whose initial pilot results
were already inspected. They are explicitly post hoc in the specifications.

The supported description is: fixed model predictions for exact six-mers omitted
from fitting, evaluated on a restricted set of measured composition-preserving
swaps, followed by consistency checks in constituent experiments. The description
"independent validation on unseen parents" would overstate this design.

## 1. Split and composition baseline

`pilots.py:46` assigns each exact six-mer to test using a fixed SHA-256 rule.
`fit_order` constructs composition means solely from non-test labels
(`pilots.py:75`), fits the scaler solely on training features (`:79`), and fits
Ridge solely on training residuals (`:80`). The comparison models follow the
same training-only procedure (`robustness.py:45`). Evaluation classes need at
least two training and two test sequences (`pilots.py:82`). Thus the zero fallback
for a class without training observations is not used in the evaluated classes.

Using each training observation in its own class mean is ordinary in-sample
nuisance estimation here, not use of a test label. It is not cross-fitting, and
the resulting uncertainty calculations condition on those fitted means and
coefficients. The composition baseline is a training-label lookup within already
represented classes; it is not a transferable composition model for new classes.

The hash split has no neighborhood grouping. A test six-mer can share most bases,
motifs and its composition class with training sequences. This is expected for
this interpolation task, but prevents claims of neighborhood-independent or
new-context generalization. Exact parent and candidate sequences omitted from
fitting should not be confused with independent biological parent contexts.

## 2. Candidate eligibility and outcome-dependent exclusions

`robustness.py:64` constructs eligibility from the original test indices. Each
parent must itself be an eligible test sequence, and its candidate list retains
only single unequal-base swaps that are also eligible test sequences (`:68`).
No candidate sequence's own label enters model fitting. However, the evaluated
choice set excludes legal swaps assigned to training. This is a restricted
held-out-candidate benchmark, not optimization over every legal swap of a parent.
A swap of unequal bases changes two sequence positions; it is not a single-base
substitution.

The code excludes neighborhoods with fewer than two candidates or zero measured
candidate range (`robustness.py:69`). The nonzero-range condition is an
outcome-dependent eligibility rule needed by this normalization; it is not
training leakage. It makes the reported estimand conditional on non-degenerate
measured neighborhoods. The follow-up specification states the candidate-count
rule but does not separately state this zero-range exclusion. Do not claim that
every cohort decision was entirely outcome-independent.

The raw check retains a parent only when it and every candidate pass the existing
count threshold in all four libraries (`raw_swap_consistency.py:38`). This avoids
dropping unfavorable individual candidates from a retained neighborhood, but
restricts the estimand to fully covered, sufficiently counted neighborhoods.
Read coverage is not an independent random sample of phenotypes. The raw check
raises an error, rather than silently excludes, if a retained replicate has zero
candidate range (`:43`). No data were inspected here to count either condition.

## 3. Ties and what the symmetric metrics actually measure

All policies break prediction ties lexicographically (`pilots.py:66` and
`robustness.py:75`). This deterministic rule is fixed and outcome-independent,
but it can create directional lexical preferences; it is not a random tie break.
The composition prediction is constant within a candidate set, so its upward
and downward policies choose the same lexical candidate.

Let candidate outcomes be y, with minimum m, maximum M, mean mu and range
R = M - m > 0. Let y_up and y_down be the outcomes selected by a policy when
asked to increase and decrease NRS. For the same parent and candidate set:

- Upward regret gain over uniform is (y_up - mu) / R.
- Downward regret gain over uniform is (mu - y_down) / R.
- Their mean is (y_up - y_down) / (2R).

For a flat predictor using the same tie choice in both directions, this last
quantity is exactly zero. Both the flat policy and uniform selection have mean
two-direction regret exactly 0.5. This algebra does not imply that either
direction separately has regret 0.5 or gain zero. The near-zero composition
result is therefore expected by construction, not an independent empirical
validation of composition neutrality.

There is a parallel interpretation issue for the reported directed score change.
Writing the parent outcome as y_parent, the symmetric average is

    [(y_up - y_parent) + (y_parent - y_down)] / 2
        = (y_up - y_down) / 2.

The parent score cancels. A positive symmetric average demonstrates separation
between selected candidate outcomes; it does not establish that both selected
directions improved on the unedited parent. Likewise, positive regret gain in a
direction means outperforming uniform candidate choice, not necessarily the
parent. Keep "mean bidirectional directed NRS change" as the exact metric name
and avoid interpreting it as a guaranteed per-edit improvement. The current raw
summary reports direction-specific regret gains, but not direction-specific
parent-relative NRS changes.

The unedited parent is not an available candidate. Consequently this is a forced
swap-selection task: there is no leave-unchanged or abstain option and no claim
that making a change is always preferable to keeping the original sequence.

## 4. Overlap, uncertainty and biological independence

Swap neighborhoods overlap: a six-mer may appear as a parent and as a candidate
for several other parents. All such single-swap connections preserve composition.
Aggregation within composition before resampling classes therefore avoids
treating those overlapping parent neighborhoods as independent observations.
It does not create independent experiments. Classes still share a fitted model,
training procedure, reporter assay and experimental normalization.

The primary prediction error reduction pools squared errors and therefore gives
larger eligible classes more weight in its point estimate. Selection metrics
first average within class and then weight classes equally. These are different
estimands and should not be described as a single common weighting scheme.

The raw consistency check uses common bootstrap indices for models and
replicates, including paired pair-minus-kmer differences
(`raw_swap_consistency.py:57,73`). That pairing is correct. The earlier swap
diagnostic draws a fresh bootstrap array for each model (`robustness.py:85`);
its separate confidence intervals are not paired model-comparison intervals.
Neither approach re-fits models inside bootstrap draws or incorporates full
training-sample uncertainty. The intervals are descriptive and conditional.

The original permutation test shuffles only test outcomes within composition,
with fitted predictions fixed. Its interpretation requires conditional
exchangeability under that null. It is not a test of independent biological
replication or prospective edit effects, and its original p-value cannot be
transferred to the later, post hoc swap analysis.

The raw-reconstruction specification states that the published aggregate labels
already used these constituent experiments. Recounting them is an independent
implementation of measurement processing, not an untouched experiment. The
separate experimental score estimates and their consistency do not remove the
shared training-label provenance.

## 5. Freeze enforcement gap

The raw-swap freeze records the evaluator, specification, saved choices and raw
scores, but omits `robustness_predictions.csv`, which is subsequently read to
reconstruct candidate eligibility (`raw_swap_consistency.py:14,23`). It also omits
the imported candidate-generation and composition-key implementations. The raw
entry point records current hashes instead of verifying an earlier raw-swap
freeze before evaluation. This is incomplete prospective dependency enforcement,
not evidence that any file was changed. Later integrity evidence cannot
retroactively expand the original freeze. Preserve the historical files and
describe this limitation in any reproducibility claim.

## Claims that survive

- Within one measured reporter landscape, exact sequence identities omitted from
  fitting can be scored using training sequences from shared composition classes.
- The documented fixed policies can be evaluated on the declared restricted swap
  task, with composition-matched comparisons and cluster-aware descriptive
  uncertainty. The previously reported positive values remain conditional on
  that task and its eligibility rules; this audit does not re-score them.
- Reconstructed constituent scores provide a useful consistency and provenance
  check. They do not provide independent biological confirmation.
- The strong short-motif comparator remains essential. These methods provide no
  grounds to claim pairwise-model superiority, a new mechanism, universal edit
  control, superiority to leaving the parent unchanged, or effectiveness on new
  transcripts, genes or cell types.

Suggested concise description: "A retrospective, composition-controlled benchmark
of fixed choices among measured test-set swaps in one six-mer reporter landscape,
with constituent-replicate recounting and explicit transfer failures."

This review is additive documentation. It authorizes no new data access, fitting,
confirmation opening or change to any frozen gate or historical verdict.
