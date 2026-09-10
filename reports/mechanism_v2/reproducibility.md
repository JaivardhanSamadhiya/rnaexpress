# Mechanism-v2 reproducibility log

Base experiment: FinalShot `98ffc02`; isolated branch `rnaddress-mechanism-v2`.
First audit checkpoint: `c1867cb`. All original 238 release artifacts and six
additional inputs remain covered by the 244-entry preservation manifest.

The isolated CPU environment lives in `data/interim/mechanism_v2/runtime`.
Use the bundled CPython executable (not the unrelated MSYS `python` on PATH):

```powershell
& 'C:\Users\jaisa\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -u -m src.mechanism_v2.run_pipeline audit
& 'C:\Users\jaisa\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -u -m src.mechanism_v2.run_pipeline test
& 'C:\Users\jaisa\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -u -m src.mechanism_v2.run_pipeline resources
& 'C:\Users\jaisa\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -u -m src.mechanism_v2.run_pipeline audit-probes
& 'C:\Users\jaisa\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -u -m src.mechanism_v2.run_pipeline features --workers 3
```

The runner inserts only the isolated runtime into its import path. Network
retrieval requires host permission. No system packages or old inference runtime
were replaced. Installation of edlib failed because no Microsoft C++ compiler was
available; the failure did not install a substitute model. Local alignment uses
a tested dynamic-programming convention; RapidFuzz provides a Windows wheel for
distance-only grouping sensitivity. Exact versions are recorded in the lock file.

At the completed extraction checkpoint, 60 new tests passed. Fifteen audited
legacy resource/protocol tests also passed. Whole-repository tests are not run:
some explicitly load protected N-zip outcomes or Astrocyte features. The new holdout test checks
that the reader is never reached for unauthorized paths; passing an `authorized`
flag cannot open the holdout. Unimplemented training/evaluation/freeze/holdout
stages fail explicitly rather than reporting fabricated completion.

## Preserved failed diagnostic

Probe v1 incorrectly interpreted literal `gene_id='missing'` as a shared gene,
joining unrelated Moffatt parents. Inspection of full-data component membership
detected the error before new localization modeling. Its outputs are retained
and explicitly withdrawn in `forensics/withdrawn_probe_v1.json`. Five sentinel
regression tests were added. Corrected diagnostics write to `forensics/probes_v2/`
and yield 211 components from 213 prior units, including two cross-source gene
overlaps. None of the old scientific results or gates was changed.

The forensic bootstrap is a fresh, valid source-stratified implementation with
paired directions. Vectorized RNG draw ordering differs from the archived loop;
its CI is not advertised as bitwise reproduction of the old bootstrap sample.

No N-zip outcomes or Astrocyte data were loaded. There is no final model freeze,
no completed new outer evaluation and no new scientific verdict yet.

## Second implementation checkpoint

All 212,979 local folding windows completed. The final structure array is
62,665 × 18, SHA-256
`d8a33188a89dbfd7adb9c236323cc242bbf699d4121e9ddf2c30be2edbc19f90`.
Signed RBP (412 columns), contextual BERT deltas (128 columns), pilot and full
structure arrays all passed fresh hash, shape and finite-value checks. The
244-artifact historical preservation check passed again.

Both 95% and 90% parent-sequence grouping thresholds yield 211 components from
213 units. Five outer and three inner folds are generated deterministically
without outcomes and validated for component/intervention separation. These
thresholds do not add new merges beyond the exact/gene grouping; they are not
evidence of gene-family independence. Split files and component-to-fold maps
are retained, not regenerated after seeing performance.

Additional commands executed:

```powershell
& 'C:\Users\jaisa\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -u -m src.mechanism_v2.run_pipeline external_stability
& 'C:\Users\jaisa\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -u -m src.mechanism_v2.run_pipeline stability-reads
& 'C:\Users\jaisa\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -u -m src.mechanism_v2.run_pipeline stability-recover --limit 10000
& 'C:\Users\jaisa\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -u -m src.mechanism_v2.run_pipeline stability-recover
& 'C:\Users\jaisa\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -u -m src.mechanism_v2.run_pipeline splits
```

Full-genome-window retrieval is a separate network operation in
`stability_mapping.fetch_windows(None, ('hg38',))`; the initial pilot uses
`fetch_windows()` and `map_library()`. Exact URLs and timestamps are retained
in individual content-hash receipts. Both raw mate checksums passed before
sequence discovery. A subsequent `map_library(pilot=False)` consumes the full
window inventory only after it completes.

New namespace-local `.gitattributes` disable Git text conversion for recorded
byte hashes. They do not alter FinalShot attributes or files. Generated feature
arrays/raw FASTQ remain local cache artifacts with recorded hashes and retrieval
provenance rather than being added as gigabyte Git blobs.

## Completed overnight extraction and independent validation (10 September)

All 103 absolute RBP allele shards completed. Their mutant-minus-reference
arithmetic reconstructs the signed delta block within the locked 1e-6 tolerance.
Both absolute matrices, the separate pooled BERT allele delta, all 72,998 motif
sequence folds, and the compact CAD/N2A trans interactions completed. A fresh
recursive verification checked 215 feature arrays (including all allele shards)
against their recorded SHA-256, shapes and finite values. All 244 preservation
checks passed again. No duplicate extraction processes were started.

The exact all-allele 95% global-Levenshtein audit performed 117,515 candidate
comparisons over 72,998 unique sequences and found no additional cross-component
edges. There remain 211 connected groups. Its five outer and three inner fold
inventories supersede the parent-only primary inventory before localization
modeling. The 90% parent-only sensitivity does not establish gene-family isolation.

Independent external stability validation was frozen in commit `ccc50ca` before
fitting. Both SH and HEK models failed admission; all out-of-fold predictions,
bootstrap samples and failed summaries are retained. No stability predictor was
exported or applied to localization. This negative result is not a failed download
or an invitation to retune its admission thresholds.

Commands completing this checkpoint use the same bundled executable above with
`-u -m src.mechanism_v2.run_pipeline` and stages `stability-validate`,
`motifs --workers 3`, `processing`, `sequence-audit`, `allele-summaries`,
`trans-context`, and `test`. The paired evaluation module also rejects comparisons
whose candidate/outcome cohort hashes differ, even if candidate counts match.
