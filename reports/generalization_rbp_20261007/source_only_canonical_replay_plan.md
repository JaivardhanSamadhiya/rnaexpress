# Source-only entrypoint for the committed canonical verifier

This additive thin entrypoint preserves the already committed canonical_inner_replay.py, its note and both existing synthetic receipts. It reuses that helper's complete-matrix canonical score calls and independent arithmetic/decision/reselection checks.

NEXT/RBP common.load otherwise reads unused admitted replicate_pairwise_evidence.csv and historical data.npz feature/replicate arrays. These are exposed inputs, not protected outcomes, but replay needs none of them. The new entrypoint reads only the original core's six identity columns, endpoint_class, measured_delta and primary_eligible, using the same project-runtime Pandas default parser. It verifies the immutable target -> generalization_20261007 prefit -> probabilistic_ranking prefit -> original core SHA chain and exact original inventory/row metadata before a temporary process-local loader override. Alignment already has a minimal loader; the same explicit reader retains its endpoint identity check. No frozen source is edited.

Complete target-model receipts and target freeze checks precede any label read. Original default mean-effect parse is preserved; no altered rounding or new outcome is admitted. No historical replicate table/data.npz is loaded. The new final receipt name is canonical_source_only_replay.json, leaving every prior receipt untouched and pinning both helper and entrypoint provenance. Hashing old frozen files during preservation checks is not analysis of their outcome values.

After root confirms complete frozen runs, use bundled Python with one numerical thread:

```text
python -u -m src.generalization_rbp_20261007.source_only_canonical_replay next
python -u -m src.generalization_rbp_20261007.source_only_canonical_replay rbp
python -u -m src.generalization_rbp_20261007.source_only_canonical_replay alignment
```

Preparation/tests use invented temporary inputs only. No project replay, protected outcome, fit, encoder inference, new configuration, changed gate or retrospective checkpoint creation certificate is introduced.
