# RNAddress hostile novelty audit

Search cutoff: 2026-08-26. Scope included scholarly search, PubMed/PMC, datasets, source repositories, patents and publicly indexed commercial descriptions. This is a technical novelty audit, not a legal freedom-to-operate opinion.

## Exact defensible novelty claim

The defensible target is: **a target-conditioned computational framework that accepts a starting RNA, a requested localization direction and protected molecular properties; ranks minimal cis-sequence edits; and is evaluated by revealing measured interventions on parent-held-out mutagenesis landscapes plus a lab-independent in-vivo assay.**

The novelty is the biological operation, constrained system formulation and intervention-ranking evidence. It is not the generic optimization algorithm, RNA-localization prediction, motif discovery, MPRA, or the idea that zipcodes control RNA localization.

The strongest wording remains conditional until experiments support it: “To our knowledge, RNAddress is the first evaluated computational framework for target-conditioned minimal cis-edit selection for RNA localization with parent-held-out and independent in-vivo intervention tests.” It must not be shortened to “the first method to engineer RNA localization.”

## Strongest prior collision

[CRISPR-TO](https://pmc.ncbi.nlm.nih.gov/articles/PMC12882822/) is the strongest capability collision. It programmatically redirects endogenous RNAs to multiple compartments in live cells and neurons and experimentally validates functional effects at impressive scale. It uses guide-directed dCas13 and localization/motor proteins, however, not minimal edits to the RNA’s endogenous cis-regulatory sequence.

The strongest cis-sequence-engineering collision is [RNA localization to nuclear speckles follows splicing logic](https://pmc.ncbi.nlm.nih.gov/articles/PMC12962856/). It designs motif/splice-site combinations and tests localization, including single-nucleotide disease variants. It does not provide a general requested-destination inverse editor, minimal-edit optimization on arbitrary parents, or held-out exhaustive intervention-ranking benchmark.

No searched system satisfied all four decisive clauses: starting RNA; requested destination/direction; computationally selected minimal cis edit; comparable experimental intervention validation. The Phase A stop rule is therefore not triggered.

## Closest five prior systems

| System | What directly collides | Decisive difference |
|---|---|---|
| CRISPR-TO (2025) | Programmable RNA relocation and strong live-cell validation | Trans-acting dCas13/motor machinery, not cis-sequence rewriting |
| Nuclear-speckle splicing-logic constructs (2026) | Rational sequence design and experimental localization | One compartment and hand-designed sequence grammar; no general inverse recommender |
| [N-zip](https://pmc.ncbi.nlm.nih.gov/articles/PMC9991926/) (2023) | Large causal cis-mutagenesis landscape in primary neurons | Assay/motif dissection, not target-conditioned computational edit selection |
| [Astrocyte SN-MPRA](https://pubmed.ncbi.nlm.nih.gov/42094343/) (2026) | In-vivo localization, translation and near-saturation SNVs | Experimental map for two genes, not an inverse design system |
| [SRLE-seq](https://pmc.ncbi.nlm.nih.gov/articles/PMC13191086/) (2026) / [mutREL-seq](https://pmc.ncbi.nlm.nih.gov/articles/PMC12018070/) | Gain-of-function localization motifs and mutational causal mapping | Fixed/small reporter contexts; no minimal-edit recommendation on unseen parents |

Forward predictors—including RNA-GPS, [DM3Loc](https://academic.oup.com/nar/article/49/8/e46/6121470), [DeepLocRNA](https://pmc.ncbi.nlm.nih.gov/articles/PMC10879750/) and [RNALoc-LM](https://pmc.ncbi.nlm.nih.gov/articles/PMC11978386/)—map sequence to localization labels. RNAddress’s intended operation is inverse intervention selection and must be compared against forward-model-plus-search as a baseline, not presented as merely a better predictor. [RNALocate](https://academic.oup.com/nar/article/50/D1/D333/6374157) is a database/tool hub rather than an intervention recommender.

## Patent/commercial threats

- [US5641675](https://patents.google.com/patent/US5641675A/en) broadly establishes cis-acting RNA “zipcode” sequences and artificial localization constructs. It destroys any broad claim to inventing localization by sequence.
- [WO2025096250A1](https://patents.google.com/patent/WO2025096250A1/en) covers programmable spatial RNA manipulation corresponding to the CRISPR-TO capability, but primarily through RNA-carrier and localization polypeptides.
- [WO2023215761A1](https://patents.google.com/patent/WO2023215761A1/en) describes localization domains in trans-splicing nucleic acids.
- [US20250101393A1](https://patents.google.com/patent/US20250101393A1/en) discusses manipulating RNA zipcodes/trafficking in RNA-targeting methods.

These are serious broad-claim and future-translation threats. None found claims the exact computational evaluation architecture, but a patent professional would need a claim-by-claim search before commercialization. No publicly indexed commercial product was found that accepts an arbitrary RNA and destination and returns experimentally validated minimal cis edits; absence from search is not proof of absence.

## Variable-renaming result

Renamed generically, RNAddress is constrained counterfactual recourse: find the smallest discrete input change that moves a predictor toward a target while bounding collateral objectives. Exhaustive one-step search, beam search, Pareto ranking, retrieval and constrained optimization are established ideas. Calling these algorithms novel would fail review. The contribution must arise from RNA-localization-specific constraints, leakage-resistant intervention evaluation and demonstrated transfer.

## What is new

- Target-conditioned *cis* intervention selection rather than forward classification or trans-acting transport.
- Joint minimization of edits and protection of measured/estimated stability, expression, translation and structure.
- Parent-held-out ranking against measured counterfactuals, not mutation-level random splits.
- A frozen lab-independent, in-vivo assay used only after model and predictions are committed.
- An end-to-end system that exposes uncertainty and infeasibility rather than always returning a mutation.

## What is not new

RNA zipcodes; motif discovery; MPRA; saturation mutagenesis; localization prediction; RNA inverse folding; generic sequence optimization; counterfactual explanations; exhaustive SNV enumeration; Pareto optimization; or CRISPR-mediated RNA transport.

## Forbidden claims

- “First to engineer/program RNA localization.”
- “Prospectively experimentally validated” when only public retrospective measurements are revealed.
- “General RNA localization solution” from neurite/soma and one fixed nuclear/cytoplasmic reporter.
- “Preserves expression/stability/translation” unless the exact protected endpoint is measured and passes a prespecified bound.
- “Mechanistic discovery” from predictive attribution alone.
- “Independent external validation” without disclosing the three-row pre-freeze exposure.

## Novelty score /10

**8.0/10.** The exact system-and-evidence claim survived the direct search, but broad biological claims are crowded and generic optimization contributes little novelty by itself.

## PV-Care-style capability novelty score /10

**8.3/10 potential; not yet earned.** The requested-input-to-action workflow and independent intervention reveal can become a genuine capability. At Phase A–E it remains an evidence-backed opportunity, whereas [PV-Care](https://www.tian-2.com/yau/browse/computer-science) already integrated sensing, state recognition, proactive decision logic, hardware and user testing.
