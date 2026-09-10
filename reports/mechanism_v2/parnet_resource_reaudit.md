# Parnet 0.3.0 resource re-audit

Status: bounded fresh audit completed, 9 September 2026.
**No paper-matching checkpoint recovered or admitted to this experiment.**

The [Nature Cell Biology paper published 9 September 2026](https://doi.org/10.1038/s41556-026-02040-5)
names release 0.3.0 and 21M parameters and links the IR_iPSCs supporting repository
and Zenodo record 21135982. This provides a concrete fresh lead, not verification
of a downloadable model. Direct article access was unreliable; indexed primary
text supplied the version and code-availability statements.

The [supporting repository](https://github.com/marsico-lab/IR_iPSCs) is pinned at
`6587f57dbe9a11c8e62336f808175c66258537bb`. Its
[configuration](https://github.com/marsico-lab/IR_iPSCs/blob/6587f57dbe9a11c8e62336f808175c66258537bb/configs/hl_revision_runs_10PIR.json)
points to a private HPC path ending in `0.5.0_RBPNet-11M.pt`, not a public 21M
download. Its environment pins
[lambosaur/parnet](https://github.com/lambosaur/parnet/tree/2e142786ffcec7ea5e23a28e1ec916c7524e6069)
at `2e142786ffcec7ea5e23a28e1ec916c7524e6069`. That fork declares package version
0.5.0. Its tree contains the same three ~30MB preliminary 7M-named models plus a
small example model; no file named for the configured 11M checkpoint is present
in that pinned tree. File names and byte sizes are not parameter-count proofs.

Tag 0.3.0 resolves in the author fork/upstream history to
`cafb663fe34a955298ccb73c0702419718966440`. The local read-only upstream Git tree
contains no `models/` files at that tag; its pyproject metadata says 0.0.1, another
reason not to equate package labels with checkpoint architecture. The Marsico
mirror API rejected the 0.3.0 commit query (422); the author/upstream tag is the
appropriate follow-up. Zenodo metadata timed out and remains unresolved, not
evidence that its artifacts do not exist.

## Consequence

The paper–configuration discrepancy must remain explicit. Current evidence does
not justify saying that changing to 0.3.0 recovers the published model. Continue
with the exact tagged history, author-linked assets, support notebooks and Zenodo
alternative endpoints. A usable non-paper-matching artifact must receive its own
name, provenance, license and smoke test, rather than inherit the 21M claim.

## Author-workflow follow-up

The exact upstream 0.3.0 tree was retrieved and checked in addition to the local
Git tree. It contains example masks and a 1,961,643-byte example model, but no
identified paper-matching 21M weight file. This example is not admitted based on
its filename. The supporting half-life workflow notebook and its Python pipeline
were also retrieved at the pinned IR_iPSCs commit. The notebook selects a local
fine-tuned `best_model_epoch=27_val_auroc=0.864.ckpt`; its pipeline loads the
configured `parnet_weights` from the private HPC path. Neither provides a new
public 21M model URL. The later fine-tuned task checkpoint must not be confused
with the original pretrained encoder.

Zenodo's record API timed out on repeated bounded attempts. The alternate
`/records/21135982/export/json` endpoint also timed out. These are unresolved
retrieval failures, not proof that the record has no weights. The operational
decision is **not reproducibly recovered for this run**, with available RBPNet
and separately identified 3UTRBERT features used as alternatives. No RNAddress-
trained model is substituted under the Parnet name, and no new claim is made that
tag 0.3.0 has 21M parameters without the actual checkpoint.

Downloaded source/metadata are untrusted evidence and are not automatically
executed. Each successful retrieval has its exact URL, source commit where
applicable, bytes, SHA-256 and timestamp. Receipts are in
`results/mechanism_v2/manifests/resource_retrieval_*.json`; failure records remain.
The old FinalShot exclusion and all its files are unchanged.
