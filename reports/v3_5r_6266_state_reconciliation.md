# RNAddress v3.5R reconciliation of all 6,266 N-zip constructs

Every design row is represented in `results/v3_5r/nzip_6266_outcome_state_reconciliation.csv.gz`. States sum exactly to 6,266.

| State | Rows | Meaning |
|---|---:|---|
| `measured_valid` | 5,383 | Reconstructed UMI coverage passes, source-defined ratio is finite, and identity is not quarantined. |
| `coverage_filtered` | 473 | Fewer than three samples contain at least 20 distinct mapped UMIs. |
| `sequence_ambiguous` | 404 | Cflar_2 design/outcome identity cannot be assigned safely between source tiles 107 and 52. |
| `duplicate_sequence_collapsed` | 6 | Secondary design IDs share an exact physical sequence measurement with another design row. |

The coverage total itself is 5,787 pass and 479 fail before Cflar quarantine and duplicate-state presentation. The 404/6 state precedence is representational: every duplicate group has exactly one collapsed secondary design ID, while its canonical measurement remains single.

## The 491-versus-587 discrepancy

The source XLSX stores 491 literal numeric `0` values in `Mean_log2ratio_NeuriteSoma_WT`, each paired with missing `Mean_padj_NeuriteSoma_WT`. These are not blank cells, formulas, or zeros created by RNAddress.

Cross-tabulation against reconstructed UMI coverage is:

| Workbook state | Reconstructed coverage fail | Reconstructed coverage pass | Total |
|---|---:|---:|---:|
| zero ratio + missing padj | 443 | 48 | 491 |
| not zero/missing-padj | 36 | 5,739 | 5,775 |
| **Total** | **479** | **5,787** | **6,266** |

Therefore the 491 rows are a source workbook/export-processing sentinel pattern, not the publication's 587-row coverage-failure set. The public historical materials do not identify the additional/different historical failures: reconstructed UMI coverage fails 479 rows, while the paper implies 587. The aggregate gap is 108 rows, and exact identities cannot be recovered without tuning or an author-supplied historical intermediate.

## Zero semantics

Classification: **mixed source-processing and supplement-export sentinel**, already present in the supplement. The pinned public R script contains a low-count indexing statement with no assignment, while DESeq2 independent filtering can produce missing adjusted P values. The public artifacts do not reveal the exact transformation that wrote zero into the ratio cells. The zeros are not genuine measured localization values and cannot be used in deltas.
