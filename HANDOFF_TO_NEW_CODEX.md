# RNAddress transfer handoff — 11 September 2026

Use the prompt below verbatim in the destination Codex account after cloning this
repository. This document is deliberately an operational handoff, not a new
scientific conclusion. The project is **not complete** and Astrocyte remains
sealed.

```text
You are continuing the RNAddress-Mechanism-v2 project in this repository.

Read HANDOFF_TO_NEW_CODEX.md in full before taking action. Then read the
controlling user prompt at
C:\Users\jaisa\.codex\attachments\5820b267-5e61-47ce-88c5-5396acfb6a83\pasted-text.txt
if that attachment exists; otherwise treat this handoff and the committed
Mechanism-v2 reports/configs as the controlling specification. Work on branch
rnaddress-mechanism-v2 (create it from the checked-out commit if necessary).

Mission: make one rigorous prospective test of whether mutation-induced,
mechanism-aware features can select RNA-localization interventions zero-shot.
Do not force a positive result. FinalShot commit 98ffc02 is a permanently
reproducible historical negative: "NO-GO — END ZERO-SHOT RNADDRESS." Never alter
or reinterpret it. Mechanism-v2 is a distinct new experiment.

NON-NEGOTIABLE BOUNDARIES
- Never access N-zip outcomes or quarantined TDP EV5 stability data.
- Astrocyte is sealed. Do not load its sequence, labels, outcomes, feature rows,
  metrics, schema that exposes outcomes, or downstream files containing them.
  It may be opened once only after a complete, committed pre-holdout freeze and
  the protocol expressly authorizes it.
- Do not change frozen representations, feature hashes, splits, model grid,
  tie rules, gates, or selection rules after examining new outer results.
- Do not silently use source, reporter, parent, gene, absolute sequence/RBP blocks
  in the primary latent score. Do not zero-fill unsupported stability/trans data.
- Treat every unknown file as potentially sealed until its contents are safely
  established. Preserve the old result namespaces.

START WITH READ-ONLY INTEGRITY CHECKS
1. `git log --oneline -10`, `git status --short`, and read this handoff.
2. Use the bundled CPython, not PATH Python:
   C:\Users\jaisa\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
   Its Mechanism-v2 isolated dependencies are expected under
   data/interim/mechanism_v2/runtime.
3. Run `-u -m src.mechanism_v2.run_pipeline audit` and the safe test target
   `-u -m src.mechanism_v2.run_pipeline test`. Do NOT run unfiltered repository
   pytest: legacy tests can load protected N-zip/Astrocyte inputs.
4. Rehash manifests before reuse. The key all-allele95 split manifest and
   development-training freeze must remain byte-identical. Verify all completed
   training checkpoints through `python -m src.mechanism_v2.training_status`.
   If a status record already exists, inspect it rather than overwriting it.

WHAT IS COMPLETE AND COMMITTED
- FinalShot preservation/audit: 244 protected artifacts verified repeatedly.
- Exact all-allele 95% global-Levenshtein audit: 72,998 unique sequences,
  117,515 candidate comparisons, no new cross-component edge, 211 components.
- Stricter all-allele 90% audit: 88,884,604 exact candidate comparisons, no new
  cross-component edge, still 211 components. This is a sensitivity only, never
  a replacement for the primary 95% folds.
- RBPNet signed delta 62,665x412; structure 62,665x18; processing 62,665x8;
  motif-accessibility 62,665x8; pooled BERT allele delta 62,665x128; compact
  trans interactions 93,208x4. Their manifests/hashes are in
  results/mechanism_v2/features/.
- All 103 absolute RBP allele shards passed arithmetic reconstruction versus the
  signed delta. These absolute blocks are controls, not primary inputs.
- Independent external stability reconstruction/validation is a documented
  negative in BOTH cells and is excluded. Do not retune it or retry a different
  architecture under the same claim.
- 48 prospectively frozen recipes across M0–M7, 5 outer folds x 3 inner folds.
  All 720 INNER-ONLY fits have completed with no stderr and five inner selections.
  `inner_complete.json` explicitly says outer evaluation is false. Do not report
  their numerical selection results as final outer evidence.
- 43 purged transfer partition inventories exist; one GFP→Firefly fold with zero
  eligible held groups is ineligible and must be reported, not passed.
- External HGNC/HCOP gene-group sensitivity inventory: 96 eligible groups from
  183 annotated units, primary splits unchanged. It is a conservative annotated-
  only sensitivity, not a complete mouse paralog phylogeny.
- 74 safe Mechanism-v2 tests passed at the handoff checkpoint; new tests may
  increase that count. Deep-research novelty audit is committed and explicitly
  limits novelty claims.

LOCAL CACHE TRANSFER (IMPORTANT)
Ordinary Git intentionally excludes large reproducible caches and 720 inner-fit
checkpoints (~0.7 GB). To resume without recomputation, copy these directories
from the original D:\rnaexpress workspace into the same relative paths in the
clone before verification:
- data/interim/mechanism_v2/
- data/external/mechanism_v2/
- models/mechanism_v2/
- results/mechanism_v2/training/
- results/mechanism_v2/features/ (manifests are committed; arrays are not)
- results/mechanism_v2/stability/ and data/interim/finalshot_rbpnet_cache/
Do not put large caches into ordinary Git history. The commit records hashes and
the pipeline can reproduce public resources, but the old RBPNet profile cache is
an immutable expensive reconstruction artifact and must never be modified.

CURRENT NEXT WORK, IN ORDER
1. Verify/copy caches and audit the completed 720 inner checkpoints. Commit a
   concise verification receipt only after success. Do not start duplicate fits.
2. Implement a separately frozen OUTER evaluator that, for each outer fold,
   trains only the inner-selected recipe on that fold's development rows and
   scores its untouched outer rows. It must record predictions, candidate/outcome
   cohort hashes, deterministic tie selection, component bootstrap, eligibility,
   exclusions, model hashes and exact commands. It must never touch Astrocyte.
3. Before outer evaluation, implement and test all prospectively specified
   controls: M0/M1–M7 comparisons; N0–N10 as applicable; block removals;
   random kmer M1-matched null; whole-intervention bijections; absolute blocks;
   correctly pooled recipient-window broken-reference RBP null; structure and
   trans controls; bootstrap/uncertainty; all purged transfer tasks; sequence90
   and annotated gene-group sensitivities. The source code presently includes
   control kernels and inventories, not completed control fitting.
4. Commit the full outer evaluation implementation, exact reports/templates,
   formal multiple-testing/uncertainty code and final frozen protocol BEFORE
   generating ANY outer scores. The gates are already prospectively stated in
   reports/mechanism_v2/prospective_gate_design.md; retain them unless a genuine
   pre-result software/integrity defect makes the protocol impossible, in which
   case preserve and document the defect rather than silently changing it.
5. Run the outer evaluation once under that committed freeze; verify its outputs;
   write required reports and a candid development verdict. Only if every gate,
   integrity condition and report is complete should you create/commit the
   pre-holdout freeze and request/execute the ONE authorized Astrocyte opening.
6. Final conclusion must use exactly one allowed verdict: STRONG GO — UNIVERSAL
   ZERO-SHOT RNADDRESS SUPPORTED; PARTIAL GO — RESTRICTED ZERO-SHOT DOMAIN
   SUPPORTED; or NO-GO — END UNIVERSAL ZERO-SHOT RNADDRESS. Do not turn a
   development-only result into a GO claim.

READ THESE FIRST
- reports/mechanism_v2/protocol_design.md
- reports/mechanism_v2/model_selection.md
- reports/mechanism_v2/prospective_gate_design.md
- reports/mechanism_v2/reproducibility.md
- reports/mechanism_v2/implementation_incidents.md
- reports/mechanism_v2/stability_external_model.md
- reports/mechanism_v2/delta_representation.md
- reports/mechanism_v2/processing_splicing_model.md
- reports/mechanism_v2/gene_family_sensitivity.md
- reports/mechanism_v2/novelty_audit.md
- configs/mechanism_v2/localization_design.json
- results/mechanism_v2/manifests/development_training_freeze.json
- results/mechanism_v2/manifests/splits_all_alleles95.json

Do not claim the project is complete, PV-CARE level, externally validated, or
positive until the stated gates actually pass. Keep the user updated at least
every 60 seconds during long work and commit each verified checkpoint.
```

## Publication state

This Git repository stores source, specifications, manifests, reports and compact
results. Large source/feature/model caches are intentionally excluded through
`.gitignore`: they exceed normal GitHub transport limits and include immutable
reconstructable or already-provenanced artifacts. Copy the listed cache folders
out-of-band (external drive, encrypted storage, or a dedicated data release)
when moving to the other account.

At handoff, the two background processes have finished normally:

- Inner training: 720 of 720 inner-only fits; stdout ends `Outer fold 4: inner
  selection complete; outer outcomes not evaluated`; stderr is empty.
- Sequence-90 sensitivity: 72,998 sequences, 88,884,604 exact candidate
  comparisons; 211 components; stderr is empty.

The current uncommitted handoff checkpoint includes these completion receipts,
the sequence-90 inventory, and this document. It contains no outer-test results
and no sealed-data access.
