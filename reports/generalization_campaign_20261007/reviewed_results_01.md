# Independent review of completed development results

**NEXT, crossed-cell and represented-cell gates are all NO-GO.** No arithmetic discrepancy explaining the failures was found. A read-only independent reconstruction checked 316 headline, component-weighted comparison, shared-bootstrap, wrong-direction and best-fold calculations; maximum discrepancy was 1.11e-16 against a declared 1e-12 tolerance. No fit, model inference, protected outcome or original-file modification was performed in this review. This audit evaluates reported numerical results, not the complete author count-processing pipelines.

Normalized two-direction candidate-extrema regret is lower when better; uniform is .5. These columns have different evaluation populations and must not be treated as directly interchangeable benchmarks.

| Fixed track | NEXT four-assay regret | Crossed-cell held-gene regret | Same-cell held-gene regret |
|---|---:|---:|---:|
| simple102 | — | .493225 | .497438 |
| base246 | .512255 | .512154 | .499935 |
| raw251 | .500327 | .517409 | .522171 |
| structure262 | .516485 | .495074 | .516943 |
| lookup502 | .502673 | .517049 | .515469 |
| bert502 | .468185 | .514084 | .512165 |
| combined518 | .478262 | .500594 | .508226 |

The strongest NEXT result is BERT: mean gain .028683 versus the frozen best simple comparator, descriptive paired interval [.014732,.042523], gain .044070 versus corrected base and .034488 versus lookup. This is a bounded positive representation association under the tested settings. It is **not a near-complete generalization success**: despite missing the .468 regret cutoff by only .000185, BERT also fails assay breadth, Mikl protection and gain concentration. Astro contributes 71.4% of positive simple-comparator gains; Mikl is harmed by .029317 versus composition, and SRLE remains marginally worse than uniform. Removing Astro leaves only .003797 average simple gain. Combined also has a positive aggregate interval, but 96.2% of positive gains come from Astro, its leave-best-source gain is negative, and adding structure worsens BERT by .010077 on average.

Crossed-cell structure is the strongest informed result there: gain .017080 versus rich base (interval [.002925,.032557]) and .022335 versus raw ([.007555,.039221]), with positive gains after removing the best gene fold. It nevertheless loses to the additive simple comparator by .001849, has regret .495074 rather than the required .48, and fails the distributed simple-comparator gate. BERT is .020859 worse than simple overall. Improvements over a weak rich baseline must not be presented as superior candidate selection to the strongest prespecified control.

The same-cell evaluation reuses the identical 42 frozen source-cell predictors and source-only configurations, adding **zero fitted evidence**. Every informed macro regret exceeds .5. CAD base has regret .473636 versus CAD simple .500446, while Neuro-2a base reverses the result (.526234 versus simple .494430). Selecting CAD or another favorable subset now would change scope after results. These results do not show that missing cell information alone explains the held-gene failures.

The separate canonical paired diagnostic certifies equal allele feature bytes, uses one common-shape call and shared lexical mutant-sequence ties, and evaluates the same chosen allele on both truth menus. It covers all 2,408 exact menus/187 genes. Independently reaggregated means and shared-component intervals match exactly; **every interval includes zero**. Positive advantage means crossed-state regret minus same-state regret.

| Track | Known-state advantage | Descriptive 95% interval |
|---|---:|---:|
| simple | -.005084 | [-.035627,.024797] |
| base | .011031 | [-.025618,.045754] |
| raw | -.005951 | [-.040766,.027980] |
| structure | -.023057 | [-.058888,.010458] |
| lookup | .000313 | [-.032323,.032052] |
| bert | .001554 | [-.029474,.032023] |
| combined | -.008424 | [-.038319,.021808] |

Known-state advantage is therefore not established for these predictors; this does not prove cell state irrelevant. Cell-specific effect spans, measurement noise and other context differences remain. No diagnostic estimates a causal cell effect or biological noise ceiling.

Inferential limits are substantial: the four-assay aggregate weights sources equally but contains only 2 Astro, 6 Moffatt and 1 SRLE biological components, versus 187 Mikl components. One-component SRLE contributes no component-resampling uncertainty; these intervals omit author measurement/count uncertainty and uncertainty over new assays. Repeatedly exposed data, multiple routes, unknown full reporter context and potential unlabeled pretraining overlap restrict claims to development evidence. None demonstrates a novel transport mechanism, calibrated benefit or independent confirmation.

Concrete integrity limitation: the original NEXT/crosscell gate entrypoints do not themselves require a fresh replay receipt or rehash every final derived result. Root completed replay before these gates, this numerical audit pins observed result bytes, and the new known-cell verifier checks the same checkpoints in both states. No evidence here shows that this limitation corrupted the current results. Original crosscell inner replay reuses the canonical scorer and independently reconstructs selection/choice arithmetic; the independent coefficient bound for current crossed **outer** predictions is additionally supplied by known-cell replay. Do not describe the older inner verifier as an independent numerical predictor implementation.

Cell conditioning was already attempted. [V4 source](D:/rnaexpress/src/modeling/v4_decision_models.py:76) defines dataset/assay/reporter/cell contexts, shared global plus context-specific residual ridge heads (lines 142–175), and within-decision-set normalized edit utility (107–115). [Its runner](D:/rnaexpress/src/analysis/run_v4_phaseB_models.py:186) pools both cells outside held biological gene folds. [FinalShot M2](D:/rnaexpress/src/modeling/finalshot_models.py:125) constructs RBP features plus cell-expression interactions; [the direct runner](D:/rnaexpress/src/analysis/run_finalshot_direct_models.py:158) also pools cells outside gene folds. For a block with two distinct expression values, these interactions can represent independent cell-specific slopes, although the penalty couples them and equality of all actual cell contrasts was not assumed. Additive cell intercepts and positive affine measurement heads alone cannot reorder within-cell candidates. A new shared-plus-cell-deviation model would reassess an existing idea with current representations, purges and objectives; it would not introduce a missing conditioning concept. Historical implementation existence is not proof that earlier estimators or verdicts were correct.

Provenance: [numerical_audit_01.json](D:/rnaexpress/reports/generalization_campaign_20261007/numerical_audit_01.json) pins 63 observed gate/decision/comparison/source/protocol/verification inputs; SHA256 `a67693a2d42b98b94fda86ee6e83ae1f5da14536a186d2b8085b1c95103b1217`. These are late observed digests, not retroactive creation-time certificates. It preceded completion of the paired diagnostic; that separately read result JSON has SHA256 `94e90e1f57e59c135d13de183e89feeef04ba5a855fe33448b343706b4feffb7`. The paired CSVs independently reaggregated for this review have hashes:

```text
simple    aaf81905f8f4e45a009bb365857141d2eb19eff099d3c3c70afcfc493262ab71
base      c38281d11bf2489516c3f3bb94fdfebe28852c87fc35010e5ecdf59bab5119f8
raw       4cc42f771e56c761fe6c4cbd4467d2636b0614d48de76bca824e4a02f2a2d3b2
structure aa8c1948ec4ffae8eb1af6e5de532d869e99f544df3481d8a3872673bfc4783d
lookup    e8a0e26b670351df5d7a34ed8924babaf296712e08837928644603d60160ecc2
bert      30fb19efce21283216f9f951a522c04832127cf24c14dce5a05bc63f6a679f34
combined  5c532c09e8e5da1163f8061f7ea1a8575e78b3b036af170ad91995057f8a208a
```

Historical source-only digests: V4 model `e9818f7b9e0b3ac71e5261b6070845d549b23fa1fd6a1bef29268b7bf16f8421`; V4 runner `fa88deb38b550a09f24c92fea40ab1ea2199ff5fac6386f7dceef9f155232b5a`; FinalShot direct runner `a7bae186cb8e2032eaf21c34fe3239811685a8883e971981624ba1ee49001883`. FinalShot model source is also pinned by numerical_audit_01.json. No historical protected outcome or stability table was read.
