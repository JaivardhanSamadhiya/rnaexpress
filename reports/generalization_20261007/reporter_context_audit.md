# SRLE reporter-context audit, 7 October 2026

**A 46-nt local synthesis context is verifiable from the published oligos. The
complete mature reporter RNA is not yet certified. A historical cell annotation
also needs an additive correction: the SRLE six-mer screen used HEK293T, while
the canonical cross-assay table labels SRLE as MCF7.**

This audit reads only the already cached public SRLE article, Supplement Tables
S1/S2, and existing local counting-source text. No outcome workbook, raw read,
Rep3 measurement, reserved confirmation outcome or model was loaded. No new
data download, biological fit or frozen-file modification occurred. The cached
article and supplement were rehashed against their original official-Europe-PMC
receipts before the two primer workbooks were explicitly whitelisted.

## Verified published context

The [primary article](https://doi.org/10.34133/csbj.0107) identifies HEK293T cells
and describes constructing N1-HBB from pEGFP-N1 by PCR and Gibson assembly.
Separate HBB genomic and spliced-transcript constructs were made. The six-mer
library inserts a degenerate six-base sequence at the HBB 3prime-UTR cloning
site; the article describes using intron-containing HBB for subsequent main
experiments. Table S1 supplies construction oligos, and Table S2 supplies
RT-qPCR primers. These facts establish design and study context, not a verified
full-length RNA sequence or per-clone splice state.

Official source copies and provenance:

- [Europe PMC article XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13191086/fullTextXML): cached `srle_article`, SHA-256 `12401286a3de1fa15a2910aaea8806a97ce993521ff09b7c772f4121c67ecb3c`.
- [Europe PMC supplementary files](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13191086/supplementaryFiles): cached `srle_epmc_supplement`, SHA-256 `ff42cc9b5d7f0bb703369370cfc29c1d51614bca677294a2ffbb3bbec61344a9`.
- Only `Supplement Table1.xlsx`, sheet `Table S1`, and `Supplement Table2.xlsx`, sheet `Table S2`, were opened from nested `csbj.0107.f1.zip`. All numerical outcome workbooks remained unopened. Per-member hashes and 19 selected primer records are in [reporter_context_metadata.json](D:/rnaexpress/artifacts/generalization_20261007/reporter_context_metadata.json).
- [The bounded extraction/audit code](D:/rnaexpress/src/generalization_20261007/reporter_context_audit.py) does not import a source-outcome loader or execute downloaded author code.

## Exact local sequence that can be stated

Table S1's `Gibson_6mer_Random_F` is:

```text
GCCCACAAGTATCACTAAGC NNNNNN ATCATAATCAGCCATACCAC
       left 20 nt    6 nt        right 20 nt
```

The spaces are explanatory. The actual degenerate synthesis sequence has 46
nucleotides. `Gibson_6mer_Random_R` is its exact reverse complement. In this DNA
notation, a measured six-mer can replace the six Ns to specify the **published
local synthesis design**. RNA notation substitutes U for T, while retaining the
same orientation. This is not a claim to recover the full mature transcript.

Three independent metadata checks agree:

1. Reverse-complementing the published genomic HBB reverse primer
   `GCTTAGTGATACTTGTGGGCCAG` gives `CTGGCCCACAAGTATCACTAAGC`; its last 20 bases
   equal the left synthesis arm.
2. The published downstream N1-HBB linearization primer
   `ATCATAATCAGCCATACCACATTTGT` starts with the right 20-base synthesis arm.
3. The already implemented paired-read counter uses
   `ATCACTAAGC-[six-mer]-ATCATAATCA` and its reverse complement. These 10-base
   flanks are the terminal/initial halves of the two synthesis arms. This audit
   verifies the source-code definition, without rereading any FASTQ or claiming
   new experimental confirmation of all 20 flanking bases.

The extraction returned PASS for these checks. It also preserved the author
primer descriptions distinguishing genomic HBB with introns from blood-derived
spliced HBB cDNA. RT-qPCR primer sequences identify small assayed regions; they
do not specify the complete transcript, transcript ends, or a single mature
isoform in both fractions.

## Concrete annotation problem

`src/cross_assay_20260927/dataset.py` assigns `cell='MCF7'` to SRLE. The cached
paper's culture methods and six-mer-screen description identify HEK293T. The
earlier context-transfer reports also sometimes describe the source as
unspliced-HBB/MCF7. Those descriptions should not be propagated as authoritative
SRLE metadata.

This audit leaves the historical canonical table, reports and hashes intact.
The mismatch alone does not explain their numerical ranking results: the
current frozen ranking tracks do not feed the cell label into their latent
utility features. Future trans-expression or cell-context models must use an
explicit corrected metadata ledger and must not derive SRLE context from MCF7.
The screen's intron-containing plasmid also must not be equated with all measured
RNAs being unspliced; the nuclear/cytoplasmic samples can contain different
processing states, and per-clone isoform identity is unresolved here.

## What cannot yet be reconstructed authoritatively

| Missing link | Why the available metadata do not settle it |
| --- | --- |
| Exact amplified HBB donor/clone sequence | PCR endpoints and a human gene name do not certify every internal base, donor allele or cloned mutation. Choosing an arbitrary current NM accession would add an assumption. |
| Complete final backbone and junction sequence | The backbone name and homology arms constrain assembly but are not a sequence-verified deposited final clone. The inspected author repository tree has no clearly identified full reporter plasmid/GenBank file. This does not prove none exists elsewhere. |
| Exact TSS and 3prime cleavage/polyadenylation boundaries | CMV/vector origin and a 3prime-UTR insertion site do not uniquely determine the RNA endpoints experimentally produced. |
| Mature versus precursor RNA species | Genomic and spliced-cDNA designs are distinct; an intron-containing construct can generate multiple processed states. A genomic sequence must not simply be presented as mature RNA. |
| Per-clone cryptic splicing or sequencing variation | Primer design and six-mer counting identify local elements, but do not establish identical complete transcripts or absence of unintended splice events. |

The paper points to an earlier construction-method reference, Li et al.,
*Science China Life Sciences* 67 (2024), 2198–2212. That citation alone does not
provide a deposited sequence-verified reporter or identify the precise clone
used in this screen. This audit did not guess a whole HBB isoform or substitute
a generic pEGFP-N1 reference as the final expressed reporter.

## Practical consequence for the next experiment

The primer metadata resolves more local context than a bare six-mer: a future
separately frozen model can explicitly evaluate the author-designed 20+6+20
window, with a matched bare-six-mer control. This permits examining junction
words and local sequence/structure under an honestly partial context. It does
not license a full-reporter BERT embedding, whole-transcript structure claim,
independent biological test, or alteration of the currently running frozen
tracks. Local-window folding would represent that window and boundary convention
only, not validated full-reporter folding.

Full-context admission still needs authoritative clone/backbone sequence plus
transcript-boundary and processing evidence. Those missing records concern
metadata/provenance; favorable prediction scores cannot certify them. No author
contact was made and no reserved replicate was opened.
