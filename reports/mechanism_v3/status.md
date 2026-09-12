# Mechanism-v3 status report

Mechanism-v2 verdict preserved: **NO-GO - END UNIVERSAL ZERO-SHOT RNADDRESS**.

FinalShot preserved: **NO-GO - END ZERO-SHOT RNADDRESS (commit 98ffc02)**.

Primary selector: outcome-free zipcode-grammar finite difference (`learned_from_localization_effect=false`).

## Gate checkpoint (partial executable surface)

| gate | status |
| --- | --- |
| g1_useful_selection | fail |
| g7_grammar_necessity | pass |
| g8_outcome_free_integrity | pass |

## First executable checkpoint (12 September 2026)

Outcome-free grammar vs size baseline on the full development benchmark:

* `g1_useful_selection`: **fail** (rank gain ≈ −0.121, regret gain ≈ −0.067)
* `g7_grammar_necessity`: pass (scrambled grammar also fails useful selection)
* `g8_outcome_free_integrity`: pass
* Nonzero grammar-delta coverage ≈ 3.6% of candidate rows

So this first grammar dictionary does **not** beat a dumb edit-size heuristic.
Mechanism-v3 remains open as an experiment only in the sense that additional
prospectively frozen arms (e.g. DeepLocRNA absolute-difference) may be added
under new versioned configs; fishing motifs until g1 passes is forbidden.

