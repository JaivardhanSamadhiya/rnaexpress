# RNAddress-Mechanism-v4 frozen protocol

This document and `configs/mechanism_v4/design.json`
(sha256 `93a32d4d07076c64e1181f2b245cd393002e652daf0a20ff5c3691b673fdd595`)
together are the controlling specification for a single scored evaluation. Both
are committed before any score exists.

Nothing here authorizes Astrocyte access. `src/mechanism_v4/io.py::open_holdout`
refuses unconditionally.

## Why v4 exists, and what it does not do

Mechanism-v2 and Mechanism-v3 both closed
`NO-GO - END UNIVERSAL ZERO-SHOT RNADDRESS` on the *within-parent
intervention-ranking* estimand. Those verdicts stand and are not revisited. The
historical FinalShot conclusion `NO-GO — END ZERO-SHOT RNADDRESS` also stands
unchanged.

The v3 diagnostics established that the blocker was measurement reliability, not
representation:

| quantity | value |
| --- | --- |
| paired within-decision outcome reliability | **0.239** |
| leaky all-feature nonlinear ceiling (rank gain) | +0.0218 |
| gate requirement (rank gain) | 0.020 |

Differencing two nearly identical sequences cancels the biological signal while
compounding assay noise. So v4 asks a different question, on the same permitted
data, chosen because its measured reliability is adequate:

| source | outcome semantics | sequence-level reliability |
| --- | --- | --- |
| `moffatt_gse334718` | absolute WT-normalized log2 neurite enrichment | **0.8818** |
| `mikl_gse173098` | mutant minus matched-WT (already a difference) | 0.4527 |
| `tdp43_gse288185` | mutant minus WT, no usable uncertainty | not estimable |

Only Moffatt carries an absolute per-sequence outcome with usable uncertainty, so
it is the sole primary source. Using Mikl or TDP43 would re-pose the failed
differenced estimand.

## Inventory, fixed before scoring

* 46,291 unique 260-nt sequences; 10 components; 10 genes; 8 distinct parents.
* Positive rate 0.3861 under the pre-registered label.
* Frozen `biological_fold` values 0–4, reused unchanged from Mechanism-v2.

## The two estimands

**T1 — within-parent design.** Predict the absolute localization of unseen
variants of a 3′UTR whose other variants were seen in training. Split:
stratified 5-fold inside each gene, unioned across genes. Not zero-shot. This is
the practically useful "design a localization element in a known context" task.

**T2 — cross-parent zero-shot.** Train on some genes, predict sequences from
entirely unseen genes, grouped by `group_id` on the frozen folds. This is the
actual universal RNAddress claim.

## Declared weakness of T2, stated before scoring

Moffatt contains only **10 genes and 8 distinct parents**. T2 therefore has five
grouped folds over very few independent units, and the per-fold positive rate
ranges from 0.077 to 0.859 because each fold is a different gene with a
different baseline. T2 is consequently **low-powered by construction**.

This is pre-registered so it cannot be used as an excuse afterwards: a T2 failure
here is **weaker** evidence than the Mechanism-v2 failure was, and must be
reported as *inconclusive or negative*, never as proof of impossibility. A T2
success on 10 genes would likewise require the sealed holdout before any
universal claim.

## Features and controls

* Primary: sliding-window k-mer counts for k = 1…5, 1,364 columns, from the
  ACGT-normalized sequence alone.
* Composition control: k = 1…2 only, 20 columns. The primary must beat this by
  ≥ 0.030 auROC, or the result is only nucleotide composition.
* Shuffled-label null: must stay ≤ 0.550 auROC.
* No outcome-derived, parent-identity, gene-name, source-label or split-index
  feature may enter any model.

The label definition (significant neurite enrichment versus all others) matches
the definition used by the Mikl source paper, whose published models reached
auROC 0.81–0.83. That paper also found plain 4-mers (0.83) beat 218 RBP motif
scores (0.81) — independently reproducing this project's own N4 random-k-mer
finding. Reported v4 auROC is therefore interpretable against that benchmark,
with the caveat that the source and split differ.

## Gates

`g1`–`g9` as written in the design file. Summary:

* `g1` T1 auROC ≥ 0.80 and Spearman ≥ 0.50
* `g2` T1 beats composition by ≥ 0.030 auROC
* `g3` shuffled-label null ≤ 0.550
* `g4` T2 mean auROC ≥ 0.700
* `g5` T2 worst fold ≥ 0.600
* `g6` T2 beats composition by ≥ 0.030
* `g7` T2 seed SD ≤ 0.020 across seeds 20260912/13/14
* `g8` no component straddles train and test in any scored split
* `g9` Astrocyte never opened

## Verdict rule

Development evidence alone can never be a STRONG GO.

* `g1`, `g2` or `g3` fails → `NO-GO - END UNIVERSAL ZERO-SHOT RNADDRESS`
* all of `g1`–`g9` pass → development gates passed; STRONG GO still requires the
  one-time Astrocyte confirmation after a separate committed pre-holdout freeze
* T1 block passes but a T2 gate fails →
  `PARTIAL GO - RESTRICTED ZERO-SHOT DOMAIN SUPPORTED`, and the claim must state
  explicitly that it is restricted to within-parent design

## Prior exposure

Moffatt absolute outcomes contributed to the paired regret and rank metrics
examined during Mechanism-v2 and v3, so they are not pristine, although they were
never examined under a sequence-level classification estimand. The sealed
Astrocyte holdout remains the only uncontaminated confirmation available.

## Integrity

* Only `tests/mechanism_v4` and `tests/mechanism_v2` are ever run. Legacy tests
  can load protected N-zip or Astrocyte inputs and are excluded by construction.
* Writes outside the Mechanism-v4 namespaces are refused. Evidence records are
  write-once: identical replay allowed, a differing record is an error.
* N-zip outcomes and quarantined TDP EV5 stability data are never accessed.
* Scored exactly once per seed. No gate, threshold, feature set, split, label
  definition or estimator may change after any score is observed. If the gates
  fail, v4 closes.
