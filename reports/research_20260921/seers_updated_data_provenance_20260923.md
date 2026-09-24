# SEERS updated-data provenance check, 23 September 2026

AI-authored research working note. This was a bounded metadata search, not a new outcome analysis.

No updated processed-data download or newer linked raw archive was located in the checked official resources. This does not establish universal unavailability.

The [official repository](https://github.com/gao-lab/SEERS/tree/d014bedc3abc032d6151c870d1fb5d519756eabb) names `TALE_train_data_260312.csv` and `3pL6-A549-T1.csv` but states that they are distributed separately. Its root and model READMEs provide no retrieval URL. The training notebook source uses local filenames and provides no downloader. The checked tree has one commit, one branch, no releases, and no tags. Notebook outputs were not inspected and the downloaded notebook was not executed.

The [official BioProject](https://ngdc.cncb.ac.cn/bioproject/browse/PRJCA029014) dynamically links to exactly one GSA-Human archive, HRA008408, and no OMIX datasets. The archive metadata marks the files public and uncontrolled, with creation on 27 August 2024 and last modification/release on 28 August 2024. This strengthens the evidence that the available run collection does not document the newer protocol.

The [primary preprint methods](https://www.biorxiv.org/content/10.1101/2025.06.09.658412v2.full) place Method 2 in August 2025 onward and describe gene-specific reverse transcription to reduce an A-rich-sequence artifact associated with internal oligo(dT) priming. They describe L6 transfection in one dish and repeated subsamplings, library preparations, and sequencing runs as technical replication. Thus R1–R4 do not establish independent biological replication. The archived L6 sample is dated 2021; identity with the 2026 processed benchmark remains unestablished.

Admission decision: retain the archived data only as an explicitly older, single-biological-sample exploratory resource. Do not claim reconstruction of the current TALE benchmark or validation of Method 2. A sensitivity analysis using previously opened raw prefixes may assess processing choices, but cannot change the frozen screen verdict or solve protocol provenance.

Saved source downloads and SHA-256 receipts use the unique `seers_provenance_*_20260923` prefix under `data/external/research_20260921`. The bioRxiv API returned an empty body and is not scientific evidence. Direct article requests failed with 403/429; methods were available through the search index of the primary page. No access restrictions were bypassed. No per-sequence RNA outcomes, models, or new sequencing files were opened in this audit.

Machine-readable record: `results/research_20260921/seers_updated_data_provenance_20260923.json`.
