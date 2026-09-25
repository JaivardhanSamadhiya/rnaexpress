# Reproduction and preservation

The study protocol and original seven Python files were frozen in Git commit **6e793d7** before fitting. The complete prior evidence synthesis is commit **117fb27**. This study is additive; it does not replace that evidence or any failed gate.

Frozen configuration SHA-256:
`8da1ff9df206945f041a3a9fdffd77900c8cb6ce682f2a2273dc3cc73c291ccc`

Primary prediction CSV SHA-256:
`82d9b73b02a8e8ed8b8c07f9360011d3fe30d3c77960a9c8d3b8f0dc9195a07f`

## Environment

Use the bundled interpreter, not PATH Python. The repository helper loads its existing isolated numpy/pandas/scipy/scikit-learn dependencies. Plotting uses the existing plot runtime. No dependency installation, network call, or paid service is needed for replay in this workspace.

```powershell
Set-Location D:\rnaexpress
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
$env:OPENBLAS_NUM_THREADS='2'
$env:OMP_NUM_THREADS='2'
& 'C:\Users\jaisa\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -u -m src.small_edit_20260925.verify
```

The verified run passed **76 scoped tests**, replayed all **19,438** primary predictions/probabilities from saved coefficients with **zero maximum difference**, and independently replayed selected candidates/regrets with **zero maximum difference**. No genes, parent IDs, parent sequences, mutant sequences, or exact alleles crossed biological folds. All **16 research freeze manifests** and the **228-file tracked-source snapshot** remained unchanged. The test target imports only the explicitly scoped research and new small-edit tests. Do not run unfiltered pytest.

`verify` performs no fitting and opens only the admitted inputs already pinned in the inventory/freeze. Its first-run receipt and test log are immutable. A repeated run may finish the checks and then refuse to overwrite a test log whose elapsed-time text differs; that refusal is expected preservation behavior, not a reason to delete an existing receipt. For a separate replay, use a separate copied analysis workspace/output namespace and preserve the original files.

## Recorded execution sequence

The original sequence was inventory, scope/protocol creation, synthetic tests, freeze and pre-fit commit, then `predict`, `evaluate`, `secondary`, `sufficiency`, `secondary_intervals`, `figures`, `verify`, `report`. `predict` is the only new training step. It ran once. The secondary analyses use existing frozen predictions. Do not rerun `freeze`, alter its code hashes, or retrain in this evaluation workspace to seek a different result.

The saved coefficient file contains each training-fold scaler, regression/classification coefficients and intercepts. `inner_model_selection.csv` preserves every alpha/family score. `prediction_receipt.json` pins these outputs; `verification_receipt.json` records their replay. Full predictions and candidate rankings remain plain CSVs in the local results directory; the inventory is gzip CSV. The seven figures have both PNG and SVG copies.

## Delivery archive

`artifacts/small_edit_20260925/small_edit_evidence_20260925.zip` contains all new source, reports, scores, inventory, coefficients, receipts and figures, with an internal SHA-256 manifest. The external `delivery_receipt.json` pins the archive hash. Large derived outputs remain local and in this archive rather than being added to ordinary Git history; compact reports, code and result summaries are tracked.

This is an evidence bundle, **not a self-contained training environment or redistribution of all original raw data**. Clean replay requires this repository's existing research helpers and the admitted input files with the hashes in `inventory_receipt.json`, plus the documented runtime. The archive's prediction CSVs and result tables can be inspected without fitting or opening protected data. Original raw datasets, sealed outcomes, large old model caches and unrelated user files are not included.

The archive has no new scientific independence: it preserves the same experiment and analysis. Source discovery was not retried after its prior automatic approval rejection.
