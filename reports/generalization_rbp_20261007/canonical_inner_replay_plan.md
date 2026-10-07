# Additive canonical-shape replay review

Prepared 7 October 2026 after the RBP production freeze. This adds a verifier; it changes no frozen production source, model, selected configuration, label, feature matrix, gate or existing replay receipt.

The previous additive inner replay uses 1,024-row predictor calls and returns a block dot product after a 1e-9 parity bound. The original nested engines score a complete validation matrix. A tolerated numerical difference can split an exact score tie, and BLAS shape or summation order need not preserve exact values. This is a verification risk, not evidence that fitted rankings or biological conclusions are wrong.

The new helper imports the original research runtime bootstrap before NumPy/Pandas, matching engine library resolution rather than importing numerical packages before the project runtime path is inserted. Its receipt reports the loaded numerical library paths/versions and bootstrap SHA. It calls the declared original predictor once per complete validation/target matrix, using its original advanced-indexed float64 values and one numerical thread. Only independent coefficient-sum arithmetic is blocked. It bounds the independent formula against canonical scores within 1e-9, then uses canonical values for separately implemented lexical max/min choices and original-truth regret. No epsilon score-tie rule is added. For alignment, the independent formula applies only the already fixed metadata endpoint sign, and original/aligned training-label identities are checked.

Modes next, rbp and alignment reconstruct original component and allele purges; bind every training-ID order/configuration/source set; replay every inner source-only regret and complete penalty means; retain the declared 1e-12 fixed-order penalty tie rule; and verify all outer canonical scores, lexical decisions, feasibility/error classes and component identities against saved outputs. NEXT/alignment each require216 inner+24 outer checkpoints; RBP requires108+12. A distinct canonical_inner_replay.json receipt is written in the target namespace. Existing receipts are preserved.

The helper is additive and may not be a member of the earlier target prefit manifest; its receipt explicitly reports this fact and pins its own source, imported legacy helper and all inspected checkpoint/output bytes. It does not retroactively certify the old checkpoints' creation-time label/feature/model bytes. Earlier freeze provenance limits remain.

Memory retains one feature matrix and one full validation matrix plus1,024-row independent arithmetic buffers. Reproducing the exact full validation shape deliberately costs a bounded temporary float64 allocation. No pretrained encoder, estimator or fit routine is invoked. Synthetic tests use artificial matrices, mocked scorers and tiny invented labels only.

After root confirms each namespace's complete frozen model runs, invoke bundled Python with PYTHONDONTWRITEBYTECODE=1, PYTHONUTF8=1, OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=1:

```text
python -u -m src.generalization_rbp_20261007.canonical_inner_replay next
python -u -m src.generalization_rbp_20261007.canonical_inner_replay rbp
python -u -m src.generalization_rbp_20261007.canonical_inner_replay alignment
```

No project replay, project-label analysis or fitting is authorized merely by writing or testing this helper. N-zip, TDP EV5/stability, SRLE Rep3 and every reserved/unadmitted outcome remain excluded.
