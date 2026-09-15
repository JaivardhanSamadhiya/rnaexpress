# Dataset guide — what is in Git vs what to download

This document lists every data dependency for RNAddress. **Large raw archives are not committed to Git.** Small processed tables, manifests, and the certified Mechanism-v2–v5 benchmark **are committed**.

---

## Committed in this repository (no download needed)

### Primary evaluation benchmark (required for Mechanism-v2–v5)

| Path | Description | Size (approx.) |
|---|---|---|
| `results/v4_phaseB/model_candidate_rows.csv.gz` | 93,208 candidate rows, all three sources | ~9.8 MB |
| `results/v4_phaseB/model_interventions.csv.gz` | 62,665 intervention records | — |
| `results/v4_phaseB/biological_split_manifest.csv` | Frozen outer-fold assignments | — |
| `results/v4_phaseB/*.json`, `*.csv` | Audits, gates, transfer metrics | — |

**Verify after clone:**

```bash
# Linux/macOS
sha256sum results/v4_phaseB/model_candidate_rows.csv.gz
# Expected: 4e2339e1845147a14076bd8db9105a60ac91c59607c718212b59199f3ec0fd4c
```

### Manifests and inventories

| Path | Description |
|---|---|
| `data/manifests/acquisition_manifest.csv` | Download URLs, DOIs, expected checksums |
| `data/manifests/file_inventory.csv` | Full local inventory with SHA-256 |
| `data/manifests/nzip_parent_split.csv` | N-zip parent split assignments |

### Frozen lock artifacts (small)

| Path | Description |
|---|---|
| `data/frozen/*.json` | Lock manifests for TDP, Moffatt, N-zip truth, external models |
| `data/frozen/tdp43_v2_locked_features.csv.gz` | TDP feature lock |
| `data/frozen/astrocyte_external_features.csv.gz` | Astrocyte **features only** (no outcomes) |

### Selected processed tables

| Path | Description |
|---|---|
| `data/processed/tdp43_v3_diagnostic_pairs.csv.gz` | TDP diagnostic pairs |
| `data/processed/nzip_*` | N-zip processed design/outcome tables (legacy FinalShot era) |

### Compact evaluation evidence

| Path | Description |
|---|---|
| `results/mechanism_v2/outer/*.json` | Mechanism-v2 outer verdict and manifests |
| `results/mechanism_v3/outer/*.json` | Mechanism-v3 evidence |
| `results/mechanism_v4/outer/development_evidence.json` | Mechanism-v4 scores |
| `results/mechanism_v5/outer/development_evidence.json` | Mechanism-v5 scores |

---

## NOT committed — download manually

Raw data live under `data/raw/` (gitignored). After download, run checksum verification against `data/manifests/file_inventory.csv`.

### 1. Mikl neuronal MPRA — **GSE173098** (primary Mechanism-v5 cross-gene source)

| Item | URL |
|---|---|
| Processed counts | https://ftp.ncbi.nlm.nih.gov/geo/series/GSE173nnn/GSE173098/suppl/GSE173098_RNAloc_MPRA_counts.csv.gz |
| Supplementary ZIP | https://pmc.ncbi.nlm.nih.gov/articles/PMC9561380/bin/gkac806_supplemental_files.zip |
| GEO landing page | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE173098 |
| Paper | von Kügelgen et al. (2022) NAR, doi:10.1093/nar/gkac045 |

**Local path:** `data/raw/mikl_gse173098/`  
**Expected checksum (counts):** `sha256:809e4d3f286edd3373ebf2dfb3b93a658179a83eac85007a04ad381612f44d99`

---

### 2. Moffatt deep mutagenesis — **GSE334718** (Mechanism-v4 primary source)

| Item | URL |
|---|---|
| Raw archive | https://ftp.ncbi.nlm.nih.gov/geo/series/GSE334nnn/GSE334718/suppl/GSE334718_RAW.tar |
| GEO landing page | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE334718 |
| Paper | Moffatt et al. (2026) bioRxiv, doi:10.64898/2026.06.09.731215 |

**Local path:** `data/raw/moffatt_gse334718/`  
**Expected checksum (RAW.tar):** `sha256:abc6e571ed68833e3fb0c0028209303a0f468347ac5f6efbeffd788c35c7ade1`

---

### 3. TDP-43 neurite reporters — **GSE288185**

| Item | URL |
|---|---|
| GEO landing page | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE288185 |
| Paper / PMC | https://pmc.ncbi.nlm.nih.gov/articles/PMC12864922/ |

**Local path:** `data/raw/gse288185_metadata/` (metadata and supplementary files)  
**Note:** Outcomes are in the certified `results/v4_phaseB/` table; raw rebuild optional.

---

### 4. N-zip saturation mutagenesis — **E-MTAB-10902** (SEALED in Mechanism-v2–v5)

Used in legacy FinalShot era only. **Do not load N-zip outcomes** for Mechanism-v2–v5 evaluations.

| Item | URL |
|---|---|
| Supplementary workbook | https://pmc.ncbi.nlm.nih.gov/articles/PMC9991926/bin/41593_2022_1243_MOESM2_ESM.xlsx |
| BioStudies | https://www.ebi.ac.uk/biostudies/studies/E-MTAB-10902 |
| Paper | Mendonsa et al. (2023) Nat. Neurosci., doi:10.1038/s41593-022-01243-x |

**Local path:** `data/raw/nzip/`

---

### 5. Astrocyte SN-MPRA holdout — **GSE330741** (SEALED)

Features-only artifact is committed; **outcomes must not be loaded** until a one-time holdout protocol authorizes it.

| Item | URL |
|---|---|
| Raw archive | https://ftp.ncbi.nlm.nih.gov/geo/series/GSE330nnn/GSE330741/suppl/GSE330741_RAW.tar |
| Supplementary workbook | https://pmc.ncbi.nlm.nih.gov/articles/PMC13142395/bin/media-1.xlsx |
| Analysis code | https://github.com/Dougherty-Lab/astrocyte_sn-mpra |
| Preprint | doi:10.1101/2026.04.27.721172 |

**Local path:** `data/raw/astrocyte_gse330741/`

---

### 6. Optional / legacy sources

| Dataset | Accession | Notes |
|---|---|---|
| Arora 3′UTR MPRA | GSE183192 | Forward-model development; not intervention benchmark |
| SRLE-seq 6-mer screen | HRA016642 | Human nuclear/cytoplasmic; supplementary only committed |

See `data/manifests/acquisition_manifest.csv` for full URLs and checksums.

---

## Mechanism-v2 inner model caches (not in Git)

**Path:** `models/mechanism_v2/inner/`  
**Content:** 720 fitted inner-cross-validation models (5 outer × 3 inner × 48 recipes)  
**Size:** Large (local cache)  
**Reproduce:** Run Mechanism-v2 inner training pipeline after benchmark and features are built:

```bash
python -m src.mechanism_v2.run_pipeline train-inner   # long-running
python -m src.mechanism_v2.training_status            # verify 720/720
```

Receipts and hashes are recorded under `results/mechanism_v2/inner/` (manifests committed where compact).

---

## Download workflow

```bash
mkdir -p data/raw/mikl_gse173098 data/raw/moffatt_gse334718 data/raw/nzip data/raw/astrocyte_gse330741

# Example: Mikl counts
curl -L -o data/raw/mikl_gse173098/GSE173098_RNAloc_MPRA_counts.csv.gz \
  "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE173nnn/GSE173098/suppl/GSE173098_RNAloc_MPRA_counts.csv.gz"

# Verify checksums
python -m src.acquisition.inventory
```

---

## What you need for each pipeline

| Pipeline | Minimum data required |
|---|---|
| Mechanism-v4 / v5 evaluate | `results/v4_phaseB/model_candidate_rows.csv.gz` only (committed) |
| Mechanism-v2 outer evaluate | Above + 720 inner fits in `models/mechanism_v2/inner/` |
| Full rebuild from raw | All raw downloads per sections 1–5 above |
