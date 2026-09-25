# Independent small-edit confirmation: metadata-first admission contract

Status: **source admission requirements only; no source admitted, no new outcomes opened, no target evaluation frozen.** Written after the completed development analyses. This is not a new confirmatory result or permission to reopen protected data. The intended scientific question remains prediction of experimentally measured localization change from a small edit.

## Stage 1: source identity, access and independence

Before downloading or inspecting outcomes, record the official publication/accession, public source URL, access and reuse terms, expected files/size, and evidence identifying the original experiment. Access must be free; no purchase, credentials obtained from another party, cloud expenditure or paid service is permitted. Pin file identities/checksums when available. Unknown access or provenance stays unresolved.

Use design descriptions, file manifests and permitted metadata to determine whether this is a genuinely separate experiment. Document any overlap in samples, raw libraries, reporter constructs, parents/genes, assays or published derived tables with SRLE, Mikl, Moffatt, TDP43 and SIRLOIN and the complete prior source/exposure inventory. A renamed accession, processed re-export, new split or new replicate of an already-used experiment is not independent confirmation. Uncertainty about overlap prevents admission; a self-declared 'independent' label is insufficient.

Never inspect sealed Astrocyte, N-zip, quarantined TDP EV5 stability, reserved SIRLOIN outcomes, or unadmitted outcomes to fill this form. The earlier new-dataset discovery rejection remains in effect; this contract is not a workaround for that block. No new source is currently available to run through it.

## Stage 2: biological and measurement compatibility

Require documented parent/reference and mutant sequences, experimental pairing identifiers, exact edit coordinates/construction, biological context, and localization endpoint. Parent and mutant must be measured in the same relevant reporter/assay context. A paired/reference-normalized effect with authoritative semantics can substitute for separate absolute values; do not impute an unmeasured parent as zero.

Establish from design metadata that the variants are experimentally related. Do not manufacture parents by nearest-sequence matching of unrelated inserts. Exclude changes in promoter, reporter, barcode or intron configuration from the pure small-RNA-substitution claim unless the actual transcribed change and all accompanying changes are explicitly identified and handled by a separately justified scope.

Record whether the endpoint is a ratio, log ratio, enrichment coefficient, probability or another quantity, its sign orientation and scale, and how reference subtraction is defined. RNA abundance/stability alone is not localization. A source predictor on log-score units is not quantitatively calibrated to a ratio-difference target. Compatibility for magnitude, direction and ranking must each be decided **before outcome values are opened**. A failure of magnitude compatibility does not license a later switch of primary task after seeing scores.

Require at least two documented biological replicate measurements or an authoritative replicated paired-effect estimator with its uncertainty definition. Technical barcodes are not biological replicates. Specify replicate identity, reference matching and permitted missing-value handling in advance. Do not admit only significant or favorable effects.

## Stage 3: size, grouping and useful decision sets

For substitution-only studies, report 1, 2, 3, 4–6 and >6 corresponding-coordinate changed bases separately. Record edit span and minimum alignment distance separately; do not relabel a larger physical replacement as small because an alternative alignment is shorter. Unresolved indel/construction semantics require a separate prior protocol.

Count variants, exact parents, independent parent genes/biological units, contexts and candidates per parent from permitted design metadata. Thousands of mutants from two parents remain two biological parent validations. Related parents, identical alleles and all variants of one gene must remain grouped; context/source claims require their own held-out level.

For a breadth-oriented candidate-selection claim, retain the existing requirement of **at least 20 independent eligible gene/biological groups within the prespecified size/context stratum**, with at least two measured candidate edits per parent decision set. This is a minimum breadth rule inherited from the small-edit protocol, not a power calculation. Smaller resources may support a declared bounded descriptive analysis, but may not pass as broad confirmation. Do not decide to relax this rule after observing target performance.

Record expected precision using design-based group counts and development-only assumptions before outcome access. If power/precision is inadequate, say so before scoring. Do not estimate a favorable sample size from preliminary target performance or count overlapping candidate pairs as independent units.

## Stage 4: outcome-blind evaluation lock

Passing metadata review only makes a source **eligible for a separate evaluation design**. Before reading its outcomes, commit a source-specific protocol naming:

- Exact source files/hashes, eligible size/context strata, independent unit and exposure history.
- One primary predictor/selection procedure with code and weight hashes, all transformations and endpoint compatibility; no target fitting or target calibration for a zero-shot claim.
- Applicable strong controls: no-change, training-only mean/prevalence where transferable, edit size/position, composition, ΔAU, 1/2/3-mer, local sequence, and documented motif controls. Mark unavailable controls and why before scoring; absence limits the claim rather than implying victory.
- A/B/C task priority, calibration semantics, fixed tie/zero/missing-value rules, outcome-independent candidate roster, desired directions, and any abstention/unchanged-parent policy.
- Parent/gene-cluster uncertainty and paired contrasts; no variant-wise biological inference. Keep all planned metrics, denominators and failures.
- The existing candidate-choice superiority requirement: >=20 independent groups, mean normalized regret improvement >=0.02 and paired 95% lower bound >0 against every applicable required comparator, >50% groups improved, and no increase in wrong-direction choice. These conditions alone do not establish novelty or a molecular mechanism.
- A prespecified method for multiplicity if several size/context strata are confirmatory; unplanned subgroup winners remain exploratory. The final design must also specify precision and effect/sign criteria appropriate to the admitted endpoint.
- One execution and a stopping rule. Any model/threshold revision after target exposure starts a development analysis and requires a new independent confirmation source.

No target-specific model choice is frozen here: its validity depends on source identity, endpoint scale and input compatibility, which are not known. Naming an unusable predictor now would create the appearance of preregistration without a defensible test.

## Current disposition

All sources in the existing [small-edit inventory](small_edit_dataset_inventory.md) are previously exposed, structurally insufficient for the stronger claim, or protected/unadmitted. None becomes independent by applying this document. The project has an explicit admission process ready for a legitimately available new source; it does not yet have that source.

The machine-readable [intake template](../../results/small_edit_20260925/independent_source_intake_template.json) deliberately uses null for unknown facts. It is a review record, not an executable approval. Outcome access and scoring remain disabled until a separate source-specific admission and committed protocol are recorded.
