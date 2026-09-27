# GSE330741 pre-fit freeze

Protocol commit: `0b100d32a106d038deedcd98c1cdba2d53c0663e`

Manifest timestamp: 2026-09-26 23:09:01 UTC (exact fractional timestamp in the JSON manifest). Both protocols, evaluation configuration, feature/model/metric implementations and all 4,553 source-only candidate predictions were committed before mutation outcome access in this analysis. This marker is committed separately because the protocol commit must already exist to record its hash.

SHA-256 admission protocol: `ee576140c1c7f276d05b3ebfeafa714a0b0e2141392dfccb1ca0507d72468e36`.

SHA-256 external-test protocol: `2f397abfe199a67e62d414ce5bca13c28be0351e317e8db7828adcc8fffc8470`.

SHA-256 prefit manifest: `1f56dc0610a40f1426cb016112643137851fd466cfe096daa22a684371c74e36`.

SHA-256 precomputed predictions: `2c1bcaa2f6118a930c44392d813b1fda51d1c2d3a82ed9b0939e2262e7397d64`.

The 37-file manifest is `results/generalization_20260926/prefit_freeze.json`. Twelve scoped synthetic tests passed, including outer-label invariance of model selection and overlap exclusion. No unfiltered pytest was run.

- A primary: `srle_2mer_full`, original SRLE sequence-holdout fit plus its existing composition fallback; full-insert overlapping-count differences; fixed sign +1. No target calibration or sign flip.
- A primary metric: unweighted mean parent signed Spearman. Required controls: no change, frozen source composition, source-only AU and substitution; all other declared k-mer controls retained.
- B conditional primary: `simple_full_delta2` versus `simple_full`; nested Ridge alpha [1,10,100], training-only scaling/selection, parent-balanced training, centered training-parent nuisance, complete parent and overlapping-interval purge. B runs only when A does not strongly succeed.
- Target: author normalized SN-input/cortex-input log2 localization coefficient, mutant minus exact 190-nt WT. The endpoint differs from SRLE nuclear retention.
- QC: author poor-cloning parent excluded; exact one-SNP lineage; finite mutant and WT; at least two matched positive CPM replicate pairs; no FDR/sign/magnitude filtering; no silent ambiguous mapping repair.
- Unit: seven eligible parent elements in five nonoverlap components from two genes, subject to frozen QC. Bootstrap components 10,000 times, seed 20260926; exact block sign flips. These are descriptive small-sample intervals.
- Candidate set: every admitted SNP for each parent; both increase and decrease; lexical ID ties; no outcome-based subset or abstention. Uniform expectation, regret, wrong direction and top-5 recovery are predeclared.

Historical status is **PARTIALLY EXPOSED**, not pristine untouched: three result rows were printed before the August freeze, prior mapping/testing code loaded the source worksheet, and aggregate literature excerpts were seen. No documented target-outcome model tuning was found; absence of undocumented influence cannot be guaranteed. Current-phase sequence designs and source predictions were outcome-free. Original SRLE analyses and protected unrelated datasets remain unchanged.

**OUTCOMES MAY NOW BE OPENED** after this record is committed and the executable freeze check passes. Current user authorization covers the specified GSE330741 localization reveal and fixed A/conditional B tests. It does not authorize reclassifying the historical exposure, changing frozen decisions, or reopening GSE334718 as an untouched test.
