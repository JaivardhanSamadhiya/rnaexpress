# External fragment-selection pilot: Shukla 2018

AI-authored technical protocol, 23 September 2026 UTC. Primary paper:
https://doi.org/10.15252/embj.201798452 ; public GEO GSE98828. The article and
supplements are CC BY 4.0. Source attribution and download receipts are retained.

Question: can a fixed sequence model trained in the unspliced-HBB MCF7 reporter
select nuclear-enriching fragments in the independent fsSox2 HeLa reporter,
beyond base composition and the already-known CCC motif? This is an external
fragment-selection pilot, not a novel molecular mechanism or minimal-edit test.
Resource choice follows earlier failed transfers. Literature conclusions are
known; target numeric localization counts have not been examined.

## Sequence admission and limitations

The original 110-nt oligo map is not supplied by the downloaded supplements or
current author repository. An ungapped de novo reconstruction from a bounded
total-RNA FASTQ prefix FAILED its author-reference consistency check and is not
admitted. Its intermediate consensus and failure are preserved separately.

The substitute is explicitly reference-assisted: archived NCBI version-1
accessions must match the metadata length exactly, or differ only by terminal
A bases removed to that length. Do not guess other trimming, isoforms or final
tile coordinates. Exclude terminal tiles and nonunique barcodes. At least five
reads with Q30 barcode/Q20 insert must exactly match the expected last 90 bases,
and must comprise at least 50% of such reads. Those QC choices were made without
target localization counts. This yields 330 fragments across 23 genes; thirteen
gene sets have at least ten fragments. FIRRE orthologs form one uncertainty unit.

The first 20 bases are reference-derived and not directly measured per barcode.
The 16-MiB prefix comes from total-RNA biological replicate 1, technical replicate
1 (SRR5528987). Selection favors sufficiently represented, sequence-concordant
constructs. Published counts may include synthesis variants sharing a barcode.
PCR reads are not independent molecules. This subset cannot represent the whole
assay; confirmation in replicates 4-6 would still reuse the selected sequences.

## Source isolation and fixed prediction

Use only the original 3,235 context-calibration SOURCE rows, never its calibration,
development or confirmation outcomes. Exclude entire source components with a
named target gene alias (all 38 target genes), a shared exact 40-nt tract with an
admitted target insert, or >=95% normalized global Levenshtein similarity. Name
aliases include ANCR/DANCR, FIRRE(HG/MM) and lincFOXF1/FENDRR. This is not a complete
paralog ontology. Require >=500 finite source rows and >=20 source components.

Use Unspliced_Nuc/Cyto as the source target, chosen because fsSox2 is an unspliced
reporter construct. Source outcome loader may parse all four already-open source
context columns, but only Unspliced enters fitting. Fit StandardScaler and Ridge
alpha=100 on normalized 1-3-mer frequencies (84 features). The composition
baseline uses the same source rows, scaler and alpha on four nucleotide
frequencies. The other baseline is overlapping CCC count, with larger scores
meaning more nuclear retention. No target fitting, sign flips, tuning or model
selection. Freeze all predictions, source rows, code, inputs and this protocol,
and commit the freeze before target numeric access.

## Endpoints and gate

Discovery opens only Nuclei1-3 and Total1-3 for metadata-eligible gene sets.
Counts are author-normalized values. Per replicate use log2(Nuclei/Total) only
when both values are finite and positive; no pseudocount or raw-count-depth
interpretation. Retain a common candidate set finite across all three replicates.
Require >=10 candidates and nonzero outcome range in every replicate per gene.

For each gene and replicate choose the highest and lowest predicted fragment.
For exact prediction ties, average the outcome of all tied candidates. Normalize
each directional regret by that gene/replicate's outcome range, then average the
two directions. Random selection has expected two-direction regret 0.5.

Average genes within family, biological replicates, then families equally.
Use 5,000 paired family bootstrap draws, seed 20260923, with percentile 95%
intervals. These intervals describe these families and omit source-fit
uncertainty. Overlapping fragments and the two FIRRE orthologs are not separate
independent units.

Discovery passes only if there are >=12 families and source_kmer has >=0.05 regret
gain over EACH of source_composition, CCC, and random, a positive lower bootstrap
bound for EACH, and positive gain in EACH biological replicate against EACH.
All conditions are required, not a choice among endpoints. Failure leaves
replicates 4-6 closed. If discovery passes, unchanged frozen predictions and
discovery-eligible IDs may be evaluated once in replicates 4-6 using the same
metrics and gate. A confirmation pass would support this narrow selected-subset
transfer, not universal RNA localization, minimal edits or an STS outcome.

No changes to historical gates, outcomes, code or user modifications. No spending,
scheduled tasks, external messages, model downloads or protected-data access.
