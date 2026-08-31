# RNAddress v4 Phase A protocol

Protocol freeze date: 2026-08-31  
Frozen starting commit: `850d9a4df5d109d0aad587f9fdba86b465f99bbd`  
Branch: `rnaddress-v3-5-oracle-audit`

## Objective and hard boundaries

Phase A rebuilds a high-integrity development foundation for a minimum-edit-budget RNA-localization intervention compiler. It reconstructs source truth, uncertainty, intervention cost, independent grouping, and cross-assay compatibility. It does not train, tune, select, or evaluate an RNAddress v4 model.

N-zip remains a quantitative **NO-GO** and contributes no outcomes to Phase A decisions. The 3,453-row partial reconstruction is non-certified and cannot be used for selection, tuning, calibration, or gating. Historical models will not be rerun. Astrocyte outcome files remain sealed and Astrocyte remains the final prospective benchmark. TDP is post-lock development data, not validation data.

## Predeclared source-truth workflow

1. Reconstruct Mikl independently from GSE173098 counts, the complete supplementary design tables, the paper, and public design code. Identify exact parent/mutant sequences, intervention semantics, genes, parent contexts, reporters/cell types, biological replicates, missingness, duplicate keys, and outcome uncertainty. No row-order pairing is permitted.
2. Reaudit TDP against its public EV3/EV8/EV9 construct sources and the existing exact-ID reconstruction. Preserve the EV5 SLAM-seq duplicate-key quarantine. Translate certified records to the structural common schema without treating TDP as independent validation.
3. Freeze and commit the outcome-blind Moffatt design protocol before opening any Moffatt count file or enumerating the sealed archive. After that commit, verify the sealed archive SHA-256, log the transition to development data, extract it, and construct source truth before any model work.
4. Represent Mikl, TDP, and Moffatt structurally in one schema while retaining assay-specific outcomes and uncertainties. Never numerically pool assay outcomes in Phase A.
5. Derive intervention classes from observed edit-distance modes and experimental design. Preserve continuous changed-base, insertion, deletion, replacement, and changed-fraction costs.
6. Count effective scale at assay, gene, biological parent element, exact parent sequence, reporter context, and replicate levels. The primary leakage barrier is biological parent element; exact parent sequence and gene are stricter sensitivity groupings.
7. Audit increase and decrease directions independently, including counts, magnitude distributions, uncertainty, and context coverage.
8. Search primary literature and authoritative repositories for compatible intervention datasets, RNA sequence representations, and decision-focused/selective-prediction methods. Record why each candidate is included, secondary-only, or excluded.

## Required machine contract

Every certified record must expose dataset/accession/source identifiers, exact sequences, mapping method, exclusions, duplicate state, replicate structure, outcome semantics, missing-value state, processing-script hash, environment, and Git commit. Missing and non-finite values remain explicit; no sentinel is interpreted as a quantitative outcome. All Phase A machine outputs live under `results/v4_phaseA/`.

## Decision rule and stop

The final verdict is one of strong GO, asymmetric/limited GO, conditional GO, or NO-GO. A strong GO requires multiple independent biological parent contexts, reconstructable interventions and outcomes, defensible uncertainty, and a credible leakage-safe development split. Limited or conditional GO is used when only a narrower direction, edit regime, or assay-specific formulation is supportable. After the verdict and integrity checks, stop: do not train v4 and do not open Astrocyte outcomes.
