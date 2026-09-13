# RNAddress-Mechanism-v5 frozen protocol

This document and `configs/mechanism_v5/design.json`
(sha256 `404c13581717d288f94d8e2e4eb9cb37df0ed290889dd93368eabf75ceb112c9`)
are the controlling specification for a single scored evaluation. Both are
committed before any score exists.

Nothing here authorizes Astrocyte access. `src/mechanism_v5/io.py::open_holdout`
refuses unconditionally.

## Why v5, and what is genuinely new

Four eras have closed NO-GO. v4 was the informative one: it produced the
project's first real positive (within-parent absolute localization,
auROC 0.9503, ρ +0.799) but failed its gates because the signal was bulk
composition (+0.0197 over a 20-column baseline, under the +0.030 bar) and
because cross-gene transfer collapsed — with the 1,364-feature model
transferring **0.055 auROC worse** than plain composition.

v5 is built from that measurement rather than around it. Two arms, neither
previously attempted.

## Diagnostics that shaped this design

Measurement-only; no model score was produced before the design was committed.

**A hypothesis of mine was refuted, and the design changed accordingly.** I
predicted v4's cross-gene failure was driven by gene baseline offsets. It is
not: Mikl between-gene variance is only **2.0%** (Moffatt 19.8%, TDP43 15.2%).
Gene-centering is therefore *not* used as the fix, despite being the obvious
move and despite being nearly free (reliability 0.4527 → 0.4477).

Other findings that became design constraints:

* **Breadth exists where v4 did not look.** Mikl has 189 genes and 5,759
  parents; v4 tested transfer on 10 genes.
* **Pooling is rejected.** The pooled confident set is 24,328 rows of which
  22,986 (94%) are Moffatt's 10 genes at positive rate 0.778, against Mikl's
  1,342 rows at 0.251. Pooling would be one source wearing a disguise.
* **Lengths differ** (Mikl 150 nt, Moffatt/TDP43 260 nt), so every v5 feature is
  a k-mer *frequency*, never a raw count as in v4.
* **Mikl folds are balanced**, positive rate 0.211–0.286 across folds, versus
  Moffatt's 0.077–0.859 in v4. Cross-fold auROC is interpretable here and was
  not there.

## Arm A — cross-gene edit direction

Can the **direction** of an edit's effect be predicted for entirely unseen genes?

* Source `mikl_gse173098`, confident subset `|effect/uncertainty| ≥ 1.96`.
* 1,342 sequences, **166 genes**, positive rate 0.2511, 31–36 genes per fold.
* Split: frozen `biological_fold`; no gene and no `group_id` may straddle.
* Features: **delta** k-mer frequencies (mutant − parent), k = 1…3, 84 columns.
* Estimator: L2 logistic regression, C = 1.0.

Low capacity is a **pre-registered prediction**, not a convenience: v4 measured
that high capacity transfers worse across genes. If v5's low-capacity model also
fails, that prediction was wrong and will be reported as wrong.

## Arm B — cross-source finite difference

This is the RNAddress construction itself, and it has never been run.

* Train an absolute-localization model where reliability is highest
  (`moffatt_gse334718`, 0.8818, 46,291 sequences).
* Score `f(mutant) − f(parent)` on `mikl_gse173098` and `tdp43_gse288185` —
  different assay, different cell type, genes never seen in training.
* Features: k-mer frequencies k = 1…3, length-invariant. Estimator: Ridge.
* No test-source outcome is ever used for fitting or tuning.

Two properties make this sound rather than a length-mismatch artifact, and both
are asserted in `tests/mechanism_v5`:

1. Both arms only ever difference sequences of **equal length**, so the O(1/L)
   window-boundary bias is common to both terms.
2. Ridge is linear, so `w·x_m − w·x_p = w·(x_m − x_p)` exactly. Any
   length-dependent offset cancels identically, not approximately.

Mechanistic basis: Mendonsa et al. report that mutations **adding** (AU) or (UA)
repeats induce neurite localization, so a composition-sensitive absolute model
has a real reason to carry edit-direction information. 87.8% of Mikl edits
change AU fraction (sd 0.0197), so the finite differences are non-degenerate.

I deliberately did **not** compute the association between AU delta and measured
effect during diagnostics. That is the very relationship arm B tests, and
measuring it first would have been peeking.

## Controls

* `au_delta_only` — one feature, change in AU fraction. Both arms must beat it,
  or the result is restating the published (AU)n zipcode.
* `shuffled_label_null` — must stay near chance.
* `random_kmer_projection` — 84 seeded random projections, reproducing the
  v2/N4 null that previously **beat** the real mechanism stack.

## Gates

`a1`–`a6`, `b1`–`b4`, `i1`–`i2` exactly as written in the design file. Summary:

* `a1` arm A mean grouped auROC ≥ 0.650; `a2` worst fold ≥ 0.580
* `a3` beats AU-delta by ≥ 0.030; `a6` beats random k-mer by ≥ 0.020
* `a4` shuffled null ≤ 0.550; `a5` seed SD ≤ 0.030
* `b1` Spearman ≥ 0.100 with p < 0.001; `b2` confident-subset auROC ≥ 0.600
* `b3` beats AU-delta Spearman by ≥ 0.020; `b4` same sign in ≥ 4 of 5 folds
* `i1` no gene or component straddles any scored split; `i2` Astrocyte unopened

Two primary hypotheses, `a1` and `b1`, with Holm correction across them.

## Verdict rule

* all a-gates, all b-gates and both i-gates pass → development support; STRONG GO
  still requires the one-time Astrocyte confirmation
* exactly one arm passes all of its gates → `PARTIAL GO - RESTRICTED ZERO-SHOT
  DOMAIN SUPPORTED`, with the restriction named explicitly
* neither arm passes → `NO-GO - END UNIVERSAL ZERO-SHOT RNADDRESS`

## Honest prior, recorded before scoring

Arm A has only 1,342 labels and Mikl sequence-level reliability is 0.4527, so it
is modestly powered. Arm B is a genuine long shot: it asks a composition-sensitive
model trained on 10 genes in one assay to carry edit-direction information into
another assay and cell type. Both are nevertheless well posed and previously
untried. **Failure is an acceptable outcome and will be reported as such.**

## Integrity

* Only `tests/mechanism_v5`, `tests/mechanism_v4` and `tests/mechanism_v2` are
  run. Legacy tests can load protected N-zip or Astrocyte inputs and are
  excluded by construction.
* Writes outside the Mechanism-v5 namespaces are refused; evidence is write-once.
* N-zip outcomes and quarantined TDP EV5 stability data are never accessed.
* Scored exactly once per seed. If both arms fail, v5 closes and no v6 is opened
  on this data.
