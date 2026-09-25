# SRLE provenance continuation: source leads checked

**Determination remains PARTIAL.** Three additional official source-text blobs were inspected following the separately recorded continuation scope. None establishes the publication's full three-replicate count/statistic/export route. No downloaded script was executed, and no outcomes, normalizations, models or historical gates were changed.

## What the additional source shows

1. **Deleted `analyse_kmer_library.py`.** Recovered from the [known pre-deletion commit](https://github.com/lysovosyl/SRLE-seq/blob/2255946636e755c1551f81c4ce32270ce5616f63/analyse_kmer_library.py). It takes one nuclear and one cytoplasmic paired-read library, counts matching inserts separately in the two mates, filters to six-mers, and applies compartment-specific CPM. Its reported ratio is cytoplasmic/nuclear. Despite importing a t-test, it contains no replicate-level statistical fit; the means in the ratio each operate on a single compartment value. It writes count/ratio CSVs, not the Table 5 workbook. This does not establish which workflow produced the published scores.

2. **Historical `library_split.py`.** The [archived source](https://github.com/lysovosyl/SRLE-seq/blob/620411cae4a236cef8a333a3b117a69fdce97bbd/library_split.py) selects paired reads by primer prefixes using an external `primer.txt` and hard-coded local paths. It is evidence that a splitting helper existed, not proof of the pooling explanation for the ambiguous replicate-3 accessions. The inspected file does not map HRR accession IDs to libraries, provide the required primer manifest, or record a production run. The sample-identity ambiguity remains unresolved.

3. **Earlier `kmer_location_analysis.py`.** The [historical source](https://github.com/lysovosyl/SRLE-seq/blob/620411cae4a236cef8a333a3b117a69fdce97bbd/kmer_location_analysis.py) already contains the duplicated cytoplasmic-field lookup in its `nes` calculation; the defined finite CPM inputs would therefore yield zero in that field. It also uses a shared denominator and a separate raw-count ratio. The argument choices do not include the branch name used for insert-length filtering. These are properties of this exact code version, not evidence that the published Table 5 used it or that the published values are incorrect. It has no three-replicate fit or workbook-export lineage.

All three blobs were obtained without credentials or payment from the same already-admitted official repository. Git blob identities and local SHA-256 hashes were checked. Responses and receipts are under `data/external/research_20260921/srle_provenance_continuation_20260925/`. Only the specified tree metadata and three source-text blobs were retrieved; this was not a new biological dataset search.

## Consequence for the research claim

The bounded predictive finding on the published SRLE landscape and the fixed local replicate calculations remains available, with its existing qualifications. This continuation adds provenance evidence but **does not add biological validation or improve predictive performance**.

The unresolved requirements are still an authoritative sample/primer mapping, the exact three-replicate count matrix, the publication's statistical/normalization specification, and the actual Table 5 export record. An author-supplied archived workflow or equivalent authoritative intermediate could resolve them. The existing [unsent provenance questions](../research_20260921/srle_provenance_questions_20260925.md) already request these records; no message was sent.

The earlier action item to finish provenance from local materials cannot presently be completed. It should not be interpreted as a reason to try formulas until the published table matches. These additional leads close a specific source-history gap, not every possible historical version or unpublished workflow.

The next available step is [metadata-first admission of an independent source](independent_confirmation_admission.md). The new contract does not admit any dataset or authorize outcome access. All prior predictive claims and failed gates remain unchanged.
