# What the project has established — 25 September 2026

**The strongest defensible outcome is B: a reproducible, composition-controlled
SRLE decision benchmark with competitive simple baselines and explicit failure
rates.** Independent confirmation, a specific biological mechanism and complete
novelty remain unestablished. This is an AI-authored technical evidence package,
not student-authored competition prose or a promise of an STS outcome.

The project asks whether small sequence changes can be selected to move RNA
localization in a requested direction, including new biological contexts.
Prediction, selecting the best alternative, avoiding wrong-direction changes,
and transferring across contexts are different requirements. Earlier approaches
often satisfied the first while failing one or more of the others.

## What is complete and what remains open

- State reconstruction: [CURRENT_STATE.md](D:/rnaexpress/CURRENT_STATE.md).
- Provenance: [final SRLE audit](D:/rnaexpress/reports/research_20260921/srle_provenance_final.md),
  **PARTIAL**, with a 24,576-row measurement lineage and six-library manifest.
- Existing-resource assessment: 16 entries; none qualifies as a genuinely
  unexposed compatible resource under the requested standard. Discovery is
  **blocked/not exhaustive**. No external-test protocol or evaluation was run,
  because there is no admitted dataset to which one could be honestly applied.
- Computation: saved prediction metrics reproduced exactly; two fresh isolated
  standard-library packages reproduced 57 and 1,026 numeric values respectively.
  Maximum discrepancies were 1.11e-16 and 3.33e-16. All 69 scoped tests passed;
  16 freezes and 228 original snapshot files remained unchanged.
- Evidence: 73 claim rows cover major historical approaches, successes, failures,
  source ambiguities and exact risk comparators. See the
  [final ledger](D:/rnaexpress/artifacts/research_20260925/claim_evidence_ledger_final.md)
  and its machine-readable CSV/JSON. This synthesizes saved records; it does not
  rerun every historical experiment or every hyperparameter candidate.

There is no fresh model fit, outcome reveal, threshold selection or optimized
subgroup in this delivery. The existing stop rule rules out additional same-data
searches merely to improve the headline. Per-class outputs and original per-unit
records remain available for inspection; this release adds reproducibility, not
another biological success test.

## Why the approaches failed, and what their results still show

| Approach | What went wrong / result retained |
|---|---|
| Original linear pairwise ranking | Unchanged parent features cancel in pairwise differences. Locked rank .566 versus forward .624; no intervention advantage. |
| Parent-by-edit interactions | Fixed development .662 looked promising, but nested selection .588 and seven-seed ensemble .575 were weaker. Favorable optimization did not generalize reliably. |
| Structure, auxiliary labels and pretrained representations | Structure .539, TDP auxiliary .504, SpliceBERT .617, extreme contrast .581, external neural transfer .562, XGBoost direct .492/calibrated .621: none established the required control margin. These are failures of tested methods, not proof that the biology is irrelevant. |
| v2.6 stack and v3 magnitude/extreme heads | Better rank did not mean better decisions. TDP regret worsened; v3 gain .01744 missed .03, oracle top-five was 0/30, and improvements depended on favorable parents. Confidence abstention also failed. |
| N-zip truth reconstruction | Historical coverage and score semantics were not recovered sufficiently: 5,787 versus 5,679 covered designs; SNV-effect MAE .407. Historical modeling results remain recorded but cannot establish a certified biological truth benchmark. |
| v4/FinalShot and mechanism models | Average gains coexisted with weak small-edit transfer, many unimproved units, unstable seeds and gains retained by shuffled/random controls. Biological specificity was not demonstrated. |
| Mechanism v4/v5 reframing | Real absolute prediction and edit-direction signal: within-context auROC .9503; cross-gene direction .7051. Simple composition/AU controls were close or better; cross-assay transfer failed. |
| SRLE order prediction and swaps | This is a positive within-assay result, not a failed approach. Pair and short-mer models improve substantially over composition/random. Pair superiority over short motifs is unestablished; substantial individual failures and shared training experiment limit the claim. |
| Arora external transfer | Regret gain −.146 [−.232,−.060], negative in all four settings. A nuclear/cytoplasmic six-mer score did not transfer successfully to these neuronal reporter choices. |
| SIRLOIN single substitutions | Small positive: regret .44733, but margin .04360 over CCTCCC missed the frozen .05 requirement. Two parents cannot establish broad generalization. |
| Context calibration and robust selection | Original development CI crossed zero. Source-only calibration helped target-only modeling but did not clearly beat a sibling-context predictor. Maximin selection lost to simple averaging. |
| Faraway intron configuration | Primary interaction model lost to simpler intron-pattern controls. Secondary 8-hour quadratic/categorical selectors passed their limited random-comparison gate, but all target genotypes were previously measured and barcodes remain a confound. |
| Shukla and SEERS transfer | Shukla failed with unresolved raw/processed correspondence; SEERS had too few high-quality groups and one biological sample. Lower-quality sensitivity did not rescue transfer. These are not clean proofs of biological nontransferability. |
| mutREL and Wen resources | Admission failed before outcome testing: mutation-event versus isolated-genotype semantics for mutREL; transcript/measurement mapping and a different speckle endpoint for Wen. Unexamined outcomes are not missing positive results. |
| External stability predictor | Both independently tested cell models failed admission (Spearman .0367/−.0271; errors worse than simple baselines). No failed predictor was exported into localization modeling. |

All early N-zip numbers above are historical reported metrics, qualified by the
later truth-reconstruction failure. None is reclassified as confirmation.

## The positive SRLE result, with the failure rate beside it

Pair-model prediction error falls **27.04%** relative to composition
(descriptive 95% interval 20.63–33.78%); short 1–3-mer counts achieve **27.37%**.
The pair-minus-short-mer comparison includes zero. Holding composition fixed
still permits order/motif variation, so this demonstrates information beyond
base totals without identifying an RBP or causal mechanism.

For fixed measured swaps, pair-model normalized-regret gains over exact uniform
choice are **.23103 and .25342** in the two constituent replicates; short motifs
achieve **.21991 and .22129**. These are normalized decision scores, not fractions
of RNA relocated. Pair-minus-short-mer intervals include zero in both replicates.

| Policy | Better in both: decrease / increase | Worse in both: decrease / increase |
|---|---|---|
| Exact matched uniform | 36.27% / 39.21% | 39.21% / 36.27% |
| Composition tie choice | 32.42% / 44.34% | 44.34% / 32.42% |
| Position additive | 43.56% / 47.17% | 30.10% / 31.30% |
| Short 1–3-mers | 50.94% / 54.47% | 25.13% / 22.11% |
| Position pairs | 50.96% / 56.98% | 20.78% / 23.57% |

Pair-model benefit-rate improvements over uniform are **14.69 percentage points**
[11.25,18.08] for decrease and **17.78 points** [14.08,21.57] for increase.
The comparison fixes candidate identity across the two replicates. These are
equal-composition-class averages across 60 classes/592 parent neighborhoods;
neighborhoods overlap. They are not unweighted proportions of independent
biological experiments. Intervals condition on fitted models and shared source
data, omitting training uncertainty. Wrong direction describes score movement,
not toxicity. Candidates exclude unchanged parents and swaps allocated to training.

![SRLE fixed-choice benefit and failure rates](D:/rnaexpress/results/research_20260921/srle_uniform_risk_20260924.png)

The figure was re-inspected for legibility and retains all comparators. Its
original source, full-precision table, PNG and SVG are included in the package.

## What the evidence says about the scientific questions

1. **Why are short features competitive?** In several datasets, composition and
   short motifs capture much of the available predictive signal with few degrees
   of freedom. In SRLE, 2/3-mer counts encode order despite unchanged base totals.
   This is consistent with local sequence regularities; it does not prove a
   particular motif-binding mechanism or that all remaining signal is composition.
2. **Is there order information beyond composition?** Yes within SRLE's recorded
   held-out sequence task. The 27% error improvement survives exact-composition
   comparison and the original conditional permutation test. It is not evidence
   for a transferable higher-order biological rule.
3. **Where does it help?** Interpolation among measured alternatives in represented
   composition classes, with lower average regret and improved matched-uniform
   benefit rates. Absolute prediction in represented Moffatt parents is also strong.
4. **Where does it fail?** Individual decisions remain frequently wrong; superiority
   over simple short motifs is absent; frozen external and mechanism gates failed.
   Mapping-limited studies must be separated from valid tests of transfer.
5. **Are gains concentrated in sequence regimes?** Historical unit/fold variation
   and failed leave-best-unit tests establish heterogeneity. SRLE class outputs
   are retained, but no prospectively validated motif-defined winning regime is
   established. A favorable posthoc subset would need a new independent test.
6. **Do assays differ?** Yes, their measured endpoints, reporters and associations
   differ. Moffatt-to-Mikl transfer is weak; Arora transfer is negative; SIRLOIN
   has a small positive below its gate. Comparisons are not interchangeable.
7. **Is failure compatible with context-specific grammar?** Yes, but also with
   assay/measurement differences, limited biological units and distribution shift.
   Current evidence cannot distinguish those explanations causally. Historical
   phrases such as “no grammar recoverable at any capacity” overstate the results.
8. **How much is reliability limiting?** SRLE replicate Pearson .820 is a descriptive
   score-level repeatability measure. Historical within-decision reliability .239,
   Shukla mean replicate Spearman −.00417 and Faraway .137–.260 concern different
   estimands/cohorts. They do not define one universal ceiling. Two constituent
   replicates and uncertain source processing cannot identify an irreducible
   decision-error limit or prove that no better method could exist.

The distinguishing evidence for a transferable rule would be a frozen selector
beating strong simple controls, with acceptable wrong-direction risk, on an
authoritatively mapped and genuinely independent compatible set of measured
alternatives. Reusing labels, another random split or another constituent
replicate cannot provide that evidence.

## Next three tasks, in order

1. **Finish the bounded benchmark write-up and explanation.** Use the supplied
   replay, comparative figure, all-claim ledger and provenance qualification;
   keep the student's own scientific interpretation and disclose AI assistance.
   This can proceed with existing evidence and does not depend on a new positive.
2. **Resolve the exact Table5 production records if authoritative material becomes
   available.** The concise questions are prepared but unsent. Do not substitute
   another fitted normalization or a favorable correlation for that record.
3. **Only if an eligible independent resource becomes available, admit it and
   freeze a single external test before outcomes.** Include composition, short
   motifs, geometry and matched-context controls, independent-unit uncertainty
   and wrong-direction risk. The current inventory does not justify that step.
   A careful prior-art assessment is also needed before any novelty claim.

No money was spent, no schedule created, no external message sent and no new
model trained. The zero-cost computational-only constraint is fully understood.

## Do-not-touch list and confidence gaps

Keep Astrocyte sequences/features/outcomes, N-zip outcomes, TDP EV5 stability,
Arora replicates 3/4, SIRLOIN C3/4 and all B, Shukla reserved 4–6 and raw runs,
the 22 context confirmation groups and unused calibration labels, Faraway
original confirmation patterns/later-condition/perturbation/stability outcomes,
and unadmitted mutREL/Wen outcomes closed. Preserve every historical freeze,
negative gate, source artifact and unrelated user edit. No same-data v6 rescue,
unfiltered pytest, purchases, scheduled tasks or unrequested external contact.

Arithmetic and direct Table5 mapping are high-confidence within the verified
scope. Full source production, physical sample identity, biological independence,
causal mechanism, broad utility and novelty are unresolved. The safe legacy test
previously passed 113 tests; its historical preservation audit had a pre-existing
user modification. This turn did not rerun that writing test target or repair it.

The earlier automatic approval review rejected new-dataset discovery, citing
potential biological misuse. That action was not retried or bypassed. Therefore
the inventory result is **not an exhaustive claim that no suitable public
validation dataset exists**. Outcome A remains unavailable in this execution;
the bounded evidence package is complete, while the broad research goal is not.
