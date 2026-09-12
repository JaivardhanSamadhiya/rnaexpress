# RNAddress-Mechanism-v3 — prospective design

Status: **prospective redesign**. Created after Mechanism-v2 recorded
`NO-GO — END UNIVERSAL ZERO-SHOT RNADDRESS`. This document does **not** reopen,
soften, or reinterpret that verdict. FinalShot `98ffc02` remains permanently
negative. Astrocyte remains sealed until a separate pre-holdout freeze says
otherwise.

## Why v2 is not being patched

Mechanism-v2 trained nested paired rankers on mutation localization outcomes
using high-dimensional RBP/BERT/structure deltas. It cleared useful-selection and
some edit-band checks, then failed transfer, distributed benefit, hard harm,
mechanistic necessity, and seed stability. Retuning that stack after outer scores
would be post-hoc. Mechanism-v3 therefore changes the **estimand and learning
rule**, not the old thresholds after the fact.

## Scientific idea (unchanged)

Can we select RNA-localization interventions for unseen biological parents /
contexts without first measuring those mutants?

## Solution that v2 did not use as the primary selector

**Outcome-free zipcode-grammar finite differences (primary).**

1. Freeze a dictionary of published neuronal / localization cis-elements
   (seed sites, AU-rich zipcode motifs, and related published patterns) with
   literature-derived polarity (neurite-favoring vs soma/retention-favoring).
2. For each candidate, count motif occurrences in the mutant allele and in the
   parent/reference allele.
3. The intervention score is
   `grammar(mutant) − grammar(reference)`.
4. Decrease uses the negation of that score, exactly as in v2 metrics.
5. **No coefficient is ever fit on localization_effect labels** for the primary
   selector. Mutation outcomes are used only at evaluation time.

This is closer to true zero-shot addressing than v2: the selector is a frozen
biological grammar, not a ranker trained on the same assay family's mutants.

### Why this could succeed where v2 failed

- Transfer failure in v2 was consistent with assay-specific linear fits on noisy
  high-dimensional deltas. A published grammar has no source-specific fitted
  weights to overfit.
- Hard-harm and seed instability are reduced when there is nothing to refit.
- Necessity is intrinsic: destroying the grammar dictionary must destroy the
  score by construction (permutation of motif labels / scrambled dictionaries).

### Why this may still fail

Published zipcodes may not dominate these reporter assays; grammar changes may
be rare; polarity may be wrong for a given cell type. A negative result remains
valid and will be reported as NO-GO.

## Secondary, separately named arms (not interchangeable with primary)

- **S0 geometry baseline**: same archived geometry descriptors as v2 M0, scored
  without reselection against outer outcomes (fixed recipe A, ridge unused —
  pure feature score from a frozen linear map fit only if needed on geometry
  alone inside training partitions; see model note below).
- **S1 DeepLocRNA absolute-difference** (optional resource arm): if public
  DeepLocRNA weights can be installed under `data/external/mechanism_v3/` without
  touching sealed data, score `f(mut)−f(ref)` from that absolute localization
  model. Never fine-tuned on this project's mutation outcomes. Absent weights ⇒
  ineligible, not a pass.
- **S2 scrambled-grammar null**: same patterns with polarity signs flipped or
  motif strings reversed; must not meet primary useful-selection gates.

### Geometry baseline note

To keep the primary claim outcome-free, geometry comparison uses the same
decision metrics against a **non-learned** baseline: within each decision set,
rank by smaller edit cost (increase prefers smaller cost among positive-effect
candidates is NOT used). The baseline is: score = `−log1p(edit_cost)` for
increase and its negation for decrease — a pure size heuristic with no fitted
weights. This matches the scientific question “does grammar beat dumb size?”

## Restricted domain (prospective, not post-hoc)

PARTIAL GO is allowed only for the pre-named domain:

> **Grammar-changing interventions of 2–10 nt in neuronal / neuron-like reporter
> contexts that are covered by the development sources**, where “grammar-changing”
> means `|Δgrammar| > 0` under the frozen dictionary.

If that domain is underpowered (<20 components), it is **ineligible**, never an
automatic pass. No other subgroup discovered after scoring may become a domain.

## Data and sealing

- Same certified development tables and all-allele 95% splits as Mechanism-v2
  (hash-pinned), reused as a **benchmark**, not fresh confirmation.
- N-zip **outcomes** remain forbidden; only published motif *definitions* from
  papers may enter the dictionary.
- Quarantined TDP EV5 stability data remain forbidden.
- Astrocyte sealed.
- All artifacts under `reports/mechanism_v3`, `results/mechanism_v3`,
  `configs/mechanism_v3`, `models/mechanism_v3`, `data/interim/mechanism_v3`,
  `data/external/mechanism_v3`.

## Evaluation contract

1. Commit this protocol, the grammar JSON, gates, and code.
2. Build grammar scores once; record sequence and dictionary hashes.
3. Evaluate once on nested outer folds (concatenated held folds) with v2-compatible
   decision metrics and component bootstrap.
4. Run scrambled-grammar and size baselines, transfer inventories (reuse purged
   inventory paths), and hard-harm checks.
5. Report exactly one allowed verdict. Development-only success still cannot be
   STRONG GO without the authorized holdout.

## Allowed verdicts

Identical strings to Mechanism-v2:

- `STRONG GO - UNIVERSAL ZERO-SHOT RNADDRESS SUPPORTED`
- `PARTIAL GO - RESTRICTED ZERO-SHOT DOMAIN SUPPORTED`
- `NO-GO - END UNIVERSAL ZERO-SHOT RNADDRESS`

Mechanism-v2's NO-GO remains in the ledger regardless of Mechanism-v3.
