# What this continuation established

**The generalizable-predictor goal remains unmet and the four-study gate remains NO-GO.** This continuation completed a diagnostic study of the already-exposed data; it did not train another model or consume another independent resource.

## Useful signal exists despite noisy ordering

| Assay | Agreement between replicate candidate orderings | Regret when selecting with other replicates | Uniform regret |
| --- | ---: | ---: | ---: |
| Astrocyte | 52.43% | 0.35181 | 0.50000 |
| Mikl | 54.71% | 0.43333 | 0.50000 |
| SRLE | 78.26% | 0.18357 | 0.50000 |

The first column compares individual replicates. The selection column uses the mean of available other replicates and evaluates the chosen candidate in the omitted replicate. These are different questions: modest overall order agreement can coexist with reproducible selection of useful extremes. This selection result uses measured outcomes, so it is neither a new sequence predictor nor an independent validation result. The raw-replicate and author-processed endpoints differ; do not subtract these regrets from the original model's primary regret and call the difference a measured performance ceiling.

Mean raw-contrast ordering agrees with the processed outcome ordering in 94.96% of astrocyte and 87.72% of Mikl comparable pairs. Thus a simple wholesale reversal/mismatch of those orderings is not supported as the main explanation. Legitimate estimator differences and incomplete raw-to-published provenance remain. Moffatt paired replicate reliability is unavailable in the admitted table.

## Two apparent explanations were narrowed

Exact feature collisions are rare for kmer123 and the two tested interaction representations. Their optimistic feature-equivalence regret bound is zero in every core assay. This rules against exact representational aliasing as a sufficient explanation; it does not establish that a linear model has enough capacity or that the right biology is encoded.

Unqualified feature-range flags initially marked every astrocyte, Moffatt and SRLE candidate. Many flags came from parent-constant features that cancel in a linear candidate ranking. After removing those, the interaction_3 ranking-relevant flagged fractions were **2.33% astrocyte, 49.25% Mikl, 2.99% Moffatt, and 39.64% SRLE**. These are component-macro fractions, not raw candidate proportions. Joint-distribution support and causal effects of extrapolation are still unknown. The full-parent interaction representation increases the Mikl fraction to **80.74%**, so adding wider context is not automatically a remedy.

## A concrete, falsifiable next question

The existing objective treats a hard aggregate preference as certain after balancing biological units. The observed difference in replicate reliability motivates comparing hard author preferences, hard raw-mean preferences, and soft replicate-vote preferences under the same representation and unchanged outer gate. The hard raw-mean control is necessary to distinguish estimator changes from uncertainty handling. See `next_hypothesis.md` for the proposed comparison and its failure criteria. No proposed model has been fitted or declared successful.

The next work should preserve every candidate, use only training-study replicates, retain the original assay/component balance, and compare all held-out assays. Reliability filtering against held-out outcomes, gate changes, and new independent-data discovery remain inappropriate. The diagnostic does not identify a unique cause of failed transfer, prove novelty, or raise the claim hierarchy above Level 1.

## Delivery and preservation

The primary diagnostic covered 26,258 candidate measurements, 15,704 replicate-pair/context comparisons, 31,416 omitted-replicate selections, and 27,180 representation/context entries. Five tie-aware pair-ordering checks passed against explicit pair enumeration. The ranking-support refinement separately verified parent-length cancellation in all 20 study/representation comparisons.

All 319 prior evidence-bundle members, 36 prefit hashes, and 33 preexisting modified tracked files were checked unchanged. The first diagnostic execution was stopped to fix repeated feature-array decompression; the rerun preserved earlier replicate tables byte-for-byte. Both input manifests are retained and the completed execution has its own code hash. Only new failure-audit namespaces were written. No money, downloads, scheduled tasks, broad pytest, reserved outcomes, or model fitting were used.

Detailed tables are in `results.md` and `ranking_support_refinement.md`; CSVs and verification receipts are in `results/failure_audit_20260928`. The archive is an auditable diagnostic supplement, not a standalone runtime or a replacement for the previous cross-assay evidence archive.
