# RNAddress v3.5R truth-reconstruction verdict

## Final decision: NO-GO — N-zip cannot be recovered reliably from public historical materials

The raw reads, design, sequence identities, duplicate structure, and a deterministic modern source-equivalent reconstruction were recovered successfully. The historical experimental truth layer was not.

The mandatory stop conditions are triggered because:

1. the literal published coverage rule yields 5,787 UMI-based design passes, not 5,679;
2. the exact historical 108-row difference cannot be identified from deposited code/config/data;
3. the best workbook semantics—mean of three total-normalized, pseudocount-0.5 UMI ratios—has Spearman `0.985309`, Pearson `0.931179`, MAE `0.143845`, and maximum discrepancy `9.001`, below the prospectively frozen validation requirements;
4. finite historical SNV deltas differ materially (MAE `0.406972`, maximum `9.349905`);
5. exact-only and intended-low-count-filter sensitivities do not resolve the discrepancy and were rejected rather than selected by proximity to 5,679.

## What is established

- The 491 ratio-zero/missing-padj entries are literal source-workbook values, not RNAddress coercion and not genuine measured zero outcomes.
- The 491 pattern is not the same as the paper's implied 587 coverage failures.
- Six exact-sequence duplicate groups existed; historical design-level handling could pseudoreplicate physical measurements if rows were treated independently.
- Raw replicate read and UMI vectors are reconstructable for all 6,260 canonical sequences.
- A deterministic partial cohort contains 3,453 SNVs over 13 parents, but it is not certified for model development.
- Map2 and Cox5b WT parents fail reconstructed UMI coverage and are excluded.
- Historical N-zip-trained/selected analyses are label-exposed; historical TDP outcomes remain independent truth but their models are training-data-exposed.
- Sequence design, source acquisition/checksums, literature review, feature extraction, and protected-data quarantines remain unaffected.

## Operational consequence

Phase 3.5 must **not** resume on this reconstruction. Oracle-identifiability and direction-asymmetry analyses remain blocked. No corrected model training, evaluation, gate, ranking, recommendation, Astrocyte outcome access, or Moffatt archive access occurred in v3.5R.

The partial reconstruction may be used only for provenance debugging and for reconciliation after provenance-complete historical intermediates are obtained. It must not be represented as a PV-CARE-grade validated benchmark.
