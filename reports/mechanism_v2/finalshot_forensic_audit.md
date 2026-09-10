# FinalShot forensic audit for Mechanism-v2

Status: first checkpoint, 9 September 2026. Archived prediction recomputation has
matched all four model-family summaries; additional diagnostics are in progress.
This is an exploratory retrospective audit, not a revision of FinalShot's gates.

## What failed, and what can actually be concluded

The selected old model improved average rank by 0.042294418 and normalized regret
by 0.040094443 over geometry. Only 54.4601% of 213 biological units improved, below
the original 55% threshold. This near miss is not the main justification for the
NO-GO: several independent requirements failed substantially.

| Test | Archived result | Interpretation |
|---|---|---|
| 2–5 nt edits | regret gain +0.012902 | Some favorable small-edit evidence |
| 6–10 nt edits | regret gain −0.030535 | Clear harm, beyond the −0.005 limit |
| Combined 2–10 nt | rank −0.021293; regret −0.005723 | No general small-edit bridge |
| Leave source | regret +0.069215; six favorable direction tasks | Positive source-transfer evidence |
| Crossed cell | rank −0.004680; regret −0.001294 | Transfer not established |
| Crossed reporter | rank +0.005105; regret −0.021906 | Transfer not established |
| RBP identity disruption | 78.84% of regret gain retained | RBP-specific necessity failed |
| Delta donor control | 100.28% of regret gain retained | Intervention-alignment necessity not established; null flawed |
| Parent-binding removal | regret +0.035829; rank +0.056341 | Parent summaries not necessary in aggregate |
| Trans removal comparison | crossed-cell regret difference +0.001199 | Insufficient benefit to retain trans mechanism |

Sources: preserved `results/finalshot/m0_m3_summary.json`,
`grouped_gate_summary.json`, `transfer_summary.json`, and consolidated control
reports. New independently recomputed tables are under
`results/mechanism_v2/forensics/`; claims based only on old summaries are not
misrepresented as newly replayed training.

These results establish failure to support the intended universal mechanism.
They do **not** uniquely identify a biological cause. Weak assay compatibility,
human-trained RBP priors, missing proteins, normalized profile summaries, assay
processing artifacts and geometry shortcuts are plausible, separable hypotheses.
The new experiment must test them, not declare them proven explanations.

## Actual protocol and implementation defects

1. **Mikl matching cap:** initial freeze `30c89a3` required at most two candidates
   per gene/stratum and at least four per within-gene subset. These cannot both
   hold. Git shows only the sigmoid clarification in `ac0443e`; no cap supersession.
   The implemented uncapped estimate (+0.015818 rank; +0.017845 regret) is preserved
   but qualified. The literal-cap sensitivity has **zero evaluable subsets**, not
   a zero effect or a failed numerical threshold. Neither interpretation is
   silently rebranded as the unique preregistered one.
2. **Old delta null:** cycling donors within unequal units is not a permutation.
   It can also move covariates across old folds. It uses no donor outcomes, but
   changes the empirical feature multiset and is transductive at the covariate
   level. New controls use exact partition-local bijections, with ineligible
   cross-unit derangements recorded explicitly. The independent identity control
   already failed, so fixing this defect does not rescue the old mechanism claim.
3. **Tie ambiguity:** code uses the 0.002 regret window, then rank and Good@3
   before simplicity. Prose also implied simplicity immediately within the
   window. Archived selections remain M1/M2/M3/M1/M1. The new implementation has
   one tested total order; there is no retrospective old-model reselection.
4. **Head randomization:** the September 6 pooled-plus-macro conjunction was not
   in the September 2 protocol. Pooled MSE/correlation worsened, but equal-head
   correlation improved. Report mixed evidence, not a prospectively failed
   criterion invented later. The original transfer-harm limit independently
   failed for two TDP direction tasks.
5. **Numerical reproduction:** repeated fits agreed within each tested runtime,
   but old sparse predictions were not reproduced across runs at 1e−8. New
   metric recomputation agrees; this is not proof of training bitwise identity.

## Scope and audit coverage

All 238 old release artifact hashes passed. The new write-once preservation
manifest covers 244 artifacts, including the release inventory itself and reused
development/matrix inputs. It is anchored in Git, not advertised as an operating-
system write lock. Per-checkpoint caches need individual rehashing before reuse.

| Requested diagnostic | Current evidence / remaining work |
|---|---|
| Overall, source, unit, direction, model family | Recomputed from archived predictions |
| Size, mutation class, parent subsets | New retrospective subset recomputation |
| Unit uncertainty/distribution | Paired-direction source-stratified bootstrap |
| Cell/reporter/source transfers | Archived results reviewed; prediction replay remains |
| Identity, delta, parent, trans, head controls | Archived implementation/results reviewed; new corrected nulls tested on synthetic cases |
| Prediction shortcut reconstruction | Fixed grouped Ridge/forest probes specified; results pending |
| Latent nuisance decoding, partial R² | Pending; exploratory, not mechanistic proof |
| Near-sequence/gene-family sensitivity | New grouping checks pending on full development table |

No N-zip outcome or Astrocyte data has been accessed. Astrocyte remains sealed.
