# Independent stability model: reconstruction checkpoint

Status: independent grouped validation completed; **both cell predictors failed
admission and are excluded from primary localization features**.

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
validation of every variant. Full hg38 retrieval/mapping subsequently completed,
requiring each pair to pass the same allele, sequence and GC checks.

Before training, exclude overlap with localization development genes/sequences;
28 gene-symbol overlaps were identified in the full supplement audit. Then use
grouped external-only validation for the proposed log2(mutant/reference
half-life) target. No localization label may train or select this predictor.
No credible performance estimate exists yet, and M3/M5/M6 stability inclusion
remains conditional on successful reconstruction and independent validation.

## Prospective external-only validation design

Before any real external predictor fit, the versioned design specifies three
recipes: Ridge with alpha 10 or 100 and a fixed shallow histogram-boosted model.
Inputs are paired 1–4-mer density differences; the nonlinear model can also use
symmetric pair-average mono/dinucleotide composition. Training includes reverse
pairs within the same group; antisymmetrized inference enforces a zero prediction
for identical alleles and sign reversal when reference and mutant are exchanged.
This is an independently trained paired-effect model, not a pretrained RNA LM.

Use five outer and three inner folds, joining genes and sequence pairs with
at least 95% global identity. Exclude development genes, exact containment in
development reporter sequences, and at least 90% global sequence identity.
Selection uses inner gene-macro MSE only. SH and HEK are evaluated independently.
Admission requires at least 200 independent groups, OOF Spearman at least 0.15
with a positive group-bootstrap 95% lower bound, and at least 2% gene-macro MSE
improvement over **both** the zero-delta and training-mean baselines. These are
new external-resource admission criteria, not changes to FinalShot gates. A
failed model is excluded without a subsequent architecture or threshold search.

The validation runner refuses real fitting until predictor code and design
match committed Git bytes. External inputs and exclusions are hashed into a
separate training freeze before any model fit. No successful external score has
yet been observed when the design was committed at `ccc50ca`.

## Completed independent validation — negative result

The full mapping recovered 1,022 unique observed reference/mutant pairs.
After excluding 22 development-overlapping/missing-gene pairs, 1,000 pairs in
651 connected external groups remained before cell-specific half-life QC.

| External cell | Eligible pairs / groups | OOF Spearman (group-bootstrap 95% CI) | MSE improvement vs training mean | Admission |
|---|---:|---:|---:|---|
| SH-SY5Y | 682 / 480 | 0.03672 (−0.04454, 0.11936) | −3.295% | Failed |
| HEK293T | 990 / 648 | −0.02707 (−0.09265, 0.03977) | −4.754% | Failed |

The boosted recipe was chosen independently in every outer fold by inner
gene-macro MSE. Error was also worse than the zero-delta baseline: −3.458% and
−4.595% relative improvements for SH and HEK, respectively. All ten outer
prediction checkpoints, inner recipe scores, 2,000 group bootstrap values per
cell, exclusions and training-input hashes are preserved. No final stability
model was exported or applied to localization data because admission failed.

This is failure of the declared compact external-prediction attempt, **not proof
that RNA stability is irrelevant**. Exact-sequence recovery covers only part
of the source library; the external assay and engineered representations also
limit transportability. Those qualifications do not turn the failed validation
into a pass. No post-result threshold or architecture search will be performed
under this frozen external design. Remaining Mechanism-v2 blocks proceed without
an independently validated stability prediction.

The spreadsheet was not edited. All extraction, raw-read validation and mapping
work occurs in the isolated Mechanism-v2 namespace. N-zip and Astrocyte remain
unopened.
