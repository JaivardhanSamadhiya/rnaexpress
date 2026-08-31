# RNAddress v4 TDP-43 common-schema audit

## Verdict and role

The TDP-43 source remains a valid exact-sequence intervention landscape and is translated into the v4 common schema as **post-lock development data**, not independent validation. It contributes **4,566 interventions, 16 genes, and 4,566 independent parent contexts**.

## Source identity and mapping

- Public study/data identity: `GSE288185` and `S-SCDT-10_1038-S44318-025-00653-4`.
- Frozen exact intervention file: `data/processed/tdp43_motif_intervention_pairs.csv.gz`; SHA-256 `39590d9609a4376d39b1e48886576fdad2ef10764bbebb0130ecd86e27ba8e6f`.
- Prior first-principles source audit: `reports/v3_tdp_source_data_audit.json`; SHA-256 `212fd3d43a7960b97ff1f40fd5a60612d1475ffa065abc74ed6c592476d470f4`.
- Parent and mutant identifiers map exactly to exact 260-nt EV8 sequences. Every declared edited-base count was recomputed from the exact sequences and matches.
- No row-order or approximate sequence pairing is used. The prior audit's `historical_pairing_error_found` guard remains false.

All immutable hashes, package versions, script hash, and processing commit are recorded in `results/v4_phaseA/source_manifest.json`.

## Common-schema translation

| Common field | TDP-43 meaning |
| --- | --- |
| `parent_id` / `mutant_id` | exact source construct identifiers |
| `parent_sequence` / `mutant_sequence` | exact verified 260-nt sequences |
| `intervention_class` | `tdp43_motif_complement_replacement` |
| `motif_family` | TDP-43 UG-rich motif |
| `edit_distance`, `edit_cost` | exact changed-base count |
| `group_id` | exact biological parent construct |
| `localization_effect` | mutant minus WT author-processed log2(neurite/soma) |
| `replicate_count` | four biological replicates represented by source EV3 |
| `effect_uncertainty` | explicitly missing at the processed pair level |

## Scale and direction

| Quantity | Result |
| --- | ---: |
| Certified interventions | 4,566 |
| Genes | 16 |
| Parent contexts | 4,566 |
| Changed bases: minimum / median / maximum | 5 / 7 / 179 |
| Increase | 1,899 |
| Decrease | 2,667 |

The library is direction-asymmetric and has no exact one-base interventions. It is valuable for motif disruption and larger complement-replacement operations, not exact-SNV supervision.

## Replicates and unresolved uncertainty

The experimental design contains four biological replicates in EV3. The processed Figure 4E pair table does not expose pair-level replicate uncertainty, so `effect_uncertainty` remains missing for all 4,566 rows. The missing state is not encoded as zero and is not reconstructed from a different outcome table.

The EV5 raw stability/SLAM-seq table remains quarantined because it has **10,935 duplicate `(sample, oligo)` keys**. The audit does not collapse or select among them. Exact paired auxiliary support remains 3,600 RBNS pairs and 3,600 processed stability pairs, but those auxiliary outcomes are not relabeled as localization uncertainty.

## Leakage-safe use

Every TDP parent is a distinct context. All reporter outcomes and auxiliary properties for a parent-mutant pair must remain in one group. Gene-held-out evaluation is required as a strict sensitivity analysis because 4,566 sequence parents come from only 16 genes.

TDP supports a shared intervention representation and an assay-specific TDP head. Its direction skew, missing pair uncertainty, and distinct motif-generation mechanism rule out naive numerical pooling with Mikl or Moffatt.

## Machine artifacts

- `results/v4_phaseA/tdp_interventions.csv.gz`
- `results/v4_phaseA/common_intervention_outcomes.csv.gz`
- `results/v4_phaseA/edit_distribution.csv`
- `results/v4_phaseA/phaseA_summary.json`
- `results/v4_phaseA/source_manifest.json`
