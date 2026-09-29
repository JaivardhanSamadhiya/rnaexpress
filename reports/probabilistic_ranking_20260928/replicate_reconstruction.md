# Replicate reconstruction and limits

The roster is the previous frozen core: 26,258 candidate measurements, retaining exact parent/context and gene/allele components. Feature rows are the unchanged 246-dimensional `interaction_3` arrays. `candidate_index.csv` maps the new row index to the historical row index and every exact parent/mutant sequence.

`replicate_candidate_measurements.csv` contains 127,603 records: 100,430 finite admitted candidate-minus-WT contrasts and 27,173 missing entries. Missing entries include all four expected slots for each of the 6,749 Moffatt candidates (26,996 records), plus missing astrocyte contrasts. Missingness is explicit and never reconstructed from aggregate estimates. Values are paired localization contrasts, not absolute compartment measurements. The direction-increase value is stored; direction-decrease is its exact negative, not another measurement.

Astrocyte replicate labels are 1–9 and 11–15 from the exposed author-retained pools. Mikl has three source-array slots, SRLE the already reconstructed Rep1/2. No reserved SIRLOIN, N-zip, TDP EV5, Arora, or Shukla measurements are accessed. The raw/author estimator distinctions and partial raw-to-published provenance remain exactly as documented in the prior admission. Technical array slots do not by themselves establish independent biological replication.

The new table includes assay, parent/candidate IDs, replicate ID, QC/provenance, biological grouping, exact sequences and edit coordinates, composition deltas, feature row and feature block. All remaining raw features are in `data.npz`; fold-specific scalers are preserved with models. This is an explicit join, not missing feature information.

The pair roster has 23,563 outcome-independently sampled unordered pairs, of which 23,471 are eligible for the historical non-tie training objective. Exact equality of pair indices, label orientation and hierarchical weights to the original implementation is tested. The 92 aggregate-tie pairs remain in the evidence and calibration tables. No new disagreement filter is applied to the primary soft-label models.

Canonical and feature input hashes, previous-bundle receipts, and unrelated-file hashes are recorded in the preparation and prefit manifests. The 319-member cross-assay archive and 28-member failure-diagnostic supplement were verified unchanged before reconstruction.
