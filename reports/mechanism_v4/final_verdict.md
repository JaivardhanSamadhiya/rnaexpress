# Mechanism-v4 final verdict

**Verdict: `NO-GO - END UNIVERSAL ZERO-SHOT RNADDRESS`**

Design `configs/mechanism_v4/design.json`
sha256 `93a32d4d07076c64e1181f2b245cd393002e652daf0a20ff5c3691b673fdd595`,
committed at `e2b46e6` before any score existed. Scored once per seed. No gate,
threshold, feature set, split, label or estimator was changed after scoring.

Primary source `moffatt_gse334718`: 46,291 unique 260-nt sequences, 10 genes,
8 distinct parents, positive rate 0.386.

## Gate results

| gate | requirement | observed | result |
| --- | --- | --- | --- |
| g1 T1 predictive | auROC ≥ 0.80 and ρ ≥ 0.50 | **0.9503**, ρ **+0.799** | **pass** |
| g2 T1 beats composition | ≥ +0.030 auROC | **+0.0197** | **fail** |
| g3 null inert | ≤ 0.550 | 0.5006 | pass |
| g4 T2 zero-shot | auROC ≥ 0.700 | 0.6980 | **fail** |
| g5 T2 worst fold | ≥ 0.600 | 0.5758 | **fail** |
| g6 T2 beats composition | ≥ +0.030 auROC | **−0.0549** | **fail** |
| g7 T2 seed stability | SD ≤ 0.020 | 0.0282 | **fail** |
| g8 split integrity | no straddling component | verified | pass |
| g9 holdout sealed | Astrocyte unopened | unopened | pass |

Per the pre-registered rule, a `g2` failure forces NO-GO.

## The three findings, stated plainly

**1. Sequence does predict absolute localization, strongly and reproducibly.**

T1 reached auROC **0.9503** and Spearman **+0.799** for unseen variants of a
3′UTR already represented in training. This is stable to four decimal places
across seeds (0.9503 / 0.9506 / 0.9504) and tight across folds
(0.9482–0.9533), with a shuffled-label null at 0.5006. It exceeds the 0.81–0.83
published on the Mikl source.

This is a real positive result. It is the first one this project has produced.
It says the reframe was correct about *where* the signal is: absolute per-sequence
localization is measurable (reliability 0.88) and learnable, whereas
within-parent intervention differences were not (reliability 0.239).

**2. But that prediction is nucleotide composition, not a learned grammar.**

A 20-column mononucleotide-plus-dinucleotide baseline already reaches **0.9306**.
The full 1,364-column k-mer model adds only **+0.0197**, below the pre-registered
+0.030. So roughly 93% of the achievable discrimination is composition — almost
certainly AU-richness, consistent with the published (AU)n zipcode.

`g2` existed precisely to stop a composition effect being credited as
mechanism-aware RNA addressing. It did its job. RNAddress claims to select edits
by mechanism; "this fragment is AU-rich" is not that claim.

**3. Cross-gene zero-shot transfer does not hold, and the rich features actively hurt.**

T2 mean auROC was 0.6980 against a 0.700 bar, with worst fold 0.5758. Per-fold
values were 0.819 / 0.642 / 0.847 / 0.607 / 0.576 — each fold is a different gene
with a different baseline, and performance tracks the gene, not the model.

The decisive number is `g6`: composition-only **beat** the full k-mer model on
T2 by 0.055 (0.7529 versus 0.6980), and by 0.087 and 0.097 on the replication
seeds. With 1,364 features over 10 genes, the richer representation memorizes
gene-specific k-mer fingerprints and transfers worse than counting nucleotides.
T2 seed SD was 0.0282, above the 0.020 limit.

## One observation I am deliberately not converting into a pass

Composition-only T2 means were 0.7529 / 0.7284 / 0.7667, which would clear
`g4`'s 0.700 bar. Composition was pre-registered as a **control**, not the
primary, and promoting a control to primary after seeing scores is exactly the
manoeuvre this project's rules forbid. I am not doing it.

For the record it would not have rescued the verdict anyway: composition's worst
folds were 0.5946 / 0.5917 / 0.6044, failing `g5`'s 0.600 bar in two of three
seeds. It is logged here as a hypothesis for any future pre-registration, not as
a result.

## What v4 changes and does not change

* `FinalShot 98ffc02` — `NO-GO — END ZERO-SHOT RNADDRESS` — unchanged.
* Mechanism-v2 NO-GO — unchanged.
* Mechanism-v3 NO-GO — unchanged.
* Astrocyte — sealed and unopened. `open_holdout` refuses unconditionally.
* N-zip outcomes and quarantined TDP EV5 stability data — never accessed.

What v4 adds is a sharper statement of *why* the project idea fails, replacing
the earlier vaguer "it doesn't work":

> Neurite localization is encoded in 3′UTR sequence, and it is encoded well
> enough to predict at auROC 0.95 within a known context. But the encoding that
> is recoverable from these assays is dominated by bulk nucleotide composition,
> it does not generalize to unseen genes at the pre-registered bar, and
> higher-order features degrade rather than improve transfer.

That is a coherent scientific conclusion rather than a null. Composition-level
determinants are real and were independently reported by the source authors,
whose own models also found plain 4-mers beating 218 RBP motif scores.

## Honest limits of this particular failure

Declared in the protocol before scoring, and binding now:

* Moffatt has only **10 genes and 8 parents**. T2 is low-powered by construction.
  Its failure is **weaker** evidence than the Mechanism-v2 failure and must be
  read as *inconclusive-or-negative*, never as proof of impossibility.
* Moffatt outcomes contributed to v2/v3 paired metrics, so they are not pristine.
  Development evidence alone could never have been a STRONG GO.
* A genuine test of cross-parent transfer needs many more independent parents
  with an absolute readout than any permitted source here provides. The options
  are set out in `reports/mechanism_v3/dataset_landscape.md`.

## Status

Mechanism-v4 is closed under its stopping rule. Four experiment eras
(FinalShot, v2, v3, v4) have now returned NO-GO on the universal zero-shot
claim, by four different routes, with the mechanism of failure now measured
rather than assumed.
