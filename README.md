# RNAddress

RNAddress investigates a constrained inverse problem in RNA localization:

> Given an existing RNA regulatory sequence, a requested localization change, and protected molecular properties, which minimal nucleotide edit should be selected?

The repository is deliberately science-gated. Full model development is forbidden until the public intervention datasets have been acquired, checksummed, reconstructed, and reviewed under the Phase A–E GO/NO-GO protocol.

## Current status

**Phase A–E passed, but the preregistered locked internal model gate failed on 2026-08-26. External Astrocyte outcomes remain sealed.**

The truth-safe historical benchmark contains 4,395 exhaustive N-zip SNVs across 15 parents. Pairwise ranking led the 12-parent development analysis (rank percentile 0.636), but on the untouched three-parent internal lock it scored 0.566 versus 0.624 for strong forward-model exhaustive search. The gate therefore failed, no external prediction freeze was authorized, and no Astrocyte outcomes were analyzed. See [development results](reports/development_results.md), [locked internal results](reports/locked_internal_results.md), the [post-lock hostile audit](reports/hostile_internal_audit.md), and the [frozen 53/100 scorecard](reports/frozen_scorecard.md).

The external benchmark still contains 4,553 verified Astrocyte SNVs across eight in-vivo parents. Its outcome-free feature artifact and source hashes are frozen; its localization, expression, translation, and ribosome-occupancy outcomes remain unavailable to model development.

## Reproduce the analysis

After acquiring the public archives listed in `data/manifests/acquisition_manifest.csv`:

```bash
python -m src.pairing.reconstruct_nzip
python -m src.pairing.reconstruct_mikl
python -m src.pairing.audit_astrocyte
python -m src.acquisition.build_manifests
python -m src.acquisition.inventory
python -m src.analysis.assay_reliability
python -m src.modeling.development_benchmark
python -m src.modeling.freeze_internal
python -m src.analysis.evaluate_internal_lock
python -m src.analysis.hostile_internal_audit
python -m pytest -q
```

`evaluate_internal_lock` is a reveal-stage command. Its frozen prediction hash is checked before labels are joined, and rerunning it must never be used for model changes.

Reconstruction is truth-safe: row/key inconsistencies and invalid SNVs fail; parent identities that cannot be uniquely proven are quarantined and counted rather than guessed.

## Scientific guardrails

- No random mutation-level train/test split.
- All edits from one parent remain together.
- No astrocyte mutation outcome values may enter development, threshold selection, or model design.
- Retrospective published outcomes are called historical or locked external validation, never prospective validation.
- Prediction accuracy is supporting evidence; inverse recommendation quality is the central outcome.
- A generic forward predictor plus exhaustive edit search is a mandatory baseline.
