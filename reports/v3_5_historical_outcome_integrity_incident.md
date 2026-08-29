# RNAddress v3.5 historical N-zip outcome-integrity incident

**Analysis class:** POST-PHASE-3 DIAGNOSTIC / NEW-PROTOCOL DEVELOPMENT

**Status:** IMMEDIATE STOP TRIGGERED

**Date:** 2026-08-29

## Executive finding

The N-zip publication workbook contains a systematic sentinel pattern that the historical RNAddress reconstruction treated as a measured localization effect. In Supplementary Table 2b, all 491 rows with a missing DESeq2 adjusted P value have `Mean_log2ratio_NeuriteSoma_WT` equal to exactly `0.0`; there are no zero-valued rows with a finite adjusted P value and no nonzero rows with a missing adjusted P value.

The historical pairing code converted this column directly with `float(...)` and retained the zero as an outcome. It did not use the missing adjusted P value to mark the localization value as filtered or unresolved. Among the 4,395 retained exact-SNV rows, this affects 406 mutant outcomes. Two retained WT parent constructs also have the same zero-plus-missing-P-value pattern, propagating an unresolved parent value to 570 SNV rows. In total, 951 retained SNV rows have an unresolved mutant or parent measurement under this diagnostic, including 25 where both are unresolved.

This is a historical **outcome-state mapping error**: a source-table filtered/unresolved state was mapped to a numerical measured-null effect. The Phase 3.5 prompt requires an immediate stop if a historical mapping error is discovered. No corrected benchmark, oracle-identifiability calculation, direction analysis, shortlist analysis, or model reassessment has been performed.

## Source evidence

Primary publication: *Massively parallel functional dissection of 3′ UTRs in neurons*, DOI `10.1038/s41593-022-01243-x`.

Primary MPRA accession: `E-MTAB-10902` / ENA study `ERP133202`.

Publication workbook:

`data/raw/nzip/supplementary/41593_2022_1243_MOESM2_ESM.xlsx`

SHA-256:

`15560b562c86c3d8fea8611154c4b0504a9528051b6038c19ff96bb47cd9fec9`

The relevant source sheet is `Supp_Table_2b`. Its documented fields include the pooled WT-PCN neurite/soma DESeq2 log2 ratio and adjusted P value.

Observed cross-tabulation over all 6,266 secondary-library rows:

| Condition | Rows |
|---|---:|
| ratio exactly 0 and adjusted P missing | 491 |
| ratio exactly 0 and adjusted P finite | 0 |
| ratio nonzero and adjusted P missing | 0 |

The publication reports that only 5,679 of 6,266 mutagenized constructs passed the read-coverage rule. The exact-zero/missing-P pattern is therefore consistent with filtered or unresolved constructs, not 491 independently estimated effects that all equal exactly zero.

## Historical RNAddress behavior

Historical reconstruction file:

`src/pairing/reconstruct_nzip.py`

The code reads `Mean_log2ratio_NeuriteSoma_WT`, converts it directly to a floating-point value, and calculates:

`delta_localization = mutant_localization - parent_localization`

It checks sequence identity, exact single-base differences, three-alternative coverage, and ambiguous construct keys, but it does not reject or flag the zero-plus-missing-adjusted-P state.

The resulting historical file is:

`data/processed/nzip_snv_intervention_pairs.csv.gz`

Historical retained-row impact:

| Diagnostic | Rows |
|---|---:|
| retained exact SNVs | 4,395 |
| unresolved mutant outcome represented as zero | 406 |
| unresolved parent outcome represented as zero | 570 |
| unresolved mutant or parent | 951 |
| both mutant and parent unresolved | 25 |
| mutant unresolved only | 381 |
| parent unresolved only | 545 |

The two unresolved WT parent constructs are:

* `ENSMUSG00000015222|Map2|5`
* `ENSMUSG00000061518|Cox5b|6+7`

An unresolved WT parent constant does not change within-parent ordering if every mutant measurement is otherwise valid, but it invalidates raw effect magnitudes, headroom, selected measured utility, and cross-parent magnitude interpretation. Unresolved mutant values can directly alter within-parent ranks, regret, oracle neighborhoods, training targets, controls, and model selection.

## Frozen recommendation/oracle diagnostic

None of the 30 nominal pooled oracle mutants has the unresolved-mutant pattern. Four parent-direction oracle records belong to the two unresolved-parent contexts because each affected parent contributes two directions.

Nevertheless, unresolved rows were eligible training and recommendation candidates. Number of 30 frozen recommendations involving an unresolved mutant or parent value:

| Frozen model | Decisions |
|---|---:|
| v2.6 | 6 |
| Phase 3 development-best v3 | 5 |
| strongest forward 3UTRBERT absolute Ridge | 5 |
| metadata baseline | 13 |

These counts are diagnostic only. They do not constitute corrected performance estimates.

## Raw-data reconstruction status at stop

The raw experiment is technically reconstructable in principle. The primary untreated mutagenized landscape has three biological neurite/soma pairs:

| Compartment | Replicate | ENA run | Compressed bytes | MD5 |
|---|---:|---|---:|---|
| neurite | 1 | ERR7337821 | 1,400,843,603 | fd80b90536363964701995c679a04df0 |
| neurite | 2 | ERR7337822 | 964,822,552 | 6b3edb97bb7890f058f057552cf3801d |
| neurite | 3 | ERR7337823 | 1,274,894,586 | 0f33bdb125acedfa826b846cd9b97f6b |
| soma | 1 | ERR7337824 | 1,417,520,067 | edb6203f498f761cee58ba3ef4b6be0d |
| soma | 2 | ERR7337825 | 1,121,848,198 | a9123739f929ecacad57571d2e6aeb8e |
| soma | 3 | ERR7337826 | 1,272,136,960 | 55b24196cc0418c1e804f889f7d1b695 |

Total: 7,452,065,966 compressed bytes and 164,832,486 reads.

The authors’ public MPRNA repository was retrieved outcome-independently and pinned at commit:

`0e7118f1d4880884e6e99e4ba48a26d67f00338a`

The paper and code specify:

* UMI introduction during second-strand synthesis;
* adapter-aware sequence extraction;
* exact library-sequence matching without indels;
* total-mapped-read normalization;
* pseudocount `0.5` for replicate ratios;
* three biological replicates;
* DESeq2 with condition and replicate terms;
* at least 20 reads on average for downstream mutagenized-library analysis.

The six large FASTQs were not downloaded because the integrity stop was triggered before outcome reconstruction.

## Additional design ambiguity identified

The 6,266-row design contains 6,260 unique nucleotide sequences. Six sequence groups are duplicated across construct annotations. One retained Ndufa2 exact SNV is sequence-identical to a kmer2 construct. This is not yet classified as a historical error: sequence-identical constructs are experimentally indistinguishable in sequence-counting data and may legitimately share a measurement. It must be handled explicitly in any authorized reconstruction protocol.

## What has not been done

Following the immediate-stop rule, this diagnostic did not:

* alter any historical N-zip file;
* relabel the 406 affected mutant outcomes;
* recompute Phase 3 metrics;
* redefine the Phase 3 NO-GO;
* calculate replicate oracle stability;
* define epsilon-optimal sets;
* perform direction-asymmetry analysis;
* inspect any Astrocyte outcome;
* list, extract, or open the Moffatt result archive;
* inspect Moffatt outcome values;
* train a model.

## Required resolution before Phase 3.5 may resume

A new committed correction protocol must explicitly define:

1. how filtered/unresolved constructs are represented;
2. whether raw replicate counts recover usable measurements for any of the 406 affected SNVs;
3. the read-count and construct-inclusion rule, fixed from the authors’ methods/code;
4. how sequence-identical design rows are collapsed or linked;
5. how the corrected truth-safe cohort is versioned without overwriting historical artifacts;
6. which historical conclusions are invariant and which require a labeled reanalysis;
7. whether oracle identifiability is evaluated only among constructs passing the prospectively fixed measurement-quality rule.

Phase 3 remains frozen as a historical analysis. Its NO-GO is not rewritten. Any future corrected analysis must be clearly labeled as a new benchmark version.

## Primary public sources

* Paper: https://doi.org/10.1038/s41593-022-01243-x
* PMC full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC9991926/
* BioStudies/ArrayExpress accession: https://www.ebi.ac.uk/biostudies/arrayexpress/studies/E-MTAB-10902
* ENA study: https://www.ebi.ac.uk/ena/browser/view/ERP133202
* Authors’ MPRNA code: https://github.com/IgorUlitsky/MPRNA
