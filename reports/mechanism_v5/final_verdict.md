# Mechanism-v5 final verdict

**Verdict: `NO-GO - END UNIVERSAL ZERO-SHOT RNADDRESS`**

Design `configs/mechanism_v5/design.json`
sha256 `404c13581717d288f94d8e2e4eb9cb37df0ed290889dd93368eabf75ceb112c9`,
committed at `70b39db` before any score existed, with one pre-scoring bug fix at
`13505cd`. Scored once per seed. Nothing was tuned after scoring.

## Gate results

| gate | requirement | observed | result |
| --- | --- | --- | --- |
| a1 cross-gene direction | mean auROC ≥ 0.650 | **0.7051** | **pass** |
| a2 worst fold | ≥ 0.580 | **0.6423** | **pass** |
| a3 beats AU-delta | ≥ +0.030 | **+0.0109** | **fail** |
| a4 null inert | ≤ 0.550 | 0.5126 | pass |
| a5 seed stability | SD ≤ 0.030 | 0.0000 | pass |
| a6 beats random k-mer | ≥ +0.020 | **−0.0044** | **fail** |
| b1 transfer correlation | ρ ≥ 0.100, p < 0.001 | **+0.0298**, p 0.0012 | **fail** |
| b2 transfer direction | auROC ≥ 0.600 | **0.5407** | **fail** |
| b3 beats AU-delta | ≥ +0.020 ρ | +0.134 | pass (see caveat) |
| b4 consistent folds | ≥ 4 of 5 same sign | 4 of 5 | pass |
| i1 split integrity | no straddling gene/component | verified | pass |
| i2 holdout sealed | Astrocyte unopened | unopened | pass |

Neither arm passed all of its gates, so the verdict is NO-GO.

## Finding 1 — cross-gene edit direction genuinely works, and this is new

Arm A reached **auROC 0.7051** mean and **0.6423** worst-fold for predicting the
direction of an edit's effect on sequences from **166 entirely unseen genes**,
with a shuffled-label null at 0.5126 and seed SD of exactly 0.0000. Per-fold:
0.698 / 0.689 / 0.755 / 0.741 / 0.642.

This is the first time the project has demonstrated cross-parent generalization
of *edit direction* at real breadth. Mechanism-v2 tested paired ranking at
reliability 0.239; Mechanism-v4 tested transfer on 10 genes. Neither could have
seen this. It is a real effect and it clears its absolute bars.

## Finding 2 — but it is one number, and that number is AU content

A **single feature** — the change in AU fraction — reaches **0.6942** on its own.
The 84-column delta k-mer model adds **+0.0109**, far under the +0.030 bar.

Worse for the mechanism story, a **random projection** of the same delta space
reaches **0.7094**, actually *beating* the real features by 0.0044. If random
directions do as well as chosen ones, nothing specific is being used.

This is now the **third independent reproduction** of the same result by three
different routes:

* Mechanism-v2 control N4: random k-mer null +0.0286 vs the RBPNet/BERT/structure
  stack at +0.0250
* Mechanism-v4 gate g2: 20-column composition 0.9306 vs 1,364 k-mers 0.9503
* Mechanism-v5 gates a3/a6: AU-delta 0.6942, random projection 0.7094, real
  features 0.7051

The signal these assays expose is bulk nucleotide composition. There is no
higher-order zipcode grammar recoverable from them at any capacity.

## Finding 3 — my pre-registered prediction was wrong, and instructively so

I predicted from v4 that **low** capacity would transfer better, since v4's 1,364
features transferred 0.055 worse than 20. v5 used 84 low-capacity delta features
and they still failed to beat one feature.

The prediction was wrong because it misdiagnosed the problem. Capacity was never
the issue. Composition *is* the signal, so there is nothing for any capacity —
high or low — to add. Recording this as a failed prediction rather than quietly
dropping it.

## Finding 4 — the sources disagree on the sign of the AU effect

This is the deepest result and it explains arm B's failure mechanically.

* In Mikl, AU-delta correlates with measured effect at **ρ = −0.1044**.
* The Moffatt-trained model predicts Mikl effects at **ρ = +0.0298**, essentially
  nothing, with confident-subset auROC **0.5407** — chance.

So the AU relationship learned on Moffatt does not carry to Mikl, and Mikl's own
AU association points the *opposite* way to the published (AU)n zipcode
expectation that motivated the arm. Arm A still achieves 0.705 on Mikl because a
fitted model can learn Mikl's own sign — but a rule fitted in one source and
applied to another cannot.

**A universal zero-shot selector requires a rule with a consistent sign across
contexts. These sources do not provide one.** That is a much sharper statement of
why RNAddress fails than "the gates did not pass."

Note that `b3` is marked pass only because +0.0298 exceeds −0.1044 by 0.134. The
model beat a control pointing the wrong way. That is a scoring technicality, not
evidence of transfer, and it must not be quoted as support.

## A non-gated observation, deliberately not claimed

Transfer to `tdp43_gse288185` gave ρ = **+0.2844**, p ≈ 1.1 × 10⁻⁸⁵, n = 4,566,
per-fold [0.568, 0.387, −0.039, 0.525, 0.305].

I am **not** claiming this. Reasons, all of which were fixed before scoring:

* Gates `b1`–`b4` are defined on `mikl_gse173098` alone. TDP43 was declared a
  descriptive secondary output. Promoting it now is precisely the manoeuvre this
  project forbids.
* TDP43 carries **no usable `effect_uncertainty`**, so its reliability cannot be
  assessed and its confident subset is empty (`b2` is undefined, not passed).
* Only 16 genes, and the per-fold range spans −0.039 to +0.568.
* TDP43 is 260 nt, identical to the Moffatt training length, whereas Mikl is
  150 nt. Shared length and assay characteristics are an obvious confound for a
  composition-driven model.

It is logged here as a candidate for a future pre-registration, not as a result.
Any such test would need an independent reliability estimate for TDP43 first.

To be explicit about boundaries: this uses the `tdp43_gse288185` **localization**
outcomes that have been part of the certified development table since
Mechanism-v2. The quarantined **TDP EV5 stability** data was not accessed.

## What v5 changes and does not change

* `FinalShot 98ffc02` NO-GO — unchanged.
* Mechanism-v2, v3, v4 NO-GO — unchanged.
* Astrocyte — sealed and unopened.
* N-zip outcomes and quarantined TDP EV5 stability data — never accessed.

The accumulated statement across five eras is no longer "it does not work." It is:

> Edit direction is predictable across unseen genes at auROC 0.705, but the
> entire effect is one scalar — change in AU content. No higher-order grammar is
> recoverable at any capacity, three separate controls agree, and the sign of
> the AU effect is not consistent between sources. A universal zero-shot
> intervention selector needs a sign-stable rule, and these assays do not
> contain one.

## Status

Mechanism-v5 is closed under its stopping rule, and that rule forbids opening a
v6 on this data. Five eras have now returned NO-GO by five different routes, with
the mechanism of failure measured rather than assumed.

Progress across the project should be read as sharpening, not repetition:
v2 established the paired estimand was unmeasurable (reliability 0.239); v3
measured the ceiling; v4 found a real positive and showed it was composition;
v5 showed the composition effect does generalize across genes but is
sign-unstable across sources. Further work requires new data with a
sign-consistent, uniformly defined, well-replicated readout, as set out in
`reports/mechanism_v3/dataset_landscape.md`.
