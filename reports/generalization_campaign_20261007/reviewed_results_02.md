# Independent review: endpoint alignment and similarity exclusion

**Both experiments remain NO-GO; no arithmetic error explaining their failures was found.** Independent reconstruction from completed admitted decision metrics checked 1,123 numerical values, 257 booleans and 76 identities, including shared-component/family bootstrap intervals, source weighting, error harm, matched controls and best-fold removal. Maximum discrepancy was 8.33e-17 against the declared 1e-12 tolerance. All 123 observed input files were unchanged before/after. This review performed zero fits, model calls, feature reads or protected-outcome reads.

Regret is component-weighted, then equally averaged across sources/cells; lower is better and uniform is .5. These two evaluation populations differ and must be assessed separately.

| Fixed representation | Original four-source regret | Endpoint-aligned regret | Matched alignment gain | Final aligned gate |
|---|---:|---:|---:|---|
| base246 | .512255 | .473306 | +.038949 | NO-GO; control |
| raw251 | .500327 | .465836 | +.034491 | NO-GO; control |
| structure262 | .516485 | .481686 | +.034798 | NO-GO |
| lookup502 | .502673 | .495854 | +.006819 | NO-GO; control |
| bert502 | .468185 | .481025 | -.012840 | NO-GO |
| combined518 | .478262 | .483913 | -.005652 | NO-GO |

Base, raw and structure meet the fixed matched alignment increment and leave-best-source conditions. The strongest aggregate aligned result is **raw**, the accessibility-off motif control: gain .031033 versus the historical best simple comparator, descriptive shared-component interval [.010860,.054890]. It crosses the .468 regret threshold but still fails the three-source improvement criterion versus historical interaction_3 and Moffatt avoidable-error protection: harm .083333 versus interaction_3 exceeds the allowed .05. Raw is not eligible for a biological-feature claim. Base similarly has Moffatt avoidable harm .125000. Neither result should be reported as a successful gate or demonstrated mechanism.

The informed additions do not survive their required matched controls. Aligned structure is .015851 worse than aligned raw. Aligned BERT is .007720 worse than aligned base; its .014829 improvement over lookup comes entirely from Moffatt while all other source gains are negative, so leave-best-source fails. BERT alignment also worsens its original result by .012840. Combined is worse than aligned structure by .002227 and aligned BERT by .002888. Alignment is therefore a bounded useful modeling observation for some representations, not a generally beneficial biological correction.

There is only one nuclear source, so endpoint sign is inseparable from study, reporter and cell differences. Holding SRLE trains only projection sources; verified predictions then equal the negative of the matched unflipped model rather than constitute learned nuclear-endpoint transport. Projection enrichment is not equivalent to total cytoplasmic abundance. The two Astro, six Moffatt and single SRLE components cannot support the same uncertainty claims as 187 Mikl genes; single-component SRLE has no between-component bootstrap uncertainty. This exposed-data follow-up was motivated by prior polarity results and cannot overturn that earlier NO-GO or establish independent confirmation.

| Similarity-excluded track | CAD to Neuro-2a regret | Neuro-2a to CAD regret | Mean regret | Gain versus matched simple | Final gate |
|---|---:|---:|---:|---:|---|
| simple102 | .508748 | .493324 | .501036 | .000000 | NO-GO; control |
| base246 | .499504 | .522023 | .510763 | -.009727 | NO-GO; control |
| raw251 | .491953 | .522793 | .507373 | -.006337 | NO-GO; control |
| structure262 | .494316 | .510416 | .502366 | -.001330 | NO-GO |
| lookup502 | .515259 | .522113 | .518686 | -.017650 | NO-GO; control |
| bert502 | .516185 | .504977 | .510581 | -.009545 | NO-GO |
| combined518 | .515062 | .487160 | .501111 | -.000075 | NO-GO |

All seven means exceed .48 and every track has at least one crossed cell worse than uniform. No informed route improves the matched simple control on average; all gene- and family-bootstrap intervals for the informed comparisons with simple, base and their feature controls include zero. Structure gains .008397 versus rich base (family interval [-.003719,.021697]), but its remaining gain after removing the best fold is -.003855; versus raw its gain is .005007 with remaining gain -.006490. Combined gains .009652 versus base but -.000075 versus simple, with a cell reversal; its .009470 advantage over BERT falls below the prescribed .01 increment. Reporting only a favorable cell, weak comparator or fold would change the declared scope.

The fixed graph checks 9,318 exact original 150-nt alleles, links 187 genes into 184 families, has four direct gene edges/20 close nonidentical allele pairs and a largest family of four. The threshold is global unit-cost Levenshtein distance <=30/150, **not** 90% ungapped identity, evolutionary homology, local similarity or absence of distant relationships. Additional outer exclusions are 26/0/86 source rows in each direction; all six outer/12 inner supports remain nonempty, and all 13,781 target rows/full menus remain. Family-correlated resampling retains an equal-gene point estimand and does not provide independent-study or measurement uncertainty.

The stricter purge has mixed descriptive effects relative to the unchanged original crossed evaluation: regret improves by .010036 for raw, .003503 for BERT and .001391 for base; it worsens by .007811 for simple, .007292 for structure, .001637 for lookup and .000517 for combined. These are fixed same-roster sensitivity comparisons, not criteria for choosing a favorable similarity threshold. The previously positive structure-versus-base result weakens under this purge; no broader sequence-family-independent success emerges. Absence of success is confined to the fixed representations, readout and exposed assay, not proof that all conservation/context methods must fail.

These experiments reused immutable features and required 240 alignment plus 294 similarity fits, with source-only selection and one numerical thread. They added no biological measurements. Independent replay PASS covers all 216 alignment inner/24 outer checkpoints (maximum independent score error 9.33e-15) and 252 similarity inner/42 outer checkpoints (3.02e-14). The numerical-inner gap identified in review01 for the original crossed experiment is now closed by the additive [crosscell score audit](D:/rnaexpress/results/generalization_campaign_20261007/crosscell_numeric_score_audit_01.json): all 252 inner/42 outer models, exact source selections/choices and zero saved-outer error, with maximum independent arithmetic error 2.49e-14. It does not add new fitted or biological evidence.

The gate calculations match their frozen protocols. No concrete numerical or weighting flaw was found in these outputs. Full reporter context, original author replicate/count estimators, study confounding, exposed-data route multiplicity and new-assay uncertainty remain substantive limits; the aggregation audit does not certify every author pipeline or causal biology. The similarity verifier binds current result hashes; alignment's additional canonical replay and this review pin observed current bytes. Observed postfit hashes do not become retroactive creation-time certificates.

Provenance: [numerical_audit_02.json](D:/rnaexpress/reports/generalization_campaign_20261007/numerical_audit_02.json), SHA256 `43afb170782fb3f24479cb181cff071035cf38d659b792e486c8f72e913adf50`, contains every reconstructed check/comparison and all 123 input digests, including protocols, sources, gates, decisions, controls and replay receipts. Existing protocols, sources and outputs were preserved; only this report and the new audit JSON were written.
