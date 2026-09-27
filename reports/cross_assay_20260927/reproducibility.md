# Reproduction and preservation

The pre-comparison freeze is commit `d6a0623`. It pins 36 files, including the canonical roster, features, exact model/gate implementation, configuration, admissions and prior numerical replay. All outcomes are explicitly development-exposed. The freeze cannot convert them into independent confirmation.

Bundled runtime, from `D:/rnaexpress`:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
$env:OPENBLAS_NUM_THREADS='2'
$env:OMP_NUM_THREADS='2'
& 'C:\Users\jaisa\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -u -m src.cross_assay_20260927.test_scoped
```

Only scoped tests are safe; never run unfiltered pytest. Existing scientific dependencies are loaded by the repository's research runtime. No package download or paid compute was used. All computations run locally; no scheduled task was created.

Original execution order: `dataset`, `features`, `prepare`, synthetic tests, `freeze`, commit, `run`, `gate`, descriptive `diagnostics`, numerical `verify`, `report`, `figures`, and evidence `package`. Feature extraction and protocol/model choices precede new results. Fit checkpoints in `results/cross_assay_20260927/fits/` are immutable: the runner can reuse exact recorded fits after interruption, but a completed run refuses replacement. `run_complete.json` identifies completion. Never rerun preparation/freeze or mutate old namespaces to force a new result.

The CSV roster includes exact sequences and all admitted small-edit inventory rows; primary training flags identify the core cohort. Large requested CSV files remain local and have deterministic gzip copies in Git. Raw feature NPZ and frozen-pretrained NPZ remain local, hash-pinned and included in the evidence archive. Reconstruct normalized features using each fit's training-only mean/scale. Predictions reference canonical `intervention_id` and `fold_id`; no long-sequence duplication is required for full audit.

To reproduce scores, join `model_row_index.csv` to the canonical table, use the named feature block, apply saved mean/scale and universal coefficients, and add a residual only when the task permits a known training-study head. Whole-study, domain and family tests always have zero held-study residual. Direction-head probabilities are separate from rank scores. Feasibility models and their fixed 0.8 acceptance policy are also retained. Decision ties use exact lexical IDs, not input row order.

`verify.py` independently replays every core score and selected decision, reruns eight source-only baseline/kmer fits, checks exact frozen-pretrained source-ID vectors, rehashes historical bundles and compares all preexisting modified tracked files against the initial state. Its receipts and timing-bearing logs are immutable; rerun verification into a separate output namespace when a new receipt is needed. Do not overwrite recorded logs solely because a runtime duration differs.

`supplementary_audit.py` separately checks unique candidate sequences, independently recomputes all 48 core study/model macro regrets, and decompresses all five large gzip tables to verify exact equality with their requested CSV originals. This check has its own execution-code hash and receipt. It covers additional aggregation assertions added to the verifier source after its long-running process had started; the earlier process is not claimed to have executed a later source edit.

`verify_vectorized.py` provides an alternative implementation of recommendation selection and regret/direction checks using grouped arrays instead of the slower per-decision loop. Its trial printed successful completion of all 44 core study/model blocks, including eight fresh fits. The original verifier completed first with PASS, so the redundant alternative was stopped during its remaining repeated provenance checks. No complete alternative PASS receipt is claimed. The completed original audit and supplementary audit are authoritative; this optimization changes no model, candidate roster, metric definition or gate.

Report/diagnostic/figure scripts only transform saved predictions and fixed prespecified strata; they do not refit or retune models. They are separate from the frozen model-selection implementation. Seven figures cover source breadth, edit size, evaluation difficulty, all held-study results, failures/abstention, feature heterogeneity, source residuals, endpoint classes and frozen-pretrained performance. Figures use the existing plotting runtime and have PNG and SVG exports. Contact-sheet visual inspection checks labels and layout.

The evidence archive contains derived outcomes, models, features, reports and figures, not original supplementary workbooks or protected unrelated datasets. Full raw-source reconstruction requires the existing certified source bundle and its pinned manifests. This is not a standalone Python environment and does not certify complete raw-to-published-estimator reproduction for every assay. Source-specific measurement caveats remain in admission and final status reports.

No new independent-dataset metadata search is allowed unless `gate_verdict.json` explicitly permits it. A failed gate ends this branch; a new hypothesis needs a separate protocol, never an edited threshold in this one.
