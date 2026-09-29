# Reproduction

Protocol commit `1c1f387`; executable prefit freeze `033c316`. The authoritative prefit manifest pins 26 files including executable model, evaluation and gate code, all candidate/replicate tables and the original 246-feature arrays. Later verification, reporting and plotting scripts do not fit/select models or alter thresholds.

Use bundled Python `C:/Users/jaisa/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe` from `D:/rnaexpress`, with PYTHONDONTWRITEBYTECODE=1, PYTHONIOENCODING=utf-8, OPENBLAS_NUM_THREADS=2, OMP_NUM_THREADS=2. Existing local scientific and plotting runtimes are used; nothing was installed or downloaded.

Execution order: prepare, scoped tests, freeze/commit, run (held-parent, cross-replicate, primary whole-study, secondary whole-study), gate, verify, report, figures, package. The completed runner refuses overwrite. Per-fold fit and target files are immutable and can be reused after interruption. Do not rerun preparation/freeze to replace existing evidence.

Git contains deterministic gzip copies of large CSVs. Decompress a missing CSV to its named location and verify the prefit/delivery hash; never regenerate frozen measurements from a different estimator. `candidate_index.csv` joins features to exact interventions; data.npz contains the original float32 features and admitted raw replicate matrix. Fitted mean/scale, coefficient, wedge/noise parameters and source-only variance pools reproduce predictions. Pair orientation is given by left/right candidate IDs. Reverse probability is exactly one minus forward probability. Candidate rankings use latent utility for BT and expected pairwise wins for the declared pairfree/probit variant.

All model evaluation outcomes are exposed development data. The diagnostic role of every table is documented in the protocol. Package contents include derived data, not original protected workbooks, and do not constitute a standalone dependency environment. Historical raw-to-author provenance limitations remain.

Only the namespaced test command `-u -m src.probabilistic_ranking_20260928.test_scoped` is appropriate; never run unfiltered pytest. Verification receipts record both numerical replay and old-file preservation. Any rerun producing timing-bearing logs needs a separate output namespace rather than overwriting a receipt.
