# Reproduction and preservation

The new namespace is `generalization_20260926` under `src`, `reports`, `results` and `artifacts`. Frozen history stays in its original namespaces. No dependency installation or spending was needed. Public official source files were reused locally after SHA-256 checks. The source manifest records local reuse rather than inventing a new download date.

## Recorded execution order

1. Outcome-free `metadata` and `source_predict`, then 12 scoped synthetic tests.
2. `freeze` hashed 37 inputs/implementations/protocols, including source-only predictions. Commit `0b100d3`.
3. The separate prefit marker was committed at `5ae6d4a`. Both precede recorded outcome access. The JSON UTC timestamp is authoritative; see the marker's timezone erratum in `execution_notes.md`.
4. `reveal` selected only exact sequence design and the specified localization/CPM fields, validated mappings, and retained every QC status.
5. `test_a` evaluated the precomputed predictions once; its failure and all results were committed at `1ff9bc2` before B.
6. Conditional `test_b` used the already-committed model family/fold rules. `cross_assay` generated the prespecified descriptive diagnostics.
7. `verify` independently reconstructed source features/predictions, refit 84 outer models at their recorded training-only selected alphas, rechecked all parent metrics and candidate decisions, and preserved historical bundles. No scientific model selection or endpoint revision was repeated.
8. `report`, `figures`, and `package` produced the final deliverables exclusively from saved results.

## Safe scoped command

Use the bundled runtime from the repository root:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
$env:OPENBLAS_NUM_THREADS='2'
$env:OMP_NUM_THREADS='2'
& 'C:\Users\jaisa\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -u -m src.generalization_20260926.test_prefit
```

Do not run unfiltered pytest. Do not rerun `reveal`, `test_a`, `test_b` or `freeze` over existing outputs: their guards deliberately preserve the recorded scientific history. Exact verification calculations are in `verify.py`; the existing receipt contains the completed check. Its timing-bearing test log is also immutable, so a fresh verification should redirect new receipt/log outputs to a separate namespace rather than overwrite them. Figure rendering is reproducible from the committed script and saved tables, using the already-installed local plot runtime.

The original raw workbook/archive are not duplicated into this delivery ZIP. Full replay requires the repository inputs pinned in the prefit manifest and the local scientific dependencies loaded through `src.research_20260921.common`. This is an evidence bundle, not a self-contained runtime. Reproducing an original once-run analysis from scratch requires a separate checkout/output root that preserves all freeze guards and does not replace this record.

## Verified invariants

- All 37 prefit hashes unchanged; 4,553 source prediction rows regenerated from independently counted overlapping words.
- 84 fresh outer model fits reproduced predictions with maximum absolute error 0.0.
- 154 parent/model metrics and 308 deterministic selections reproduced independently; both primary interval/sign-flip calculations checked.
- Twelve scoped tests pass, including overlap purging, parent balance, and outer-label invariance of inner alpha selection.
- Original synthesis/small-edit/SRLE prediction receipts retain all 119/70/41 members and archive hashes.
- All 3,984 eligible SNPs are represented; no new outcome-based exclusions. Seven parent groups, five nonoverlap components, two genes remain explicit.
- The 33 preexisting modified tracked files and five unrelated untracked files were not staged or edited by this work.

Source-to-author-REML reproduction is explicitly incomplete: paired CPM contrasts corroborate the chosen endpoint but do not exactly reconstruct the complete author pipeline. Known biological dependence within genes and shared experimental pools limits the component-bootstrap interpretation.

See `artifacts/generalization_20260926/delivery_receipt.json` for archive size, member hashes and verification. The final bundle includes the eight requested reports, complete prediction/ranking files, ledger, configurations, fit records and reproducible figure scripts.
