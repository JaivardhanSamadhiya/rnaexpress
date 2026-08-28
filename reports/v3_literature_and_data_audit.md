# RNAddress v3 Phase 1 literature and public-data audit

Audit date: 2026-08-27 (America/Los_Angeles)  
Search cutoff: 2026-08-27  
Branch: `rnaddress-v3-mechanistic-selective`

## Executive decision

The search found one important new intervention landscape that was absent from the v1/v2 audit:

> Moffatt et al., **“Robust mammalian RNA localization elements are complex and multipartite”** (bioRxiv, 2026), DOI [`10.64898/2026.06.09.731215`](https://doi.org/10.64898/2026.06.09.731215), GEO [`GSE334718`](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE334718), BioProject `PRJNA1476227`.

The abstract reports tens of thousands of designed mutant localization elements measured in neuronal cells. GEO independently confirms a public neurite/soma MPRA with 80 samples spanning five intervention-library families, two reporter backbones, two compartments and four replicates.

This is a genuinely new and potentially high-value intervention dataset. It is **not yet established as a valid exact parent-mutant benchmark**, and it is **not unambiguously better than the in-vivo Astrocyte SN-MPRA**. Its intervention scale and experimental diversity may exceed Astrocyte, but its exact natural-parent count and sequence dictionary have not yet been recovered outcome-blind; it uses a CAD neuronal cell line; and it comes from the same experimental lineage as existing Arora/TDP development sources. Astrocyte remains stronger on in-vivo context, exact exhaustive SNVs, eight already reconstructed parents, multiple protected-property outcomes and laboratory independence from the principal development assays.

Therefore:

- the prompt's “clearly superior replacement benchmark” stop condition is **not proven**;
- `GSE334718` has nevertheless been frozen as an **untouched candidate secondary lock** before any per-oligo outcome inspection;
- its archive must remain opaque until a dedicated prospective acquisition/reconstruction protocol is written and committed;
- Phase 2 may proceed later using only the already-spent TDP data, while both Astrocyte and `GSE334718` remain unavailable for model design.

Phase 1 decision: **CONDITIONAL GO** to Phase 2, with two sealed external resources and no v3 model training performed.

## Search protocol

### Question

The primary question was whether a public 2024–2026 dataset can legitimately test minimal cis-sequence interventions for RNA localization in unseen parent contexts. Secondary questions were whether newer representation models, motif resources or mechanistic datasets materially change the v3 design space.

### Eligibility standard for an independent intervention benchmark

A candidate was required, ideally, to provide:

1. exact parent sequence;
2. exact mutant sequence or a deterministic reconstruction;
3. intervention-level localization outcome;
4. more than one independent natural parent context;
5. enough interventions within each parent to support ranking, not merely binary classification;
6. a biological context relevant to mammalian RNA localization;
7. a public, stable and reproducible data route;
8. outcomes that had not already influenced RNAddress model selection.

The following were not promoted to independent minimal-edit validation:

- overlapping tiling libraries without parent-mutant pairs;
- fixed-backbone motif insertion screens;
- forward transcript localization atlases;
- a few hand-designed variants;
- trans-acting RNA transport systems;
- perturbations where localization is changed by proteins, guides or drugs rather than by a reconstructable cis edit;
- datasets with no public construct-level outcomes.

### Sources and query families

The audit searched PubMed/PubMed Central, Europe PMC-style indexed records, Crossref, bioRxiv, medRxiv where relevant, GEO, SRA/BioProject metadata, ENA/ArrayExpress/BioStudies, GSA-Human, Zenodo, Dryad, Figshare, GitHub, journal supplements and institutional repositories. Search terms combined:

- `RNA localization`, `mRNA localization`, `subcellular RNA localization`;
- `neurite`, `soma`, `astrocyte`, `nuclear retention`, `RNA export`, `nuclear speckle`;
- `MPRA`, `MPRNA`, `saturation mutagenesis`, `SNV`, `mutagenesis`, `cis-regulatory element`, `RNA zipcode`;
- `RNA design`, `inverse design`, `sequence optimization`;
- `RNA foundation model`, `RNA language model`, `3UTRBERT`, `HydraRNA`;
- `RBP binding`, `RNA stability`, `m6A`, `3'UTR`.

Repository searches were repeated with DOI, title, author and accession variants. Search-engine snippets were never treated as enough to establish data eligibility: accession metadata, public file inventories or primary papers were checked where available.

## New candidate: Moffatt 2026 / GSE334718

### What is directly verified without outcome access

Primary records:

- paper DOI: [`10.64898/2026.06.09.731215`](https://doi.org/10.64898/2026.06.09.731215);
- PubMed: [`PMID 42327238`](https://pubmed.ncbi.nlm.nih.gov/42327238/);
- PMC metadata-only record: [`PMC13277945`](https://pmc.ncbi.nlm.nih.gov/articles/PMC13277945/);
- GEO: [`GSE334718`](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE334718);
- BioProject: `PRJNA1476227`.

The preprint abstract reports:

- tens of thousands of mutant localization elements;
- quantitative subcellular localization measurement in neuronal cells;
- minimally active elements of approximately 200 nt;
- multipartite subsequences with different mutational tolerances;
- orthogonal single-molecule microscopy in primary rat neurons.

GEO series- and sample-level metadata verify:

- organism: *Mus musculus*;
- experimental cell line: CAD neuronal cells;
- localization readout: targeted RNA sequencing in neurite and soma fractions;
- two reporter RNAs: GFP and firefly luciferase;
- UMI deduplication;
- five library families: `mutation`, `necessity`, `SHAPE`, `shuffle`, `sufficiency`;
- 16 processed count files per family: two reporters × two fractions × four replicates;
- 80 processed `.umis.txt.gz` files in total;
- each processed sample reports, for every oligo, the read count and unique-UMI count.

The public archive was downloaded but never opened:

| Artifact | Bytes | SHA-256 | Access status |
|---|---:|---|---|
| `data/raw/moffatt_gse334718/GSE334718_RAW.tar` | 12,697,600 | `abc6e571ed68833e3fb0c0028209303a0f468347ac5f6efbeffd788c35c7ade1` | Hashed as opaque bytes; not listed, extracted or parsed |
| `data/raw/moffatt_gse334718/filelist.txt` | 6,076 | `249d48f5389792db0024307dabea5782d76e6ee8af69f5da50b8e4c6ace77c6b` | Safe file-name/size metadata read |
| `data/raw/moffatt_gse334718/GSE334718_series_brief.soft` | 5,288 | `a1492329336e26c1007488bf5207352abe40af4da0f571a431c35c79f448b430` | Safe series metadata read |

The frozen boundary is recorded in `data/frozen/moffatt_2026_candidate_lock_manifest.json`. A safe audit verifies hashes and the 5 × 16 file design without opening the TAR.

### What is deliberately not known yet

No `.umis.txt.gz` header or row has been opened. Consequently, the audit has not yet established:

- the exact number of independent natural parent elements;
- the exact number of constructs or interventions per parent;
- whether every processed row carries an exact sequence or an opaque oligo identifier;
- where the known-oligo design dictionary is publicly stored;
- whether each intervention can be reconstructed into a unique parent/mutant pair;
- which mutation-library constructs are exact SNVs versus multi-base or compositional perturbations;
- any localization effect, rank, distribution, correlation or model result.

These are not cosmetic omissions. Until the input mapping is independently reconstructed and audited, `GSE334718` must be called a **candidate intervention lock**, not a validated benchmark.

### Comparison with Astrocyte

| Axis | Moffatt 2026 candidate | Astrocyte SN-MPRA |
|---|---|---|
| Scale | Abstract says tens of thousands of mutants | 4,553 reconstructed exact SNVs |
| Parent contexts | “Several” elements; exact count not yet recovered | Eight exact 190-nt parents |
| Intervention types | Mutation, necessity, SHAPE, shuffle, sufficiency | Near-exhaustive single-nucleotide substitutions |
| Cell context | CAD neuronal cell line; selected microscopy validation in primary rat neurons | AAV assay in adult mouse brain astrocytes in vivo |
| Reporter context | GFP and firefly reporters | One AAV reporter design |
| Measured properties | Public neurite/soma count data confirmed | Localization, ribosome occupancy, local translation and expression proxy |
| Independence from RNAddress development sources | Same Taliaferro/Arora experimental lineage | Different laboratory and in-vivo astrocyte context |
| Exact outcome-free feature reconstruction | Not yet available | Complete, SHA-frozen 4,553-row artifact |
| Current RNAddress status | Untouched candidate secondary lock | Untouched primary external lock, subject to disclosed historical schema exposure |

Conclusion: Moffatt is potentially superior for intervention breadth and mechanistic dissection, but not globally superior as a final independent test. It should be protected because it may become an excellent **second prospective lock** after outcome-blind sequence reconstruction. It should not replace or weaken the Astrocyte protocol.

## Intervention-dataset eligibility matrix

| Dataset / primary source | Assay and scope | Parent / intervention structure | Public properties | Legitimate RNAddress role | Decision |
|---|---|---|---|---|---|
| **Moffatt 2026**, DOI [`10.64898/2026.06.09.731215`](https://doi.org/10.64898/2026.06.09.731215), `GSE334718` | CAD neurite/soma MPRA; five designed libraries; two reporters; four replicates | Tens of thousands reported; exact parents and pairing not yet reconstructed | Per-oligo counts and raw reads public | Candidate secondary frozen validation if exact mapping passes | **Promising, sealed, eligibility incomplete** |
| **Astrocyte SN-MPRA**, [`GSE330741`](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE330741) | AAV MPRA in adult mouse astrocytes in vivo | Eight parents; 4,553 exact SNVs | Localization, ribosome occupancy, local translation, expression proxy | Primary frozen independent intervention validation | **Retain as flagship lock** |
| **N-zip**, DOI [`10.1038/s41593-022-01243-x`](https://doi.org/10.1038/s41593-022-01243-x) | Primary cortical-neuron neurite/soma MPRA and stability perturbations | 15 development parents; 4,395 truth-safe exhaustive SNVs | Localization and auxiliary stability-related assays | Core grouped development only; historical lock is spent and failed | **Development** |
| **TDP-43**, DOI [`10.1038/s44318-025-00653-4`](https://doi.org/10.1038/s44318-025-00653-4) | Neurite/soma MPRA plus TDP knockout and SLAM-seq | 16 genes; 4,566 multi-base motif-complement pairs | Localization, TDP dependence, reporter stability, binding | Post-lock diagnosis/development only | **Spent; never validation again** |
| **Mikl**, DOI [`10.1093/nar/gkac806`](https://doi.org/10.1093/nar/gkac806), `GSE173098` | Neuronal fixed-backbone motif/sufficiency libraries with ActD stability | Many constructs, but interventions are heterogeneous and context-fixed | Localization and selected stability measurements | Auxiliary representation/mechanism learning | **Not independent minimal-edit validation** |
| **Arora**, DOI [`10.1093/nar/gkac763`](https://doi.org/10.1093/nar/gkac763), `GSE183192` | Tiled endogenous 3'UTR fragments in neuronal cells | Thousands of overlapping tiles; no general parent-mutant pairing | Forward localization activity | Forward representation/pretraining | **Forward only** |
| **Nuclear-speckle splicing logic**, DOI [`10.1093/nar/gkag174`](https://doi.org/10.1093/nar/gkag174), `GSE318459`, [Zenodo `18598678`](https://zenodo.org/records/18598678) | Imaging of designed splice-site/motif constructs and isolated disease exons in HeLa cells | Many designed minigenes; only a small number of biologically grounded SNV comparisons | Speckle partition coefficients, selected splicing/degradation kinetics | Mechanism prior and small secondary sanity check | **Too small/fixed for broad validation** |
| **SRLE-seq**, DOI [`10.34133/csbj.0107`](https://doi.org/10.34133/csbj.0107), `HRA016642` | MALAT1 fragments and all 4,096 6-mers in HBB reporters, HEK293T | Fixed backbone; motif insertions rather than minimal edits to natural parents | Nuclear/cytoplasmic enrichment and nuclear-retention scores | Motif/mechanism prior | **Not independent intervention validation** |
| **mutREL-seq**, `GSE107131` / `GSE134287` | Chromatin/cytoplasm localization; one randomly mutagenized NXF1 element | One 162-nt parent; 469 observed mutation/deletion events | Compartment enrichment; U1 mechanism | Secondary single-parent mechanism test | **Insufficient parent breadth** |
| **CRISPR-TO**, DOI [`10.1038/s41586-025-09020-z`](https://doi.org/10.1038/s41586-025-09020-z) | Programmable guide/dCas13-mediated RNA relocation in cells and neurons | Guide/protein interventions, not cis sequence edits | Localization and functional phenotypes | Capability/novelty comparator | **Wrong intervention class** |
| **SPRAWL / RNALocate / APEX-style atlases** | Forward localization measurements and databases | Natural transcript observations, no measured cis counterfactuals | Compartment labels or spatial scores | Forward representation and biological priors | **Not intervention validation** |

No other searched 2024–2026 record met the parent-mutant-localization requirements. Zenodo, Dryad and Figshare hits were principally analysis code, imaging data, forward spatial transcriptomics or nuclear-speckle resources. The new pyTrance spatial record is forward co-localization rather than a sequence intervention landscape. No additional valid construct-level intervention lock was found in ENA/ArrayExpress/BioStudies, GSA-Human or GitHub beyond the studies above.

## Representation-method refresh

The search supports a small, prespecified representation benchmark later; it does not justify a model zoo.

### 3UTRBERT — priority candidate

Primary paper: Yang et al., **“Deciphering 3'UTR Mediated Gene Regulation Using Interpretable Deep Representation Learning,”** *Advanced Science* 2024, DOI [`10.1002/advs.202407013`](https://doi.org/10.1002/advs.202407013). Official code and checkpoint links: [`yangyn533/3UTRBERT`](https://github.com/yangyn533/3UTRBERT).

Evidence relevant to RNAddress:

- pretrained specifically on aggregated human 3'UTR sequences;
- evaluated on RBP binding, m6A sites and subcellular localization;
- official code exposes embedding extraction and mutation analysis;
- 3-mer and 4-mer checkpoints are public.

Limitations:

- its reported localization benchmark is forward prediction, not mutation-effect ranking;
- human 3'UTR pretraining does not guarantee transfer to mouse neuronal MPRA constructs;
- legacy Python/PyTorch requirements may complicate reproducibility;
- any pooling choice creates researcher degrees of freedom.

Phase 3 implication: compare one prespecified checkpoint/tokenization and a small pooling set under identical grouped downstream evaluation. No fine-tuning on external locks.

### HydraRNA — feasible long-context candidate

Primary paper: Li et al., **“HydraRNA: a hybrid architecture based full-length RNA language model,”** *Genome Biology* 2025, DOI [`10.1186/s13059-025-03853-7`](https://doi.org/10.1186/s13059-025-03853-7). Official code/checkpoints: [`GuipengLi/HydraRNA`](https://github.com/GuipengLi/HydraRNA); archival code: [Zenodo `17337346`](https://doi.org/10.5281/zenodo.17337346).

Evidence relevant to RNAddress:

- pretrained on 28.1 million coding and non-coding RNAs;
- supports inputs up to approximately 10 kb;
- public 12-layer, 1,024-dimensional checkpoint and extraction code;
- evaluated on RBP binding, structure, splicing, polyadenylation, stability, translation and mutation effects.

Limitations:

- no direct localization-intervention evidence;
- installation requires a Linux/CUDA stack with Mamba/FlashAttention dependencies;
- model size and per-token embeddings may be expensive for exhaustive SNV enumeration;
- use must be benchmarked as frozen representation extraction, not accepted from paper-level task performance.

### Existing SpliceBERT — mandatory baseline

SpliceBERT remains the only contextual representation already shown to help RNAddress v2 development. It must remain in the same downstream benchmark to separate a true representation improvement from changes in modeling complexity.

### Other models

RNA-FM, RiNALMo, mRNA-LM and newer broad RNA models remain relevant background. They are not promoted into the initial v3 benchmark because the protocol explicitly calls for a small set and 3UTRBERT/HydraRNA are better aligned to 3'UTR regulation or full-length mRNA properties. A later substitution is justified only if a priority checkpoint is technically unavailable, and that substitution must be logged before outcome-bearing development runs.

## Mechanism and annotation refresh

### Stability is a required hypothesis, not an optional feature

The neuronal stability study [Loedige et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC10529935/) shows that mRNA half-life, m6A, AU-rich elements and codon optimality can causally alter neurite accumulation. The TDP-43 study independently links motif-dependent localization to reporter stability and SLAM-seq measurements. These sources justify a separate predicted-stability block and the Phase 2 test of whether TDP transfer failure differs between stability-dominated and non-stability-dominated genes.

They do **not** justify treating predicted half-life as measured localization mechanism, nor do they establish that every localization element acts through stability.

### Public RBP resources are now strong enough for a frozen motif panel

- [CisBP-RNA](https://cisbp-rna.ccbr.utoronto.ca/) build 2.0 was updated in 2025 and exposes experimentally determined and inferred RBP specificity models across many species.
- [ATtRACT](https://attract.cnic.es/documentation) provides experimentally supported RBP motifs and source publications.
- [ENCODE eCLIP](https://www.encodeproject.org/eclip/) provides standardized binding-site evidence with replicate and input-control requirements.

For v3, direct experimental motifs should be preferred over inferred motifs. RBP inclusion should be defined by public biological relevance to transport, stability, neuronal regulation, nuclear retention or the TDP mechanism before N-zip outcome comparison. Hundreds of unfiltered motif columns would recreate an uncontrolled feature-search problem.

### Structure remains local and falsifiable

Moffatt 2026's multipartite result and the TDP accessibility observations support local structure/accessibility deltas, but neither proves that generic global MFE will help. The structure block should remain edit-centered, low-dimensional and subject to grouped ablation.

### Nuclear localization is a separate mechanism regime

The 2026 nuclear-speckle study and SRLE-seq support splice-site grammar, SR/hnRNP motifs, U1 recognition and fixed-backbone nuclear-retention scores. These are useful mechanism priors and future compartment extensions. They should not be mixed into neurite/soma labels as if all localization mechanisms were homogeneous.

## Problems discovered

1. **A major new dataset appeared after the earlier audit.** Literature freshness is consequential; `GSE334718` would have been missed by relying on the v2 inventory.
2. **The most promising new dataset lacks an immediately visible outcome-free design dictionary.** Public outcomes alone do not make a valid inverse-design benchmark.
3. **The Moffatt study is not laboratory-independent from core neuronal development resources.** Even if used as a lock, it tests construct and parent transfer more than lab transfer.
4. **Intervention heterogeneity is substantial.** Mutation, truncation/necessity, shuffle, SHAPE and sufficiency constructs must not be pooled as interchangeable SNVs.
5. **The bioRxiv full-text and supplement endpoints were rate-limited during the audit.** Eligibility claims were therefore restricted to the abstract, GEO series/sample metadata and the public file inventory. The missing design details are explicitly unresolved rather than inferred.
6. **The acquisition generator contained a stale SRLE-seq DOI.** It was corrected from `10.1093/csbj/csaf107` to the published DOI `10.34133/csbj.0107`.
7. **No foundation model has demonstrated held-out RNA-localization intervention ranking.** Representation papers provide candidates, not evidence that v3 will work.

## Governance decision and next authorized work

### GO / NO-GO determination

**CONDITIONAL GO to Phase 2 diagnosis only.**

Conditions:

1. Astrocyte outcomes remain sealed under the Phase 0 fail-closed loader.
2. `GSE334718_RAW.tar` remains unextracted and unavailable to all development/model-selection code.
3. Phase 2 uses TDP only as explicitly post-lock diagnostic/development data.
4. Before any Moffatt outcome access, a dedicated protocol must define:
   - outcome-free recovery of the oligo sequence dictionary;
   - exact parent-mutant reconstruction criteria;
   - intervention-class separation;
   - parent-level grouped split or full external-lock role;
   - metrics, comparators and anti-concentration rules;
   - immutable prediction and hash chronology.
5. If no outcome-free exact mapping can be recovered, Moffatt is downgraded to literature/mechanism evidence and is never represented as an independent intervention benchmark.

### What was not done

- No v3 model was trained.
- No N-zip or TDP outcome experiment was run.
- No Astrocyte source outcome was opened.
- No Moffatt per-oligo count, row, header, distribution or result was opened.
- No architecture, threshold, feature family, seed or stopping rule was selected using either sealed dataset.

## Files created or updated in Phase 1

- `reports/v3_literature_and_data_audit.md`
- `reports/v3_experiment_log.md`
- `data/frozen/moffatt_2026_candidate_lock_manifest.json`
- `src/pairing/audit_moffatt_candidate.py`
- `tests/test_pairing.py`
- `data/manifests/acquisition_manifest.csv`
- `src/acquisition/build_manifests.py`

Raw downloaded artifacts are intentionally ignored by git under `data/raw/moffatt_gse334718/`; their immutable hashes are committed in the candidate-lock and acquisition manifests.
