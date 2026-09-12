# Mechanism-v3 final verdict and RNAddress feasibility finding

**Verdict: `NO-GO - END UNIVERSAL ZERO-SHOT RNADDRESS`**

Mechanism-v2's NO-GO is preserved unchanged. FinalShot `98ffc02` remains a
permanent historical negative. Astrocyte was never opened.

This document additionally answers the question the earlier experiments never
asked directly: *is the RNAddress gate set reachable by any method on this
benchmark?* The measured answer is no, and the blocker is the benchmark's own
measurement noise, not the representation.

## 1. Complete inventory of what has been tested

### Era 1 — v4 phases (pre-FinalShot)
* Phase A development truth rebuild; a Phase A "strong go" was recorded and later
  superseded.
* Phase B transferable-compiler evaluation: frozen 3UTRBERT representation,
  nested ridge, leakage-safe nearest-neighbour retrieval, equalized pairwise
  decision-set weights, three-seed transfer stability.
* Phase B2 context-residual evaluation and verdict; exact-SNV evidence clarified.

### Era 2 — FinalShot (verdict: NO-GO, commit `98ffc02`)
* Frozen mechanistic protocol and resource audit.
* RBPNet intervention signature cache and frozen feature matrix.
* Frozen representation benchmark; grouped models; locked numerical semantics.
* Direct models, monotone latent M3 models.
* Transfer gates: direct transfer, two M3 transfers, Firefly→GFP, GFP→Firefly,
  leave-Mikl, leave-TDP.
* Controls: direct RBP identity, direct delta-RBP, M3 RBP identity, M3 delta-RBP,
  RBP necessity, trans-context gate, crossed-cell trans-context,
  measurement-head randomization, parent-binding knockouts.
* Distributed-mechanism and small-edit gates.

### Era 3 — Mechanism-v2 (verdict: NO-GO)
Representations: archived geometry (28), RBPNet signed delta (412), pooled
3UTRBERT allele delta (128), local structure delta at 20/50/100 nt (18),
processing-motif delta (8), motif-accessibility delta (8), aligned trans
interactions (4). Families M0–M7; 48 frozen recipes; 720 inner fits; five outer
folds scored once.

Controls actually executed: N0 geometry, N1 edit descriptors, N2 geometry +
source slopes, N3 parent identity (ineligible by construction), N4 random k-mer
projection, N5 bijections (global / source / edit-band / parent), N6 absolute
mutant and absolute reference, N7 broken reference, N8 joint source × edit-band
bijection, N9 structure bijection, M1 parent-aware comparator, block removals
over seven components with Holm, shortcut probes, three-seed replication,
purged transfer (leave-source, within-source, cross-cell, cross-reporter,
large-to-small), sequence-90 and annotated gene-group sensitivities.

Excluded after independent failure: external stability model (failed validation
in both cells, twice); N10 therefore inapplicable and never zero-filled.

### Era 4 — Mechanism-v3 (this document)
* Arm 1: outcome-free published zipcode grammar (let-7 seed, (AU)n, β-actin
  zipcode core, GC-rich retention proxy, CUA-rich transport class). **Failed.**
* Arm N: nonlinear estimator on all 1146 feature columns, pre-registered at
  commit `6704d6b` before any zero-shot score. **Failed all four gates.**

## 2. Mistakes found, and whether fixing them changes anything

### 2.1 Real defect in Mechanism-v3 arm 1 (found and fixed)
The grammar delta is nonzero for only **3.6%** of candidate rows. In the first
run the grammar was compared on all 445 decision sets, including the majority in
which every candidate scores exactly zero and the winner is decided by lexical
`candidate_id`. That measured tie-breaking, not grammar.

Fixed by restricting to the 202 decision sets with ≥2 distinct grammar values
(94 components). Result after the fix:

| model | rank | regret |
| --- | ---: | ---: |
| published grammar | 0.5029 | 0.4957 |
| size heuristic baseline | 0.6200 | 0.4537 |

Rank 0.503 is **chance**. The published zipcode grammar carries essentially no
ranking information for these edits. **Fixing the defect did not change the
conclusion.**

### 2.2 Real design limitation in Mechanism-v2 (cannot be retrofitted)
Mechanism-v2 froze a **linear** paired ranker as its only model class. In the
matched leaky diagnostic the same features under a nonlinear estimator recover
**+0.0218** rank gain versus **+0.0025** for the linear model — roughly eight
times more. Freezing a linear-only grid was a genuine design mistake.

It cannot be repaired inside Mechanism-v2 (post-hoc model changes after outer
scores are forbidden), so it was tested prospectively as Mechanism-v3 arm N.
Arm N then failed anyway — see §4.

### 2.3 Incidents already on record, all cosmetic or pre-result
The Mechanism-v2 incident ledger documents a post-score report-writer `KeyError`,
a pre-model missing-gene sentinel in forensic probes, and an `S64`/`U64` digest
encoding mismatch in the absolute-allele reader. None touched a score, gate,
split, or recipe. Re-auditing confirms no scientific result depended on them.

### 2.4 No mistake explains the failure
The failure is reproduced by controls that contain no mechanism at all:

| model | rank gain | regret gain |
| --- | ---: | ---: |
| Mechanism-v2 primary selector | +0.0250 | +0.0252 |
| **N4 random k-mer projection** | **+0.0286** | **+0.0226** |
| N2 geometry + source slopes | +0.0219 | +0.0110 |

A frozen random projection of 1–4mer counts **matched or beat** the full
RBPNet + BERT + structure + processing stack. No block reached Holm significance
(best: structure, p = 0.035, Holm 0.247). Seed 20260911 turned the whole effect
negative (−0.0095 rank). The paired bootstrap 95% interval for regret gain was
[−0.0076, +0.0592] — it included zero, so the g1 "pass" was a point estimate the
interval never supported.

## 3. Why no method can pass: the measured ceiling

### 3.1 The ranking target is mostly measurement noise
Using the benchmark's own reported per-candidate uncertainty (95.1% of rows have
it; median 4 replicates):

* **Mean within-decision reliability = 0.239.** About **76%** of the
  between-candidate variance in localization effect is measurement noise.
* Outcome semantics are heterogeneous across sources (author WT-normalized log2
  neurite enrichment vs mutant-minus-WT deltas), which the design already flagged.

### 3.2 The leaky ceiling is at the gate threshold
A model allowed to train on **sibling mutants of the same parent in the same
assay** — deliberately leaky, forbidden by the zero-shot contract — achieves:

| leaky setting | rank gain | regret gain |
| --- | ---: | ---: |
| M4 features, linear ranker | +0.0142 | +0.0139 |
| all 1146 features, linear ranker | +0.0025 | +0.0246 |
| all 1146 features, nonlinear | +0.0218 | +0.0450 |
| **g1 requirement** | **≥0.020** | **≥0.010** |

The best leaky configuration clears the rank threshold by **0.0018**. A zero-shot
selector would have to match a cheating model almost exactly *and* additionally
satisfy distributed benefit, leave-source and cross-context transfer, mechanistic
necessity, seed stability, and hard-harm limits. There is no margin for that.

### 3.3 Independent literature agrees
* Zero-shot genomic language models predict held-out MPRA variant effects poorly
  (Pearson ≤ 0.135); supervised/adapted models do much better
  ([Genome Biology 2025](https://doi.org/10.1186/s13059-025-03674-8)).
* Roughly **12%** of reported functional 3′UTR MPRA SNPs are affected by cryptic
  splicing artifacts ([Nat Commun 2025](https://doi.org/10.1038/s41467-025-62000-9)),
  so part of the target may not be localization biology at all.
* State-of-the-art sequence-to-function models still struggle to get variant
  effect *direction* right in context
  ([2026 preprint](https://doi.org/10.64898/2026.03.17.712488)).

## 4. Arm N result (pre-registered, run once)

Zero-shot, whole components held out, three declared seeds:

| seed | rank gain | regret gain | g1 | g2 | g10 |
| --- | ---: | ---: | --- | --- | --- |
| 20260912 | +0.0178 | +0.0160 | fail | fail | fail |
| 20260913 | +0.0350 | +0.0269 | pass | fail | fail |
| 20260914 | +0.0693 | +0.0473 | pass | fail | fail |

Seed-only standard deviation of rank gain ≈ **0.026** against a 0.010 limit. The
point estimate nearly quadruples from seed choice alone. Distributed benefit and
hard harm fail at **every** seed: the apparent average gain is concentrated in a
few components while badly harming the worst decile.

Final arm N gate status: `g1 fail, g2 fail, g9 fail, g10 fail`.

Per the committed stopping rule, Mechanism-v3 closes here. Adding further arms
until one passes would be fishing and is forbidden.

## 5. Verdict

**`NO-GO - END UNIVERSAL ZERO-SHOT RNADDRESS`**

Universal zero-shot mechanism-aware selection of RNA-localization interventions
is not supported. PARTIAL GO is unavailable: the only prospectively named
restricted domain does not pass on its own, and post-hoc domains are forbidden.
STRONG GO additionally requires the authorized Astrocyte test, which was never
opened and is not authorized.

## 6. What would actually be required (not attempted here)

The binding constraint is data, not model architecture:

1. **Replicated, uniformly defined outcomes.** Within-decision reliability must
   rise well above 0.24; that needs more replicates per candidate and one
   consistent effect definition rather than three source-specific semantics.
2. **Splice-aware QC** of the reporter constructs, per the cryptic-splicing
   finding, before any element is called functional.
3. **More independent biological units.** 211 connected components with ~76%
   noise cannot support stable component-level gates.
4. **Prospective wet-lab validation** of a small number of designed edits, rather
   than further reuse of a benchmark already examined across four experiment eras.

Better features or a bigger model will not fix a target that is three-quarters
measurement noise.

## 7. Reproducing this finding

```
python -m src.mechanism_v3.run_pipeline test        # safe Mechanism-v3 tests
python -m src.mechanism_v3.run_pipeline audit       # frozen grammar dictionary
python -m src.mechanism_v3.run_pipeline evaluate    # arm 1, outcome-free grammar
python -c "from src.mechanism_v3.diagnostics import run_diagnostics; run_diagnostics()"
python -c "from src.mechanism_v3.arm_nonlinear import run_arm; run_arm()"
```

Evidence: `results/mechanism_v3/diagnostics/ceiling_analysis.json`,
`results/mechanism_v3/outer/arm_nonlinear_evidence.json`,
`results/mechanism_v3/outer/development_evidence.json`.
