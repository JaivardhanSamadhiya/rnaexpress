# Independent stability model: reconstruction checkpoint

Status: external sequence identity reconstruction, **not a trained model**.

The [Su, Wang et al. eLife study](https://elifesciences.org/articles/97682)
provides a genuine independent RNA-decay assay in HEK293T and SH-SY5Y. The
read-only supplement audit found 5,072 variant/UTR records with no duplicate
variant/UTR keys or spreadsheet formulas. Positive finite 3′UTR reference/mutant
half-life pairs number 2,486 in HEK and 1,410 in SH. These counts are not yet
sequence-verified training-example counts. No significance-based filter is used.

The workbook contains alleles, coordinates and composition summaries, **not full
assayed sequences**. Training on invented sequence windows would be invalid.
The author analysis tables and GEO count tables do not resolve this omission.
Accordingly, the reconstruction retrieves original early-time-point HEK read
pairs through [ENA](https://www.ebi.ac.uk/ena/browser/view/PRJNA899463).
Both SRR22227655 mate files passed their published size/MD5 checks and were then
SHA-256 inventoried. The two compressed files total 836,719,719 bytes.

The outcome-blind sequence-discovery pipeline accepts only an unambiguous exact
mate overlap, complete published primers and high-quality coverage. It records
every rejection category. A 10,000-pair pilot recovered 4,984 accepted read pairs;
the full run is now complete: 6,008,214 pairs processed, 2,835,528 accepted, and
78,052 distinct insert sequences supported by at least ten read pairs. This is
far more than the intended library size, consistent with substantial sequence
heterogeneity; support alone is not a valid identity criterion. Sequence support
means read-pair support, not biological replication. Unsupported/noisy sequences
do not become fabricated variant labels.

Exact variant mapping must independently establish reference genome build,
transcript strand, reference allele, mutant allele and the presence of both
assayed sequences. The mapping code also requires published reference/mutant GC
fractions to agree. A pilot retrieves both hg38 and hg19 at 32 outcome-blind
positions; coordinates alone are not treated as evidence for a genome build.
Ambiguous identities are retained as unresolved, not assigned using half-life.
The pilot evaluated 65 variant IDs in the 32 windows: 21 uniquely matched pairs
in hg38 and zero in hg19. This supports proceeding with hg38, but is not blanket
validation of every variant. Full hg38 retrieval/mapping is now underway, still
requiring each pair to pass the same allele, sequence and GC checks.

Before training, exclude overlap with localization development genes/sequences;
28 gene-symbol overlaps were identified in the full supplement audit. Then use
grouped external-only validation for the proposed log2(mutant/reference
half-life) target. No localization label may train or select this predictor.
No credible performance estimate exists yet, and M3/M5/M6 stability inclusion
remains conditional on successful reconstruction and independent validation.

The spreadsheet was not edited. All extraction, raw-read validation and mapping
work occurs in the isolated Mechanism-v2 namespace. N-zip and Astrocyte remain
unopened.
