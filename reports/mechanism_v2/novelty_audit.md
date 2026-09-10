# Mechanism-v2 novelty audit

## Scope and defensible contribution

The literature supports a narrow potential contribution: **testing whether
mutation-induced sequence and biophysical changes can select localization edits
on unseen biological parents and assay contexts, with explicit failure gates and
mechanism-destroying controls**. It does not support claiming invention of RNA
localization prediction, RBP-aware representations, paired variant deltas,
structure-aware RNA models, inverse design, or latent phenotype/measurement
separation. A successful general selector has not yet been demonstrated here.

This is a bounded primary-source refresh through 10 September 2026, extending
the preserved FinalShot audit. Publication dates were checked against publisher
records where available. Exact phrase searches were complemented by broader
localization, variant, RBP and RNA-design searches. Sparse exact matches do not
prove priority. No protected outcome dataset was sought, opened or admitted.

## Closest precedents and boundaries

**RNA-GPS** already uses nucleotide features for localization prediction and
sequence-ablation analyses, with particular attention to splicing-related motifs.
Thus interpreting sequence perturbations or linking processing features to
localization is not new by itself. Its published classification/ablation setting
is distinct from the multi-source within-parent edit-selection estimand with
biological-group transfer and regret gates used here. [Wu et al., RNA 2020](https://doi.org/10.1261/rna.074161.119).

**DeepLocRNA** uses a pretrained multi-task RBP-binding model as a basis for
localization prediction through transfer learning. This is particularly close
prior art for the original RNAddress representation premise. Reusing a frozen
RBP encoder for downstream localization cannot be presented as an original
concept; the question here is paired intervention ranking and its generalization
under strict controls. [Wang et al., Bioinformatics 2024](https://doi.org/10.1093/bioinformatics/btae065).

**BRIDGE** explicitly defines variant impact as the alternative-minus-reference
predicted RBP score in a specified context. It integrates sequence and structure,
studies context transfer and performs mutagenesis/attribution analyses. It therefore
precludes a first-of-its-kind claim for context-aware RBP variant scoring or
sequence–structure binding interpretation. Its computational binding predictions
and assumptions about required experimental modalities must not be confused with
validated choice of neurite-localization edits. [Wang et al., Nature Communications 2026](https://www.nature.com/articles/s41467-026-73086-0).

**MAVE-NN** formalizes genotype-to-latent-phenotype mappings and separate noisy
measurement processes, including biophysically interpretable models. The general
hierarchical biological-score/assay-head premise is established. Mechanism-v2's
current paired ranker is substantially more restricted: it uses source ranking
temperatures, not a full generative assay calibration model. [Tareen et al., Genome Biology 2022](https://doi.org/10.1186/s13059-022-02661-7).

**BioGraphX-RNA**, published 4 September 2026 as an early accepted article,
combines structure-informed physicochemical graphs with frozen RiNALMo embeddings
for RNA localization. Its abstract reports limited blind human-to-mouse zero-shot
transfer. This is important overlap in both multimodal modeling and transfer
limitations. The results concern localization classes, not the paired edit-ranking
benchmark here; they neither prove nor disprove RNAddress. Detailed comparisons
beyond the accessible publisher abstract are not asserted. [Saeed and Abbas, BMC Bioinformatics 2026](https://link.springer.com/article/10.1186/s12859-026-06619-5).

**SRLE-seq** screens sequence elements associated with localization, derives a
nuclear-retention score, contrasts biological and randomized score features, and
connects motif effects with RBP regulation. Even a biologically informed feature
versus randomized-feature localization comparison is therefore not unprecedented.
The accessible PubMed index and figure descriptions support this methodological
overlap, not a claim that its benchmark duplicates RNAddress's held-parent
selection experiment. No SRLE-seq outcome tables were downloaded or used.
[High-throughput Screening of Sequence Elements Associated with RNA Localization, PubMed 2026](https://pubmed.ncbi.nlm.nih.gov/42179915/).

**NucleicBERT**, published 3 September 2026, learns RNA representations from
single sequences and evaluates structure/function prediction and interpretability.
Its comparisons include pretrained and randomly initialized representations with
frozen-backbone probing versus fine-tuning. Neither structural signals in a
language model nor random-representation controls are novel here. This discovery
qualifies the contribution; it does not trigger another encoder search after the
localization recipe freeze. [Upadhyay et al., Nature Machine Intelligence 2026](https://www.nature.com/articles/s42256-026-01295-9).

**AlignIF**, published 30 July 2026, uses structure alignment and cross-graph
modeling for functional RNA design, including experimentally tested aptamers and
ribozymes. RNA engineering from computational representations is established.
These structural/function targets differ from neurite/soma intervention selection;
the term “compiler” alone does not establish a new scientific capability.
[Wang et al., Nature Computational Science 2026](https://www.nature.com/articles/s43588-026-01029-2).

## What “zero-shot” means here

RNAddress trains a downstream ranking model on permitted localization development
data. “Zero-shot” means no outcome-based adaptation to the target biological
parent/context—not that the entire model was never trained on localization.
This is different from intrinsic language-model benchmarking without downstream
fitting. The 2026 RNA-language-model benchmark explicitly discusses such a
strict no-fine-tuning setting and heterogeneous task-dependent representations.
This distinction must appear in any submission. Its PMC search-index text was
available, but direct page access returned a browser challenge; no unsupported
architecture or quantitative comparison is inferred. [Wang et al., Briefings in Bioinformatics 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC12963973/).

## Research gap and claim limits

The unresolved practical question is whether a model can choose a useful edit
rather than merely classify a transcript or correlate with an assay value, and
whether that choice transfers when the parent, source, cell or reporter changes.
Mechanism-v2 operationalizes that question with shared signed scores, no absolute
parent input in the primary model, independent component grouping, small-edit
strata, paired regret, source/cell/reporter transfer, and explicit harm limits.
This combination may be distinctive; an exhaustive priority claim is not justified.

The independent stability reconstruction and precommitted negative validation,
the correction of donor cycling into genuine bijections, and the distinction
between predictive utility and mechanistic necessity are reproducible research
assets regardless of the final result. They are not discoveries that RNA stability,
structure or RBP availability govern localization. A failed component must remain
failed, and a surviving prediction after identity destruction cannot be advertised
as identifying that protein's mechanism.

Unsupported claims include a new foundation model, universal localization grammar,
validated therapeutic editing, causal RBP mediation, demonstrated clinical safety,
and PV-CARE-equivalent success without passing the complete protocol. The frozen
FinalShot negative conclusion remains unchanged. Inner-development results are not
independent confirmation, and the sealed Astrocyte experiment remains unavailable
until the complete system and evaluation authorization are frozen.

## Search coverage

The refresh included all nine inherited topics: RBP-informed RNA intervention
design; RBP-aware RNA localization editing; CLIP foundation model RNA inverse
design; variant-aware RNA localization prediction; RNA localization sequence
intervention compiler; RBP binding delta localization; RNA intervention genotype–
phenotype model; MPRA latent phenotype localization; and cell-context RNA
localization edit prediction. Targeted follow-ups covered the primary works
linked above and official HGNC/HCOP methodology. Irrelevant protein-localization,
video-localization and generic drug-design results were not treated as RNA
intervention evidence. Search discovery snippets were distinguished from directly
inspected primary text where access was limited.
