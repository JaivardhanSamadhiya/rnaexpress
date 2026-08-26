# RNAddress Project Log

All timestamps use ISO 8601 with the local offset where available. Entries are labeled **PRE-SPECIFIED** or **POST-HOC**.

## 2026-08-26 — Project initialization — PRE-SPECIFIED

- Initialized the repository from the uploaded master specification.
- Preserved the required order: novelty and physical data audit before modeling.
- Central gate: reconstruct experimental `(parent, edit, mutant, parent outcome, mutant outcome)` tuples in at least N-zip and astrocyte SN-MPRA.
- No model was developed or fit.

## 2026-08-26 — Public data acquisition — PRE-SPECIFIED

- Acquired GSE173098 processed counts and the complete Mikl supplementary archive.
- Acquired all N-zip supplementary workbooks plus BioStudies metadata for E-MTAB-10902, E-MTAB-11572, and E-MTAB-11575.
- Acquired the GSE330741 processed-count archive, complete astrocyte supplementary workbook, and public analysis repository.
- Acquired the SRLE-seq supplementary archive, source repository, and HRA016642 public raw-file checksum list. The raw HRA archive is approximately tens of gigabytes and was not required for the first processed-data gate.
- Acquired the Arora/Taliaferro supplementary archive and identified GSE183192.

## 2026-08-26 — N-zip intervention discovery — PRE-SPECIFIED

- Source workbook contains 4,813 initial-library tiles after excluding its embedded header row.
- Mutagenesis table contains 6,266 constructs: 20 WT, 4,695 single-nucleotide substitutions, 783 2-nt windows, 313 5-nt windows, 179 10-nt windows, 106 deletions, 102 targeted mutations, and 68 scrambles.
- Sixteen WT parents have exhaustive single-nucleotide coverage. Their total assayed length is 1,565 nt, exactly matching `1,565 × 3 = 4,695` substitutions.
- All 6,266 mutagenesis constructs have a WT primary-neuron neurite/soma localization value in the source table.

## 2026-08-26 — External-outcome quarantine deviation — POST-HOC

- During workbook schema discovery, the first three rows of the astrocyte result sheet were printed before the external manifest was written. This exposed a few individual numeric result cells but no aggregate outcome distribution, ranking, threshold analysis, or model result.
- Mitigation: those values are prohibited from informing target thresholds, feature design, model selection, or evaluation policy. The complete source workbook is now hash-frozen, and subsequent pre-freeze inspection is limited to schema, sequence/edit identity, row counts, and missingness counts.
- This deviation must remain visible in the final report; the external evaluation can be outcome-blinded from this point forward but cannot be described as perfectly never-seen.

## 2026-08-26 — Novelty collision findings — PRE-SPECIFIED

- CRISPR-TO and PULR directly provide programmable RNA repositioning, but through trans-acting RNA-binding/motor systems rather than minimal cis-sequence rewriting.
- Saturation and random-mutagenesis assays (N-zip, mutREL-seq, Mikl, astrocyte SN-MPRA) experimentally identify causal localization nucleotides, but do not accept a requested destination and computationally select minimal edits on held-out parents.
- Nuclear-speckle work experimentally designs motif/splice-site combinations and is a serious sequence-engineering collision, but is not a general minimal-edit inverse framework benchmarked on held-out intervention landscapes.
- No comparable system found so far performs starting RNA + requested localization + protected properties → minimal edit, then evaluates ranked recommendations on independent exhaustive mutagenesis landscapes.

## 2026-08-26 — N-zip identity ambiguity correction — POST-HOC

- The mutagenesis outcome sheet omits the source tile identifier and contains two distinct `Cflar_2` parents under the same gene-level identity. Row-order assignment would recover all 4,695 designed SNVs but is not independently verifiable from the workbook.
- The central benchmark therefore excludes the duplicated identity entirely. Its truth-safe benchmark contains 4,395 exhaustive SNVs across 15 unambiguous parents (1,465 positions, three alternate alleles each); 300 SNVs are quarantined.
- This correction supersedes any implication above that all 16 design parents are safely usable as outcome-linked intervention tuples.
