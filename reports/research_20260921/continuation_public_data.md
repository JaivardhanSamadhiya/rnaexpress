# Continued public-data research — 21 September 2026 PDT

AI-authored technical execution record, not a student research report. No money
was spent, no scheduled tasks were created, and no external messages were sent.
All downloads are inside D:/rnaexpress/data/external/research_20260921.

## What was downloaded and verified

1. **SIRLOIN, Lubelsky et al. 2021:** official publisher Table EV2 (11,002 bytes)
   and Dataset EV1 (2,317,579 bytes), plus the authors' NucLibC FASTA (714,636
   bytes). Public, unauthenticated downloads succeeded without payment. Both
   XLSX archives passed CRC checks and contain no VBA or external workbook links.
   See sirloin_public_source_verification.md for hashes and the exact audit.
2. **RNA-context study, Ron and Ulitsky 2022:** official Supplementary Data 1
   (176,176 bytes) and Data 3 (4,732,622 bytes). The publisher identifies the
   article as open access under CC BY 4.0, subject to its stated third-party
   exceptions. Both workbooks passed CRC and active-content checks.
3. **SRLE third-replicate QC:** eight 524,288-byte FASTQ prefixes from the public
   GSA archive. These are deliberately partial files, each with its range and
   SHA-256 recorded; full-file archive MD5 was NOT verified for these prefixes.

Publisher pages and per-file receipts establish where the assets came from;
they do not guarantee that every measurement or source annotation is correct.
Source data were not modified. Downloaded code was not executed. The old access
block is resolved for these downloads under the current enabled network access.

## Independent SIRLOIN test: small improvement, failed gate

All 4,205 published NucLibC sequences matched the authors' FASTA exactly. Extra
FASTA constructs were excluded. There is no exact overlap with the certified old
development sequences. Verified single substitutions: Jpx_9, 162; NICN1_53, 65.

The specification and all source-only predictions were committed in bf7e1eb
before reading localization outcomes. Candidates were grouped by parent and
base-substitution type, so composition and edit cost are identical within a
decision. Only replicate 1 and 2 outcomes were read. Twelve Jpx classes and eight
NICN1 classes met the minimum-five-candidate rule. Both high and low localization
choices were evaluated, with fixed lexical ties and no target-data fitting.

| Score | Mean normalized regret (lower is better) |
| --- | ---: |
| Composition/lexical baseline | 0.5000 |
| CCC count | 0.5252 |
| CCTCCC count | 0.4909 |
| Primary SRLE 1–3-mer model | 0.4473 |
| Secondary SRLE pair model | 0.4765 |
| Secondary measured SRLE six-mer scores | 0.4759 |

The primary model improved regret by 0.07788 over CCC and 0.04360 over CCTCCC.
Advantages were positive separately in both parents and both replicates, but
the predeclared requirement was >=0.05 over EACH baseline. Thus **discovery_pass
= false**. The threshold was not lowered. Replicates 3/4 and NucLibB outcomes
remain reserved. Two parent contexts also cannot support population-wide
generalization or independent biological significance claims. This is more
encouraging than the failed neuronal transfer but is not confirmation success.

## SRLE provenance finding

The first 1,000 read sequences AND read identifiers were identical for each of
these differently labeled GSA records, separately for both sequencing mates:

- HRR3059162 (6mer_Cyto_Sample3) and HRR3059175 (MALAT1_Cyto_Sample3).
- HRR3059165 (6mer_Nuc_Sample3) and HRR3059176 (MALAT1_Nuc_Sample3).

Identical inspected prefixes are established by saved sequence/header hashes.
This does not prove full-file identity, erroneous experiments or misconduct.
Shared pooled sequencing could explain it. The read samples include both six-base
inserts and longer inserts. Clarify pooling/demultiplexing and sample identity
before counting these labeled records as separate experimental evidence. The
previous complete, checksum-verified replicate-1/2 reconstruction stands.

## Broader dataset ready for a separately specified test

The 2022 workbook has 8,162 metadata rows, 8,158 valid unique DNA sequences and
133 gene labels; 91 gene labels contain >=20 valid rows. Counts are metadata
inventory, not counts of independent biological units or evaluable outcomes.
There are 5,510 valid 109-nt and 2,648 valid 141-nt sequences. Four rows have
invalid/missing sequences and require exclusion; missing labels also require QC.
No exact sequence overlaps the certified historical table; 43 match the SIRLOIN
metadata and need exclusion/grouping. Gene names and homologous fragments require
additional grouping checks. Only the first six metadata columns and header were
examined; localization, expression, perturbation and stability values remain
unexamined. The paper's qualitative results are known and must be acknowledged.

The appropriate next question is whether a small, predeclared amount of target-
context calibration improves gene-held-out selection beyond simple target-only
sequence models. This is distinct from repeatedly trying uncalibrated transfer.
Before scoring, define its purpose, finite calibration budget, sequence-family
split, strong baselines, exclusion rules and a failure threshold. Because these
are tiled fragments, success would support fragment/context selection rather
than direct validation of minimal edits. Context dependence itself is prior art.

## Preservation and interpretation

All original pilot files and follow-up freezes remain unchanged. Historical
Astrocyte, N-zip and TDP stability seals remain intact, as do user edits and old
NO-GO verdicts. New source-only prediction and column-access tests pass. No
unfiltered pytest was used. This continuation is a research advance and source
verification record, not a claim that complete novelty or an STS result has
been achieved. All AI assistance must be attributed; scientific interpretation
and submitted writing remain the student's responsibility.

Primary sources: [2021 SIRLOIN publisher page](https://link.springer.com/article/10.15252/embj.2020106357),
[2022 context study and license](https://link.springer.com/article/10.1038/s41467-022-30183-0),
[GSA SRLE study](https://ngdc.cncb.ac.cn/gsa-human/browse/HRA016642).
