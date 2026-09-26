# Reproducing the SRLE predictive study

The pre-fit commit is **0023b01**. The frozen protocol and source hashes are in `results/srle_prediction_20260926/evaluation_freeze.json` (SHA-256 `c2fd8b29803779b8be3189eda36f941cc6bde9638b27d4b48ff8fc0f70ef3ba9`). All three evaluation schemes, seven named models, cohort, candidate roster and figure-example rules were fixed before new model fitting or aggregate scoring.

Run from `D:\rnaexpress` with the bundled interpreter and existing isolated dependencies:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
$env:OPENBLAS_NUM_THREADS='2'
$env:OMP_NUM_THREADS='2'
& 'C:\Users\jaisa\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -u -m src.srle_prediction_20260926.verify
```

The recorded verification replayed 17,955 sequence/model/scheme predictions and 24,864 deterministic candidate decisions, with zero prediction/regret differences. Independently calculated metric differences were <=8.9e-16; 82 scoped tests passed. The verification performs no fitting. It uses the existing research helpers and checks preservation of earlier evidence. Do not run unfiltered repository pytest.

Existing output files are immutable. Re-running verification can reach its save step and refuse to replace a test log whose elapsed-time text differs; this is not permission to remove an old receipt. Use a separate copied workspace/output directory for a separately recorded reproduction. The original receipts record the successful completed run.

The recorded analysis sequence was: `inventory`; six new synthetic tests; protocol/source freeze and commit; `fit`; `evaluate`; `verify`; `figure`; `report`; and `package`. The fit step used 141 training partitions (one original split and two schemes with 70 held-group partitions), with fixed alpha=10 and no tuning. The saved coefficients contain the training composition means, unseen-composition fallback and all order-model scalers/parameters. The 1-mer residual is an analytic identity, not a fitted extra order effect.

Do not rerun `freeze`, alter groups, change the similarity radius, choose another alpha, or promote a new primary model after seeing the target results. The historical scores and candidate decisions are unchanged. All reported differences can be recomputed from saved predictions without fitting.

## Bundle contents and limits

`artifacts/small_edit_20260925/srle_prediction_evidence_20260926.zip` contains the new scripts, four SRLE reports, inventories, split masks/geometry, saved coefficients, complete predictions and candidate rankings, metric tables, diagnostics, verification receipts and PNG/SVG figure. An internal manifest pins every member; the external `srle_prediction_delivery_receipt.json` records the archive SHA-256 and byte size. The original small-edit evidence ZIP remains unchanged.

This is an evidence bundle, not a self-contained copy of the old repository and runtime. Some verification helpers and historical source artifacts are referenced by pinned hashes rather than redistributed. No raw FASTQ, protected outcome, new dataset or unmeasured sequence design is included. The full CSVs and fitted-parameter caches remain local/in the bundle; compact reports, figures, metrics and hashes are committed. Save the ZIP as well as the Git repository when transferring the project.

T in the stored six-mer identifiers follows the existing U-to-T sequence encoding. These are measured local insert identifiers; full reporter/physical clone sequences are not reconstructed. Source units and exposure limitations are described in the [results](srle_small_edit_prediction_results.md) and [final claim](srle_final_predictive_claim.md).
