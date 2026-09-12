# Dataset and estimand landscape for RNAddress

Written 12 September 2026 after the Mechanism-v3 NO-GO, in response to the
question: *is there any dataset or method that could make this project idea
work?* This is a feasibility survey, not a result. It changes no verdict.

## The key correction to my earlier claim

I previously said the project idea cannot work. That was too broad. What the
Mechanism-v2/v3 evidence actually establishes is narrower:

> **The within-parent intervention-ranking estimand cannot be supported on the
> current benchmark.** Within-decision outcome reliability is 0.239 and the leaky
> all-feature ceiling is +0.0218 rank gain against a 0.020 gate.

A different estimand, or a different dataset, is a separate question. Two real
paths exist. Neither is a way to make the existing NO-GO pass.

## Finding 1: the published task on this very data already works

The source paper for Mikl GSE173098 — the dataset already inside this benchmark —
reports **auROC 0.81–0.83** for predicting the localization behaviour of *unseen
reporter sequences*, using XGBoost on either 218 RNAcompete RBP scores (0.81) or
plain **4-mer counts (0.83)**
([von Kügelgen / Mikl et al., NAR 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC9561380/)).

Two things follow.

1. **Sequence-level localization prediction is a solved-ish, reproducible task**
   on this data. RNAddress's difficulty is not "can sequence predict
   localization"; it is the much harder "which edit to a given parent is best".
2. **4-mers beat RBP motif features in the published model too.** That
   independently reproduces this project's own N4 finding, where a frozen random
   k-mer projection (+0.0286 rank gain) matched or beat the full
   RBPNet + BERT + structure stack (+0.0250). The exploitable signal is k-mer
   composition at the sequence level, not mechanism at the mutation level.

## Finding 2: candidate datasets, and what each would and would not fix

| dataset | scale | readout | mutation-level pairs? | usable here? |
| --- | --- | --- | --- | --- |
| **SEERS** ([bioRxiv 2025/26](https://doi.org/10.1101/2025.06.09.658412), [code](https://github.com/gao-lab/SEERS)) | ~2,000,000 synthetic 45-nt 3′UTRs, A549 + HCT116 | nuclear/cytoplasmic partitioning + abundance | random N45, so dense mutational neighbourhoods; includes in-silico saturation mutagenesis and ClinVar scoring via their TALE model | **yes, not sealed** — but nuc/cyt export in cancer lines, *not* neurite/soma in neurons |
| **N-zip saturation mutagenesis** ([Nat Neurosci 2023](https://doi.org/10.1038/s41593-022-01243-x)) | 6,266 sequences: every possible single point mutation plus G↔C / A↔U windows at 2, 5, 10 nt across 16 neurite-localised fragments | neurite/soma in primary cortical neurons | **yes — this is the ideal design for the original estimand** | **forbidden.** N-zip outcomes are sealed by this project's own rules |
| **SN-MPRA astrocyte** ([PMC13142395](https://pmc.ncbi.nlm.nih.gov/articles/PMC13142395/)) | in vivo astrocyte 3′UTRs + SNVs | localization + local translation | yes | **forbidden.** Astrocyte is the sealed one-time holdout |
| **NucLibA / NucLibB (SIRLOIN)** ([Nat Genet 2018](https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC6047738&blobtype=pdf)) | 5,511 tiles + variant series within 30-nt JPX/PVT1 fragments | nuclear enrichment, human cells | yes, but few parents | small; nuclear retention, not neurites |
| **APEX-seq / RNA-GPS** ([RNA 2020](https://doi.org/10.1261/rna.074161.119)) | 20,852 transcripts, 8 compartments | native transcript localization | **no** | gene-level estimand only |
| **Halo-seq** ([PMC8887463](https://europepmc.org/article/pmc/pmc8887463)) | nuclear / nucleolar / cytoplasmic | native transcripts | **no** | gene-level estimand only |
| **RNALocate v2 / LncATLAS** ([NAR 2021](https://doi.org/10.1093/nar/gkab825)) | 473,961 mRNA entries; 231,466 human sequences | curated compartment labels | **no** | gene-level estimand only |

## Finding 3: the honest structure of the problem

* The dataset **perfectly matched** to the original RNAddress estimand is the
  N-zip saturation-mutagenesis library. It is the one dataset this project
  explicitly forbids. That is a governance decision, not a scientific limit, and
  it is the user's call — not something to work around unilaterally.
* The **largest available** localization dataset with dense mutational structure
  is SEERS (~2M sequences). It plausibly dissolves the power problem that killed
  Mechanism-v2/v3. But its readout is nuclear/cytoplasmic export in A549 and
  HCT116 cells. Adopting it changes the project from *neuronal RNA addressing* to
  *nuclear export element design*. That is a scope change, not a method swap.
* Gene-level resources (RNALocate, APEX-seq, Halo-seq, LncATLAS) are large and
  open but cannot support an intervention-ranking estimand at all, because they
  contain no reference/mutant pairs.

## What I am and am not claiming

* I am **not** claiming RNAddress is impossible in principle.
* I **am** claiming it is not achievable on the current benchmark, for measured
  reasons, and that no bug fix, feature set, or model class changes that.
* Any future GO must come from a **new prospectively frozen experiment on
  adequate data**, not from revisiting Mechanism-v2 or v3.
* FinalShot `98ffc02` and the Mechanism-v2 and Mechanism-v3 NO-GO verdicts stand
  unchanged. Astrocyte remains sealed and unopened.
