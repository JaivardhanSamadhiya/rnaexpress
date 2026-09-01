# RNAddress v4 Phase B novelty refresh

## Search scope

This collision search was refreshed on 2026-08-31 after the Phase B protocol freeze. Queries covered `RNA decision-focused learning`, `sequence design DFL`, `RNA edit regret optimization`, `MPRA predict-then-optimize`, `molecular intervention regret`, `RNA localization inverse design`, antisense candidate ranking, biological-sequence bandits, and model-guided MPRA design. Primary papers, publisher records, PubMed, PMLR, and OpenReview records were prioritized. Search-engine absence is not proof of global novelty, so the conclusion is deliberately narrow.

## Direct and adjacent collisions

No located work matched the full RNAddress task: choose among measured parent-specific RNA-localization interventions, train across heterogeneous localization perturbation assays, optimize held-set regret/shortlist utility, and test source/edit-budget transfer with a sealed prospective assay reserved.

Important adjacent work prevents any broad “first molecular design” or “first RNA design” claim:

- Mandi et al. (PMLR 2022), *Decision-Focused Learning: Through the Lens of Learning to Rank*, establishes pointwise, pairwise, and listwise views of decision-focused solution ranking. RNAddress's pick-one softmax loss is an application of this established idea, not a new DFL principle: https://proceedings.mlr.press/v162/mandi22a.html.
- Elmachtoub and Grigas, *Smart Predict, then Optimize*, establishes optimization-aware regret and SPO+. RNAddress does not invent predict-then-optimize: https://doi.org/10.1287/mnsc.2020.3922.
- Yamao et al. (UAI/PMLR 2026), *Robust Decision-Focused Learning via Worst-Case Regret Minimization*, directly addresses observation error and distribution shift. RNAddress cannot claim robust DFL novelty and correctly excludes that model here because its source uncertainties are not semantically commensurate: https://proceedings.mlr.press/v337/yamao26a.html.
- Yuan et al. (NeurIPS 2022), *Bandit Theory and Thompson Sampling-Guided Directed Evolution for Sequence Optimization*, minimizes Bayesian regret for biological sequence optimization. It is protein/directed-evolution and sequential acquisition rather than RNA-localization candidate selection, but it is a clear collision with any generic “first regret-based biological sequence optimization” claim: https://openreview.net/forum?id=drVX99PekKf.
- Linder et al. (BMC Bioinformatics 2022), *Fast activation maximization for molecular sequence design*, optimizes DNA, protein, and RNA-compatible sequence objectives through learned predictors. It blocks a generic inverse molecular-sequence-design claim: https://doi.org/10.1186/s12859-021-04437-5.
- Liu et al. (Nucleic Acids Research 2024), *Optimizing sequence design strategies for perturbation MPRAs*, evaluates mutation/shuffle design strategies and predictive robustness for perturbation MPRA. It is not decision-focused RNA-localization selection, but it is close methodological prior art for intervention-library design: https://doi.org/10.1093/nar/gkae012.
- Melnikov et al. (Nature Biotechnology 2012) used MPRA-trained quantitative sequence-activity models to optimize inducible enhancer designs, blocking a generic “first MPRA model-guided intervention design” claim: https://doi.org/10.1038/nbt.2137.
- RNA-GPS, RNATracker, RNALoc-LM, MSLP, and related systems predict RNA localization or conduct attribution/ablation. The refreshed 2025 review catalogs a crowded prediction field. These are not experimentally grounded intervention-selection systems, but they block broad RNA-localization modeling novelty claims: RNA-GPS https://doi.org/10.1038/s41592-020-0747-0; RNATracker https://doi.org/10.1093/bioinformatics/btz337; RNALoc-LM https://doi.org/10.1093/bioinformatics/btaf147.
- RNA inverse-design methods, including reinforcement-learning inverse folding, Struct2SeQ, and gRNAde, design sequences for structural targets. They differ from localization intervention selection but block “first RNA inverse-design model” language: https://doi.org/10.1371/journal.pcbi.1006176, https://pubmed.ncbi.nlm.nih.gov/41648297/, and https://pubmed.ncbi.nlm.nih.gov/39312140/.
- A public ASOCompass model listing describes antisense-oligo ranking under gene/cell/delivery shifts and reports selection regret. A peer-reviewed primary paper was not located in this search, so this is treated as a product-level collision signal, not validated literature evidence. It nevertheless blocks casual claims that candidate-level RNA intervention regret is unique to RNAddress: https://bio.rodeo/models/asocompass.

## Defensible novelty position

The defensible claim, contingent on Phase B performance and later prospective validation, is an **integration and validation contribution**:

> A mechanism-aware, decision-focused framework for selecting experimentally measured RNA-localization interventions across heterogeneous perturbation assays, biological parents, directions, reporters, and edit budgets, with explicit zero-shot source transfer and a separately sealed prospective benchmark.

Do not claim that RNAddress invented decision-focused learning, regret optimization, biological sequence optimization, RNA inverse design, MPRA-guided design, localization prediction, shortlist ranking, or robust DFL. Do not use “first” without a formal systematic review and expert prior-art review immediately before publication.

## PV-Care implication

Novel positioning alone cannot establish PV-Care-level readiness. The path remains credible only if the definitive Phase B gates demonstrate real held-context and small-edit transfer and a later Phase C freeze produces a genuinely positive untouched Astrocyte result. If Phase B transfer fails, the integration remains technically interesting but does not support a high-impact prospective intervention claim.

## Post-result path refresh

A final primary-source search after gate evaluation did not identify evidence that could legitimately change the frozen Phase B verdict. It did reinforce the next-cycle experimental design:

- the paired neuronal localization MPRAs show that localization is often distributed across many small contributions and that short motif introduction need not reverse motif disruption, supporting direction-specific modeling and denser matched small-edit experiments: https://academic.oup.com/nar/article/50/18/10643/6717835;
- the complementary reporter study measures the same long oligonucleotides in GFP and firefly contexts and in CAD and N2A cells, illustrating the value of crossed reporter/cell designs for separating sequence effects from assay context: https://academic.oup.com/nar/article/50/18/10626/6701598;
- a 2025 benchmark of foundation models on 3′UTR tasks reports that frozen language-model embeddings do not uniformly dominate task-specific alternatives, reinforcing the need to require contextual embeddings to beat metadata rather than assume scale equals mechanism: https://academic.oup.com/nar/article/53/17/gkaf871/8252024;
- 2025 work on cryptic splicing in 3′UTR MPRAs shows that assay artifacts can be sequence-dependent, supporting explicit splice/artifact controls in any new intervention library: https://www.nature.com/articles/s41467-025-62000-9.

These findings support a new matched-data acquisition cycle; they do not authorize candidate-family expansion after definitive Phase B results.
