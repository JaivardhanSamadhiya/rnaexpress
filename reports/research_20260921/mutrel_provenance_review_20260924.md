# mutREL counting-semantics review, 24 September 2026

AI-authored additive provenance record. This review opens no new localization
measurements, expands no raw sequencing files, fits no model and changes no prior
admission verdict. No contact with authors, spending or scheduled task occurred.

**Conclusion: unresolved; keep the processed rows unadmitted for isolated-mutation
intervention scoring.** No inspected source explicitly says that molecules with
more than one mutation were discarded. Neither does it explicitly establish
marginal counting of every mutation in multiply-mutated molecules. Absence of a
filter description is not evidence that the filter was absent.

Evidence and its limits:

- The publisher's Extended Data Fig. 1b describes error-prone PCR followed by
  reporter insertion. Fig. 1g labels its inventory as "mutation or deletion
  events expected and identified". These descriptions establish random
  mutagenesis and event-level reporting, not the molecular inclusion rule.
  [Primary paper](https://doi.org/10.1038/s41586-020-2105-3).
- The cached file named `mutrel_methods.pdf` is actually *Supplementary Notes
  and Discussions*. Note 1 discusses the increased resolution of mutREL-seq;
  Note 2 interprets selected positions. Neither supplies a rule for discarding
  multiply-mutated molecules. Relevant PDF pages are 2, 7 and 8.
- The official GEO sample processing field describes generic Bowtie/TopHat
  mapping, region-count calculations and a table of counts for different
  mutations. It does not specify read-level mutation cardinality or treatment
  of reads with multiple events.
  [GSM2861600](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM2861600).
- The cached publisher page contains no code-availability section or links to
  a GitHub, GitLab, Zenodo, Figshare or Code Ocean repository. This bounded review
  did not establish that no public implementation exists.

The existing metadata inventory contains 401 substitution entries, 96 deletion
entries and a WT row. The previously recorded internal-position subset has 374
substitution and 85 deletion entries. Those row counts describe events, and do
not determine whether all contributing molecules differed from WT at only one
site. The existing partial-read QC already establishes co-occurring substitutions
in some sampled molecules; it does not establish how the authors filtered or
counted those molecules. Both earlier observations are preserved.

Access limitation: the cached publisher HTML lacks the full Methods text. The
exact named article was opened at PMC12018070, but subsequent method retrieval
returned a browser-verification page. The official Europe PMC fullTextXML endpoint
returned HTTP 500. These failures are not evidence about the biological analysis.
No broad literature search or unrelated repository search was performed.

Admission requires an explicit authoritative counting rule or an auditable
implementation that connects full-read mutation calls to the processed event
rows. Barcode-to-compartment correspondence also remains unresolved. Until then,
the table cannot be represented as measured outcomes for clean single-mutant
constructs. It remains useful as primary-paper context and provenance material.

Local sources reviewed: `mutrel_publisher_html`, `mutrel_methods.pdf`,
`mutrel_geo`, `mutrel_sample_metadata`, prior checkpoint records and
`mutrel_admission_20260923.json`. No numeric compartment-count columns were read.
