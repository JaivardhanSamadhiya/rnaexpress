# RNAddress — Zero-Shot RNA Intervention Selection

**Repository:** [github.com/JaivardhanSamadhiya/rnaexpress](https://github.com/JaivardhanSamadhiya/rnaexpress)  
**Branch:** `main` (single canonical branch)

---

## What this project is

**RNAddress** asks a computational biology question:

> Given a reference RNA sequence and a set of candidate edits, can a model **trained without ever seeing that biological parent** rank which edit will most improve **subcellular localization**?

This is **zero-shot RNA intervention selection**: zero-shot because the parent is unseen; intervention because the goal is to pick an edit, not merely classify a sequence.

The repository contains a **five-era, pre-registered evaluation program** (FinalShot → Mechanism-v2 → v3 → v4 → v5) that tests this claim with nested cross-validation, eleven null controls, reliability analysis, and cross-source transfer tests.

### Bottom line (honest result)

**Universal zero-shot RNAddress is not supported on current public benchmarks**, for measured reasons:

| Finding | Detail |
|---|---|
| Paired intervention ranking is unmeasurable | Within-decision outcome reliability **0.239** (~76% noise) |
| Absolute localization is learnable | auROC **0.950** for unseen variants within a known 3′UTR (Mechanism-v4) |
| Edit direction generalizes across genes | auROC **0.705** across **166 unseen genes** (Mechanism-v5) |
| Signal is bulk AU composition | Simple AU-delta and k-mer nulls match or beat mechanism-aware features |
| Cross-assay transfer fails | AU effect **sign is inconsistent** between Moffatt and Mikl sources |

These are **valid scientific results**, not a failed codebase. The project defines measurable prerequisites—reliability, composition controls, sign consistency—for any future intervention selector.

Full verdict reports: [`reports/mechanism_v2/final_verdict.md`](reports/mechanism_v2/final_verdict.md) through [`reports/mechanism_v5/final_verdict.md`](reports/mechanism_v5/final_verdict.md).

---

## Repository layout

```
rnaexpress/
├── src/
│   ├── mechanism_v2/     # Nested CV, 720 inner fits, controls N0–N10, outer evaluation
│   ├── mechanism_v3/     # Grammar arms, capacity ceiling, nonlinear probe
│   ├── mechanism_v4/     # Sequence-level absolute localization estimand
│   ├── mechanism_v5/     # Cross-gene edit direction + cross-source finite difference
│   ├── analysis/         # Phase B/B2 pipelines, legacy development scripts
│   ├── modeling/         # Feature models, metrics, v4 decision models
│   ├── pairing/          # N-zip / Mikl / Astrocyte reconstruction (legacy)
│   └── acquisition/      # Download manifest builders
├── configs/mechanism_v*/ # Frozen designs and gate thresholds (committed before scoring)
├── reports/mechanism_v*/ # Protocols, verdicts, audits
├── results/
│   ├── v4_phaseB/      # Certified development benchmark tables (COMMITTED)
│   └── mechanism_v*/     # Compact outer evidence JSON (COMMITTED)
├── data/
│   ├── manifests/      # Acquisition URLs and checksums (COMMITTED)
│   ├── frozen/         # Lock manifests and small frozen artifacts (COMMITTED)
│   └── processed/      # Selected processed tables (COMMITTED; see DATASETS.md)
├── tests/mechanism_v*/ # Safe unit tests (143 total across v2/v4/v5)
└── DATASETS.md         # What is in Git vs what you must download locally
```

**Not in Git (by design):**

- Raw GEO/archives under `data/raw/` (too large; download locally — see [`DATASETS.md`](DATASETS.md))
- Fitted model caches under `models/mechanism_v2/inner/` (720 inner fits; reproducible from code + benchmark)
- Sealed holdout outcomes (N-zip saturation mutagenesis outcomes, Astrocyte in vivo MPRA)
- Word/report competition drafts (`reports/st_yau_*` — local only)

---

## Certified development benchmark

Mechanism-v2 through v5 share one hash-pinned candidate table:

| File | SHA-256 |
|---|---|
| `results/v4_phaseB/model_candidate_rows.csv.gz` | `4e2339e1845147a14076bd8db9105a60ac91c59607c718212b59199f3ec0fd4c` |
| `results/v4_phaseB/model_interventions.csv.gz` | `a7e651e4a2a1ccf6d16ea43c6da8de384901df9a15cdf82208c2235315989835` |

**Scale:** 93,208 rows · 62,665 interventions · 215 genes · 211 connected components · 445 decision sets

| Source | Accession | Sequences | Genes |
|---|---|---:|---:|
| Mikl neuronal MPRA | [GSE173098](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE173098) | 11,808 | 189 |
| Moffatt deep mutagenesis | [GSE334718](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE334718) | 46,291 | 10 |
| TDP-43 reporters | [GSE288185](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE288185) | 4,566 | 16 |

---

## Requirements

- **Python 3.11+**
- Dependencies: see [`configs/mechanism_v2/requirements.txt`](configs/mechanism_v2/requirements.txt)
- For Mechanism-v2 inner-fit replay, an isolated runtime may live at `data/interim/mechanism_v2/runtime/` (not committed; install from requirements if missing)

```bash
python -m pip install -r configs/mechanism_v2/requirements.txt
```

---

## Quick start — run the evaluations

**Always use scoped tests** (legacy tests may load sealed data):

```bash
# Mechanism-v2 (113 tests)
python -m src.mechanism_v2.run_pipeline test
python -m src.mechanism_v2.run_pipeline audit

# Mechanism-v4 (11 tests) — audit only, design already scored
python -m src.mechanism_v4.run_pipeline test
python -m src.mechanism_v4.run_pipeline audit

# Mechanism-v5 (19 tests)
python -m src.mechanism_v5.run_pipeline test
python -m src.mechanism_v5.run_pipeline audit
```

**Re-run outer scoring** (only if evidence files absent; write-once semantics prevent overwrite):

```bash
python -m src.mechanism_v4.run_pipeline evaluate   # once, pre-registered
python -m src.mechanism_v5.run_pipeline evaluate   # once, pre-registered
```

Mechanism-v2 outer evaluation requires 720 completed inner fits under `models/mechanism_v2/inner/`. Check status:

```bash
python -m src.mechanism_v2.training_status
```

---

## Five evaluation eras (summary)

| Era | Estimand | Key metric | Verdict |
|---|---|---|---|
| FinalShot | Paired intervention ranking | Historical baseline | NO-GO (preserved, commit `98ffc02`) |
| Mechanism-v2 | Nested CV + 11 nulls | Rank gain +0.025; N4 null +0.029 beats primary | NO-GO |
| Mechanism-v3 | Grammar + nonlinear ceiling | Reliability 0.239; ceiling +0.0218 | NO-GO |
| Mechanism-v4 | Absolute sequence localization | T1 auROC 0.950; composition-dominated | NO-GO |
| Mechanism-v5 | Cross-gene + cross-source transfer | Arm A auROC 0.705; sign unstable | NO-GO |

---

## Feature stack (Mechanism-v2 primary)

1,146 mechanism-aware columns (606 core + 540 random-k-mer for ceiling probes):

- Geometry (28), RBPNet signed delta (412), 3UTRBERT pooled delta (128)
- Structure delta (18), processing delta (8), motif delta (8), trans-aligned (4)

Mechanism-v4/v5 use length-invariant k-mer frequencies and delta-k-mer features instead.

---

## Sealed data policy

These are **never loaded** during development evaluations in Mechanism-v2–v5:

1. **N-zip saturation mutagenesis outcomes** (Nat. Neurosci. 2023) — ideal design but forbidden to prevent correlated re-analysis
2. **Astrocyte in vivo SN-MPRA holdout** ([GSE330741](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE330741)) — one-time external confirmation only, after a committed pre-holdout freeze
3. **Quarantined TDP EV5 stability data**

`open_holdout()` in each mechanism package refuses unconditionally.

---

## Reproducing from scratch

1. Clone this repository (`main` branch).
2. Download raw datasets per [`DATASETS.md`](DATASETS.md).
3. Verify checksums against `data/manifests/file_inventory.csv`.
4. Rebuild processed tables (legacy pairing scripts under `src/pairing/` and `src/analysis/`).
5. Run Mechanism-v2 inner training (long-running; 720 fits).
6. Run outer evaluations per frozen protocols in `reports/mechanism_v*/protocol.md`.

The **committed benchmark tables** in `results/v4_phaseB/` allow Mechanism-v4/v5 evaluation without re-downloading raw data.

---

## Citation

If you use this framework or results, cite the underlying datasets:

- von Kügelgen et al. (2022) NAR — GSE173098
- Moffatt et al. (2026) bioRxiv — GSE334718
- TDP-43 neurite MPRA — GSE288185 / PMC12864922
- Mendonsa et al. (2023) Nat. Neurosci. — N-zip (background only; outcomes sealed here)

---

## License

See repository license file. Third-party datasets retain their original GEO/publication terms (see `data/manifests/acquisition_manifest.csv`).
