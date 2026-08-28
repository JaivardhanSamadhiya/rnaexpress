# RNAddress v3 mechanistic feature audit

**Analysis class:** DEVELOPMENT — outcome-free feature construction

**Primary rows:** 4,395 exact N-zip SNVs in 15 parent RNAs

## Audit verdict

The frozen Phase 3 motif, local-accessibility, parent-state and parent-by-edit interaction block is reproducibly constructible for every N-zip row. The base block contains 93 finite features. It uses 4,410 exact sequence-specific ViennaRNA partition-function folds, cached by normalized-sequence SHA-256.

The block is intentionally low-dimensional relative to the 3,662 selected contextual/edit features and contains only interactions frozen in the protocol. No outcome-selected motif, radius, interaction or structural summary was added.

## Feature families

| Family membership | Features | Nonconstant |
|---|---:|---:|
| Motif core | 30 | 28 |
| Local accessibility | 25 | 25 |
| Parent state | 9 | 8 |
| Motif interactions | 15 | 14 |
| Parent-state interactions | 32 | 31 |

Memberships overlap deliberately. For example, `motif_delta × accessibility_delta_r10` belongs to both motif interaction and accessibility. This ensures an accessibility ablation removes every route by which accessibility can enter the model rather than leaving a disguised interaction behind.

## Motif block

The five frozen sequence-motif families are:

1. TDP-like UG-rich (`UGUGU`, `GUGUG`, `GUAUG`);
2. AU-rich (`AUUUA`, `UAUUUAU`);
3. Pumilio-like (`UGU[ACGU]AUA`);
4. cytoplasmic polyadenylation element (`UUUUAU`);
5. DRACH-like m6A context (`[AGU][AG]AC[ACU]`).

For each family, the matrix records parent count, mutant count, count delta, gained occurrences, lost occurrences and the fraction of union occurrences changed. Overlapping occurrences are counted. These are sequence patterns, not claims of universal RBP occupancy.

Four columns are constant in N-zip: parent Pumilio count, Pumilio loss, parent Pumilio density and `Pumilio delta × parent density`. Mutant Pumilio gains do occur, so the complete frozen family remains in the schema. Training-fold scaling maps constant columns to zero and Ridge leaves them inert. They are not removed using outcomes.

## Local accessibility

ViennaRNA partition-function base-pair probabilities provide unpaired probability for parent and mutant sequences. Features include parent, mutant and delta accessibility at:

* the edited nucleotide;
* radius 5;
* radius 10;
* radius 20.

The implementation excludes the Phase 2-rejected global MFE and whole-sequence structure summaries. All 4,410 folds are finite.

## Parent state and interactions

Outcome-free parent state contains GC fraction, AU fraction, normalized mononucleotide entropy, maximum homopolymer fraction and five motif densities. The allowed interactions are exactly:

* motif count delta × same-family parent motif density;
* motif count delta × parent edit-site accessibility;
* motif count delta × accessibility delta at radius 10;
* each of 12 valid reference→alternate classes × parent GC and AU fractions;
* accessibility delta at radii 5/10/20 × parent GC fraction.

A formal unit test holds the exact `C>G` edit class fixed while changing parent sequence, assigns weight only to the `C>G × parent GC` interaction, and requires the two predictions to differ. This demonstrates mathematically—not merely by matrix presence—that the architecture permits parent-dependent edit action.

## Stability auxiliary status

The two frozen stability columns are not in the 93-feature base matrix. They are added only after the selected 3UTRBERT Strategy-C TDP auxiliary predictor is built:

* predicted stability delta;
* predicted stability delta × parent AU fraction.

Their survival remains conditional on the frozen ablation criterion. No measured stability value will be required at N-zip inference.

## Measurement uncertainty audit

The N-zip supplement exposes aggregate localization outcomes but no deterministically construct-linked technical replicate measurements for all 4,395 SNVs. WT versus shScramble is a cross-condition comparison, not a same-construct technical replicate. Therefore `measurement-aware target not feasible` remains the correct conclusion; no standard errors, weighted likelihood or empirical-Bayes variance model will be invented.

## Reproducibility and integrity

Machine-readable artifacts:

* `results/v3_phase3/mechanistic_feature_schema.csv`
* `results/v3_phase3/mechanistic_feature_families.csv`
* `results/v3_phase3/mechanistic_feature_manifest.json`

Ignored, hash-recorded caches:

* `data/interim/v3_nzip_mechanistic_features.npy`
* `data/interim/v3_nzip_structure_cache.json`

The feature-cache SHA-256 is `e377869fbb69e4952c5bd7bc73f10339c26db2e4d18f63f9f23a6c65df0ea977`; the structure-cache SHA-256 is `a9b16cd3cf26b428244949c2517dfe4be62df3553567b72e7bdb41afc7ced068`.

Astrocyte outcomes were not opened, inspected, analyzed, recorded or used. The inherited historical complete-worksheet programmatic load remains disclosed. The sealed Moffatt archive was not listed, opened, extracted or used.
