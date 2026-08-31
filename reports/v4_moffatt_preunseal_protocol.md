# RNAddress v4 Moffatt outcome-blind pre-unseal protocol

Protocol freeze date: 2026-08-31  
Study: Moffatt et al., *Robust mammalian RNA localization elements are complex and multipartite*  
DOI/PMID/PMCID: `10.64898/2026.06.09.731215` / `42327238` / `PMC13277945`  
Public data: `GSE334718`, `PRJNA1476227`

## Outcome-blind design finding

NCBI MINiML metadata identifies exactly 80 CAD-cell MPRA samples: five assay families (mutation, necessity, SHAPE, shuffle, sufficiency) × two reporters (Firefly and GFP) × two compartments (neurite and soma) × four biological replicates. The exact GSM and processed filename mapping is frozen in `results/v4_phaseA/moffatt_geo_sample_manifest.csv`. This audit used paper/method metadata only. No processed count file was opened, and the contents of `GSE334718_RAW.tar` were neither listed nor extracted.

## Files authorized after this protocol commit

1. The sealed archive `data/raw/moffatt_gse334718/GSE334718_RAW.tar`, previously recorded as SHA-256 `abc6e571ed68833e3fb0c0028209303a0f468347ac5f6efbeffd788c35c7ade1`.
2. Exactly the 80 `*.umis.txt.gz` processed count members whose GSM accessions and full filenames are enumerated in `results/v4_phaseA/moffatt_geo_sample_manifest.csv`.
3. Public paper supplementary design/method files, public sequence dictionaries, and public analysis code required to map count-table oligo IDs to sequence and intervention design. These are not outcomes, but every acquired file must be hash-locked before use.
4. Raw-read metadata may be used to verify sample identity. FASTQ reprocessing is deferred unless processed counts fail an integrity check that raw reads can resolve.

No other result file is authorized without a protocol amendment committed before it is opened.

## What constitutes an outcome

Any per-oligo read count, UMI count, normalized abundance, neurite/soma ratio, reporter-combined value, replicate aggregate, significance statistic, or ranking derived from the 80 processed count files is an outcome. Filenames, GSM metadata, assay labels, construct dictionaries, and designed sequences are design metadata rather than outcomes.

## Mandatory unseal log

Immediately before opening the archive, the reconstruction script must calculate its SHA-256 and require an exact match to the frozen hash above. It must record UTC/local date, the current Git commit (which must contain this protocol), purpose `V4 DEVELOPMENT DATA SOURCE-TRUTH RECONSTRUCTION`, archive path/hash, and the irreversible status change `SEALED CANDIDATE -> V4 DEVELOPMENT DATA`. Moffatt must never again be described as independent validation.

## Construct identity and intervention mapping

Count keys must join by exact complete oligo identifier to a public design/sequence dictionary. Row order, approximate gene name, sample order, or outcome similarity may not be used. Each construct must map to an assay family, reporter, exact sequence, and declared biological localization element/background. Parent relationships are accepted only when explicit in design metadata or deterministically proven by sequence operations consistent with the methods.

For mutation, necessity, shuffle, sufficiency, and SHAPE families, the audit will derive—not infer from sample names—the operation, altered interval, substitutions/insertions/deletions, edit distance, changed fraction, parent sequence, and background/reporter relationship. SHAPE will be labeled a perturbation library, structural-measurement library, or other design only after inspecting methods/design files.

## Replicate outcome calculation

Primary sample unit is one biological replicate in one reporter and compartment. For each construct and reporter, compute a within-replicate log2 neurite/soma ratio only when both compartment counts pass predeclared count validity checks. Use the paper's pseudocount/normalization method when exactly recoverable; otherwise report raw paired ratios under a clearly separate reconstruction label and test reasonable fixed pseudocounts only as sensitivity analyses, never selecting one for desirable biological agreement.

The construct-level point estimate is the mean of valid replicate log2 ratios within reporter. Uncertainty is the standard error and a nonparametric replicate range; retain all replicate-level values. Firefly and GFP remain separate outcomes in Phase A. A cross-reporter summary may be descriptive only and must report reporter disagreement.

## Exclusions and missingness

Exclude or quarantine: archive hash mismatch; filename/GSM mismatch; duplicate `(sample, oligo)` keys with conflicting values; absent sequence dictionary entry; ambiguous parent mapping; invalid nucleotide sequence; impossible design operation; zero/insufficient counts under the paper's fixed filter; fewer than two valid paired biological replicates for an aggregate; or irreconcilable reporter/compartment labels. Exact duplicate sequences are retained once per outcome context with duplicate provenance. Zero is a measured count, not missing; absent, filtered, malformed, and non-finite states receive distinct machine-readable codes.

## Leakage-safe grouping hierarchy

The hierarchy, from broadest to narrowest experimental identity, is: study → assay family → biological localization element/gene → WT parent sequence → intervention family/design batch → exact construct sequence → reporter → biological replicate. Development splitting must hold out at least the biological localization element; gene-level holdout is the stricter primary sensitivity analysis. Variants of one parent, reporter measurements of one construct, and all replicates must remain in the same group.

## Gate before interpretation

The first post-unseal artifact must be a source-truth audit reporting exact parent-element count, gene count, construct/intervention count, per-family design semantics, edit-size distributions, duplicate/ambiguity/exclusion counts, replicate completeness, reporter concordance, and source/script/environment hashes. No model fitting, hyperparameter selection, feature selection, or candidate ranking is allowed during this reconstruction.
