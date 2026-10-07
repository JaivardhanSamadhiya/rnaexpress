# Execution readiness

Preparation completed before biological fitting. Both tracks use one identical matrix with 26,258 rows and 247 columns; only 246 columns are fitted. The last column is a fixed biological endpoint sign. No rows or labels were added or removed, and original sequences remain the purge identities.

- Shared matrix SHA-256: `d858b9c437e489eb16099b771dac5a2e148ce7a99ca8018c6a9aa6338c60ee31`.
- Corrected base SHA-256: `cf7d79d6b1a0efa3228fbcbe8c61b0e712c2fb630f9c1ef9302dcf83f152693c`.
- Original ordered row-ID SHA-256: `f04a8fe31976c913c1167c1b51f21d6c556928c63c2c334377d3cf2e897b187a`.
- Eight scoped synthetic tests passed. Only synthetic optimizations ran; no biological fitting started.
- Root and an independent methods reviewer found no blocking issue in the fixed orientation, original-truth inner selection, pair-support matching or replay verification.
- Both tracks have 40 checkpoints, 80 total, using one numerical thread. Outer results cannot choose signs, settings or revised criteria.

The manifest is created by `-m src.generalization_polarity_20261007.freeze` and must be committed before either `engine unflipped` or `engine polarity` runs. Set `PYTHONDONTWRITEBYTECODE=1`, `PYTHONIOENCODING=utf-8`, `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1` and `MKL_NUM_THREADS=1` when using bundled Codex Python. Once both tracks complete, run the namespace's `gate` and `verify` modules. Completed outputs are immutable; interrupted fits resume only when training-ID/configuration/prefit hashes match.

The strict four-source gate remains unchanged, with the additional prespecified polarity-versus-unflipped incremental requirement. This is repeatedly exposed development evidence. Known endpoint is confounded with source, and nuclear-score inversion does not establish export as distal transport.
