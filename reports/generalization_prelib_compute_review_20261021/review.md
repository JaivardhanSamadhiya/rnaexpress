# PRELib399-fit pipeline: static compute review

Status: SOURCE-ONLY RESOURCE STUDY,21 October2026. No NumPy or other scientific package was imported, no project cohort/feature/outcome payload was opened, and no numerical kernel, fit, guard override or duplicate PUM production was run. This report changes no study definition or execution authorization. The companion source_metadata_receipt.json binds observed source/report bytes and records arithmetic payload estimates, not measured native peaks.

The existing study is src/generalization_prelib_pooled_lineage_20261009. Its399 fits are378 inner plus21 outer over three fixed arms, seven nominal whole-lineage outer folds, six inner lineage folds and lambdas.005/.05/.5. All4054 edits,16 WT/mPRE backgrounds and seven lineages, pooled PUM2 primary target, weighting, larger-lambda tie policy,18 target sensitivities, PUM1 descriptive scope and both-control robustness gates remain unchanged. No new representation, loss, source, count filter or favorable lineage is proposed. This is exposed pooled binding association development, not localization generalization.

## Static allocations: arithmetic is small; peak memory is unmeasured

These are float64 payloads at the full4054-row upper bound. Inner/outer training subsets are smaller; no real lineage sizes were inspected.

| Object | Shape | Bytes | MiB |
|---|---:|---:|---:|
| Kmer matrix |4054×84|2724288|2.5981|
| Each augmented matrix |4054×85|2756720|2.6290|
| All three arm matrices |84+85+85 columns|8237728|7.8561|
| Four fixed PUM operator columns |4054×4|129728|0.1237|
| One target or weight vector |4054|32432|0.0309|
| All18 targets as dense numbers |4054×18|583776|0.5567|
| Largest ridge Gram/identity |85×85|57800|0.0551|
| Kmer span Gram equivalent |84×84|56448|0.0538|
| Largest coefficient/scale vector |85|680|0.0006|

Source [pipeline.py:41](D:/rnaexpress/src/generalization_prelib_pooled_lineage_20261009/pipeline.py:41) forms weighted RMS, an active-column standardized copy, a weighted standardized copy, an85×85 Gram and a regularized solve. Boolean/advanced indexing and each x/scale expression allocate additional matrices. The three global arm arrays stay live; one selected training matrix, active/scaled copies, predictions, targets and solver workspace can coexist. This is still not a pair×feature or399-model simultaneous allocation. Native BLAS/LAPACK workspace, thread stacks and import peaks are not bounded by the table.

The feature stage additionally runs seven training-only np.linalg.lstsq span checks with rcond1e-12 ([pipeline.py:90](D:/rnaexpress/src/generalization_prelib_pooled_lineage_20261009/pipeline.py:90)). Each can retain a training slice plus weighted copy, RHS and SVD workspace. Preserve lstsq, its cutoff and recorded span definition; do not replace it with a faster solver or turn its result into a new model-selection rule.

JSON and Python objects matter. The compressed feature roster is decompressed and parsed into lists/dictionaries before conversion to NumPy; those lists remain in data while numerical arrays are live. Source ancestry/design rows, selected raw-count records,18 target lists, fold indices/weights and JSON serialization buffers coexist at different stages. A Python float/list entry costs more than its8-byte numeric payload. No actual object counts, string lengths, gzip sizes or whole-stage peaks were measured here.

One useful exact source-count estimate: the seven-outer/six-inner roster contains43N stored integer indices and36N stored weights,79N=320266 primitive entries at N4054. Under nominal64-bit CPython int28B/float24B plus8B list references, this is about10.44MiB before headers, over-allocation, dictionaries and serialization. This is a logical object-layout estimate, not RSS.

Fits accumulate only one outer-lineage/arm bundle at a time:18 inner fits and one outer fit, then write one compressed checkpoint. Across the entire study, stored inner and outer prediction lists contain57N=231078 values, but they are not all needed simultaneously. Evaluation and independent replay load one bundle at a time.399 describes repeated arithmetic/time, not a399-fold multiplier of peak model memory.

## Every existing resource admission and runtime condition

The source-defined fresh() requires at least3GiB available physical RAM ([pipeline.py:18](D:/rnaexpress/src/generalization_prelib_pooled_lineage_20261009/pipeline.py:18)). It does not itself enforce a child-private-byte cap, system commit reserve, wall deadline or continuous working-set monitor. Those would require a separately reviewed external controller and may supplement, never silently replace, this guard.

| Existing phase | Guard sites on a successful full run | Numerical import |
|---|---|---|
| features |entry1; numpy_runtime before/after2; seven span iterations7: total10|NumPy once|
| prefit |entry1|None|
| fit |entry1; numpy_runtime2; admitted1;21 arm starts;378 inner lambda checks: total403|NumPy once|
| evaluate |admitted1|None|
| independent verify |numpy_runtime2; admitted1;21 checkpoint-bundle checks: total24|NumPy once|

These are static successful-path counts, not observations. The outer refit has no separate fresh() immediately on its own line; it follows the inner grid and existing checks. The original numerical_contract also executes two tiny invented ridge cases in features and again in fit, outside the399 biological fits. No production behavior is changed by identifying these distinctions.

numpy_runtime() ([pipeline.py:29](D:/rnaexpress/src/generalization_prelib_pooled_lineage_20261009/pipeline.py:29)) requires a fresh process with no already imported NumPy/pandas/SciPy/sklearn/Torch/Transformers/OpenVINO; bundled CPython3.12/cpython-312; original executable path and pinned Python native bytes; PYTHONDONTWRITEBYTECODE=1; PYTHONUTF8=1; OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=2. It selects the exact existing mechanism_v2 scientific prefix and verifies NumPy1.26.4, actual native core, imported NumPy files and loaded BLAS/native origins against the committed runtime receipt.

The launcher name contains SpliceBERT, but this path imports its standard-library bootstrap utilities and NumPy only; it does not load a BERT model, Torch or OpenVINO. Conversely, pipeline.numpy_runtime does not call the launcher's full check_runtime() inventory: do not relabel its loaded-file proof as a new whole-prefix certification. Preserve the original proof and explicitly pin any additional calibration inventory separately. Sources: [launcher.py:26](D:/rnaexpress/src/generalization_splicebert_runtime_compatibility_20261007/launcher.py:26), [launcher.py:107](D:/rnaexpress/src/generalization_splicebert_runtime_compatibility_20261007/launcher.py:107), [common.py:67](D:/rnaexpress/src/generalization_splicebert_runtime_compatibility_20261007/common.py:67).

Two threads are part of the frozen numerical policy. Do not transplant a one-thread profile, lower precision, different NumPy/BLAS or alternate lstsq/solve into production and call it the same run. A global thread count also is not a hard process-memory cap.

## Checkpoints, provenance and restart limits

Features require committed original PUM production AND independent feature-replay receipts, with matching file hashes, before assembling any4054-row numerical block. This review does not duplicate the4070-allele PUM scorer or its independent replay. The feature receipt and fold/weight roster then require root review/commit before a FIT prefit admits labels.

The FIT prefit fixes actual feature bytes, row order, source IDs, ancestry, labels and source implementation hashes. Production uses weighted ridge with zero intercept/no centering, weights summing1, train-only RMS and frozen zero-support coefficients. No resource experiment can change those invariants or the grid/selector. The verifier checks original-unit and scaled-coordinate stationarity, score agreement, all399 fits, source selections,18 target views and original robustness gates without refitting ([verify.py:26](D:/rnaexpress/src/generalization_prelib_pooled_lineage_20261009/verify.py:26)).

There are21 outer-lineage×arm compressed checkpoint files, each containing all18 inner results and its outer result, not399 separately resumable files. Writes use exclusive creation. Any existing destination stops fit() rather than silently resuming; a kill during a write can leave a partial gzip file. Preserve it and the failure log. No automatic retry, deletion, overwrite, ignored failed lineage, shortened grid or generic resume adapter is authorized. A separately reviewed future resumption would have to verify all prior creation/input/configuration bindings and preserved failures first.

## Smallest next step: a separately frozen invented-only native calibration

This is a PROPOSAL, not an executable preparation or a new guard exception. Before any native run, write/review/commit a new isolated calibration namespace. It must use only invented arrays/targets/anonymous lineage-background records, the existing pinned bundled runtime and two threads. No project dataset, author count, DNA, PUM scalar, feature-roster or real checkpoint file is opened.

1. Reuse the unchanged numpy_runtime admission and provenance proof in a fresh child; all existing3GiB checks remain. Run the original tiny analytic ridge contract, including duplicate and zero columns, with unchanged tolerances.
2. Exercise fixed N4054, widths84/85, three simultaneous arm arrays, weighted RMS, rank-deficient/zero/duplicate columns and a deterministic invented PUM-like scalar. Measure original ridge/predict kernels over the three fixed lambdas. Exercise np.linalg.lstsq(...,rcond=1e-12) on the fixed84-column span problem. Use a seed declared before execution, such as20261021; do not generate real sequence-derived features.
3. If that bounded case passes, the same fixed calibration may simulate the complete399-fit schedule over seven invented groups/16 invented backgrounds, with original source weighting and selection functions and serialization to its OWN paths. Include representative JSON/list/gzip overhead and independent score/stationarity replay. This measures operational time/memory only; its lambda choices and synthetic errors are not biological results and select no production setting.

Provisional budgets to freeze before such an attempt: caller available physical RAM>=3.5GiB; unchanged worker fresh>=3GiB; system commit reserve at launch>=2GiB; worker private-commit cap768MiB; aggregate owned-job commit cap1GiB; one scientific worker; existing two numerical threads; fresh workspace disk>=1GiB; five-minute kernel-calibration deadline. These are conservative candidate budgets, NOT validated peak requirements or permission to lower any existing floor. Original guard failure remains failure even if external reserves are otherwise satisfied. Record working set as well as private/job commit, controller overhead, all sample gaps and final lifetime peaks/resources after provenance hashing.

The exact allowed helper-process roster is unresolved. Root reports a PUM startup hard-active-process stop despite small native helper tests. That is not a biological failure or proof of excess matrix memory. Before freezing an active-process cap for this new calibration, use the separate owned-process identity evidence to pin the actual worker/Git helper topology. Do not blindly copy the failed two-process policy, arbitrarily raise it after a failure, allow a second scientific worker or weaken membership/ownership checks. No such process probe or child was run for this report.

A lower-floor NumPy calibration, if later desired, is outside this proposal's existing-guard execution and needs separate explicit scope approval plus source/test/controller freeze. The approved PUM-scalar callback exception covers neither this pipeline nor NumPy,399 fits, conservation or any general future worker. No current callback, queue, deadline or original guard is modified here.

## Full stages remain separate admissions

Only after actual calibration measurements and a reviewed resource controller may root authorize stages individually: existing feature assembly/span checks; root commit feature receipt; existing prefit/roster construction and commit;399 fits; fixed-prediction evaluation; independent399-model replay. Keep all original phase prerequisites and3GiB guards. Evaluation is standard-library-only but still calls admitted()/fresh(); it is not an indirect route around admission. At most one owned scientific child runs; no scheduled task, new installation, paid compute or unrelated-app termination is proposed.

Before each stage bind original source/runtime/input hashes and the exact approved operational scope. Preserve all existing outputs, capture creation identities/limits, and save a distinct operational receipt with peaks, resources, actual threads, time and exit status. A cap/deadline/import/provenance failure stops only the owned job and preserves partial artifacts. All original completion and independent-replay receipts remain necessary; an external resource receipt cannot substitute for them. Any future policy change needs its own reviewed approval, not post-hoc relabeling of the present3GiB requirement.

No low-RAM feasibility, runtime duration, predictive benefit or localization generalization is established by this static review. The justified conclusion is narrower: the dense arithmetic is small enough to warrant a finite invented-only measurement before committing a long, nonresumable biological fit stage.
