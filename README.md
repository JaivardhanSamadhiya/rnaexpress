# RNAddress

RNAddress investigates a constrained inverse problem in RNA localization:

> Given an existing RNA regulatory sequence, a requested localization change, and protected molecular properties, which minimal nucleotide edit should be selected?

The repository is deliberately science-gated. Full model development is forbidden until the public intervention datasets have been acquired, checksummed, reconstructed, and reviewed under the Phase A–E GO/NO-GO protocol.

## Current status

**Phase A–E completed with a strict GO on 2026-08-26. No model results exist yet.**

The truth-safe historical benchmark contains 4,395 exhaustive N-zip SNVs across 15 parents. The locked external benchmark contains 4,553 verified astrocyte SNVs across eight in-vivo parents; its outcome-free feature artifact and source hashes are frozen. See [the Phase A–E report](reports/phase_A_E_report.md), [hostile novelty audit](reports/novelty_audit.md), and [prespecified validation architecture](reports/validation_architecture.md).

## Reproduce the Phase A–E audit

After acquiring the public archives listed in `data/manifests/acquisition_manifest.csv`:

```bash
python -m src.pairing.reconstruct_nzip
python -m src.pairing.reconstruct_mikl
python -m src.pairing.audit_astrocyte
python -m src.acquisition.build_manifests
python -m src.acquisition.inventory
python -m pytest -q
```

Reconstruction is truth-safe: row/key inconsistencies and invalid SNVs fail; parent identities that cannot be uniquely proven are quarantined and counted rather than guessed.

## Scientific guardrails

- No random mutation-level train/test split.
- All edits from one parent remain together.
- No astrocyte mutation outcome values may enter development, threshold selection, or model design.
- Retrospective published outcomes are called historical or locked external validation, never prospective validation.
- Prediction accuracy is supporting evidence; inverse recommendation quality is the central outcome.
- A generic forward predictor plus exhaustive edit search is a mandatory baseline.
