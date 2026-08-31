# RNAddress v3.5R raw N-zip processing audit

## Scope and decision

The six untreated mutagenized N-zip FASTQs (`ERR7337821`–`ERR7337826`) were reconstructed from deposited raw reads. All source files passed expected-byte, ENA MD5, local SHA-256, gzip-integrity, and FASTQ-record-count validation. The source-equivalent counter was validated against the pinned authors' JAR with exact per-sequence read and UMI agreement on a frozen 100,000-read slice.

The raw reconstruction is complete and deterministic, but it does **not** reproduce the publication's aggregate coverage result or a material subset of finite published outcomes. This triggers the frozen protocol's STOP thresholds.

## Sample mapping and totals

| Run | Compartment / replicate | FASTQ reads | Unique permissive mappings | Distinct UMIs |
|---|---|---:|---:|---:|
| ERR7337821 | neurite 1 | 31,033,728 | 11,071,269 | 2,242,213 |
| ERR7337822 | neurite 2 | 21,444,343 | 7,505,916 | 1,083,302 |
| ERR7337823 | neurite 3 | 28,271,727 | 9,936,201 | 1,868,559 |
| ERR7337824 | soma 1 | 31,333,875 | 11,026,447 | 3,712,001 |
| ERR7337825 | soma 2 | 24,605,069 | 9,046,370 | 3,258,717 |
| ERR7337826 | soma 3 | 28,143,744 | 10,160,341 | 3,428,272 |
| **Total** | | **164,832,486** | **58,746,544** | **15,593,064** |

Mean permissive mappings were 9,791,091 per sample; mean distinct UMIs were 2,598,844. The publication reports approximately 1.9 million mapped reads per mutagenized sample. Distinct-UMI scale is closer, particularly in neurites, but the residual sample-dependent difference is not explained by public configuration.

## Frozen matching behavior

The pinned bytecode and concordance run establish the following behavior: first adapter placement with at most two substitutions; pre-adapter UMI extraction; skip UMIs containing `N`; source sliding-5-mer candidate seeding for truncated payloads; positional, indel-free matching; at most two substitutions in the first 15 nt and at most four total; unique minimum-distance exact-sequence identity; reject best-distance ties across distinct sequences.

Six duplicated design-sequence groups were collapsed to one physical sequence measurement. The full library contains 6,266 design rows but 6,260 canonical sequences.

## Coverage reconciliation

The workbook's quantitative field independently matches distinct-UMI simple ratios best, so the primary reconstructed coverage layer applies the paper's at-least-20/in-at-least-three-samples rule to distinct UMIs:

| Layer | Canonical pass | Design-level pass | Difference from 5,679 |
|---|---:|---:|---:|
| Source-equivalent distinct UMI | 5,782 | 5,787 | +108 |
| Source-equivalent permissive read sensitivity | 5,929 | 5,934 | +255 |
| Exact-only UMI rejected sensitivity | 5,666 | 5,670 | −9 |

The exact-only sensitivity was rejected because it worsened outcome agreement and was not the pinned authors' operational rule. The threshold was not altered to force 5,679. The identities of the historical 108-row aggregate difference are therefore unresolved.

## Rejected explanations

- Exact-only matching: numerically close to 5,679 but scientifically unsupported and globally worse.
- Read counts as the quantitative layer: poorer agreement with the workbook.
- Ratio of averaged CPMs, DESeq2 fold change, and median replicate ratio: poorer agreement than mean UMI replicate ratios.
- Applying the intended assignment behind the apparent no-assignment low-count line in `processTwist.R`: poorer agreement and no Msn resolution.
- Duplicate design rows: explain only six design rows and cannot account for the 108-row difference.

Machine-readable evidence is in `results/v3_5r/raw_count_audit.json`, `results/v3_5r/source_acquisition_manifest.json`, `results/v3_5r/author_independent_slice_concordance.json`, and `results/v3_5r/localization_ratio_semantics_audit.json`.
