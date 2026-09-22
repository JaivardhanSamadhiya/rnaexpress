# Context calibration: pre-outcome specification, 22 September 2026

AI-authored technical execution specification. This is a distinct exploratory
new-data experiment, not a reopening of Mechanism v2-v5. Original project failures
stand. The public study's qualitative conclusions are already known.

Question: can sequence models learned in three RNA contexts, with at most 64
target-context labels, improve selection of localization fragments in a fourth
context for unseen sequence-connected gene groups?

Data: Ron and Ulitsky 2022 Supplementary Data 3, numeric columns I:L (published
Nuc/Cyto readouts, treated as supplied). Four contexts are spliced/unspliced HBB,
circPVT1 and SCRcircPVT1 in MCF7. No expression, stability or knockdown outcomes.
Public official supplementary files were freely downloaded and SHA-256 verified.
This is a retrospective label-budget simulation: each task's fitting uses <=64
target labels, although other contexts serve as sources in other fixed tasks.
It does not claim that the whole workbook contains only 64 known target labels.

Exclude invalid/missing metadata, exact prior-study overlaps and all JPX, NICN1,
PVT1 gene families. Map circular transcript aliases using publisher metadata;
group explicit transcript variants and MALAT1 ortholog aliases. Merge whole
families sharing any exact 40-nt tract or >=95% normalized global Levenshtein
sequence similarity. Exhaustively check all sequence pairs. These links are
conservative sequence groups, not a complete external paralog ontology.

Sort components by SHA256 of `context-budget-20260922|` plus component ID.
Reserve first floor(N/5) components for confirmation, next floor(N/5) for
development. Of the rest, first eight with >=20 metadata rows supply calibration;
each supplies exactly eight hash-ordered rows. Remaining components supply source
training. Other calibration-family rows remain unused. Missing target values get
no replacement: require >=32 labels across >=6 calibration components per target.
This minimum was set before outcomes because the paper reports incomplete tile
quantification; 64 is the attempted-label budget, not a promise of 64 finite values.
If eligibility fails, preserve the failure; no outcome-guided repartitioning.

Use frequency-normalized 1-3-mer features (84); source models are standardized
Ridge alpha=100 trained on source components for each of the other three contexts.
Primary target model is standardized Ridge alpha=10 on these three predictions,
fitted only to the fixed calibration labels. Strong baselines use the identical
labels: standardized Ridge alpha=10 on 84 kmer features or four base frequencies.
A three-dimensional Gaussian projection of the source-standardized kmer features
(seed 20260922, divided by sqrt(84)) with the same target fit controls compression.
No hyperparameter, split, sign or model search. All models predict the same rows.

Within original gene label and library, require >=10 finite candidates and a
nonzero outcome range. Select maximum and minimum predicted localization with
lexical ID ties. Average their normalized regrets, then average decisions within
connected component/context, components within context, then contexts equally.
Bootstrap whole connected components 5,000 times, seed 20260922, preserving paired
contexts and models. Report exclusions, calibration counts, context-specific
effects and paired 95% intervals. Predictions are recorded without target labels.

Discovery promotion requires >=15 evaluable development components overall,
>=10 per context, mean regret gain >=0.03 over EACH target-only kmer and composition
baseline, paired 95% lower bounds >0, positive gains in >=3/4 contexts and no
context gain < -0.05. The random three-feature baseline also must be beaten with
mean gain >=0 and lower bound >0, with the same context requirements. All required
comparisons must pass. Only then run the identical fixed models on confirmation
components, requiring the same criteria. Failure leaves confirmation unopened.
No revised threshold or favorable subgroup can be promoted under this experiment.

Freeze source, tests, metadata, partition and specification and commit before
opening outcomes. An explicit row whitelist controls numeric parsing of I:L;
no reserved row's numeric values are interpreted. The entire public XLSX is
already downloaded, which is distinct from reading its reserved measurements.

Positive results would concern budget-limited selection of measured fragments
within this reporter study. They would not establish minimal-edit interventions,
causality, generalization to a new laboratory/cell type, or complete novelty.
Transfer learning itself has prior art, including DeepLocRNA (2024), DOI
10.1093/bioinformatics/btae065. Context dependence was shown by this source study,
DOI 10.1038/s41467-022-30183-0. Subsequent methods must retain these limitations.
