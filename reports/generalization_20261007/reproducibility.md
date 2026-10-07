# Reproduce and preserve

Prefit commit `53553f2` pins 45 unique files, exact four-assay rows and five route definitions. Use bundled Codex Python from the project root with PYTHONDONTWRITEBYTECODE=1, PYTHONIOENCODING=utf-8 and OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=2. Scientific dependencies are the existing isolated Mechanism-v2 runtime.

Commands: `-u -m src.generalization_20261007.tests`; original prefit preparation/freeze is already completed and must not replace old files. Each track was run once through `-u -m src.generalization_20261007.engine <track>` (scaling, representation, mechanism, coverage, endpoint), then gate, verify, report and package. Completed tracks refuse another run; saved fold models permit an interrupted run to resume without refitting differing coefficients. No unfiltered pytest.

The source-only inner scores select each outer configuration. All model JSONs include exact coefficient/scaling values, row hashes and the training study/component inventory; endpoint models additionally include auxiliary purge ledgers. Predictions and decision metrics are deterministic gzip/CSV artifacts. Saved feature NPZs and row index reproduce input joins; the prior immutable archives supply canonical data provenance. The archive is not a standalone Python environment or a replacement for original protected data. Old plots/verdicts and user edits remain unchanged.
