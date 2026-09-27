# Bounded SRLE candidate-recommendation prototype

`predict_edit_candidates.py` is an outcomes-free **replay of frozen held-out predictions**, restricted to complete original SRLE candidate sets. It demonstrates the computational interface; it is not inference for new RNAs, a biological design generator or an individually calibrated recommendation service. Generalization beyond the one HBB reporter context is not established.

The default 1–3-mer model has the best frozen regret point estimate; 2-mer has the best strict-purge quantitative effect error. Their ranking/risk difference is not statistically resolved. Pass `--model 2mer` for the quantitative comparator. Both directions are supported. Sequences are six-base A/C/G/U or A/C/G/T strings, normalized to uppercase T identifiers. The candidate file is one sequence per line or CSV with `candidate`/`sequence` column. The supplied list must equal the complete measured set; new parents/candidates, subsets and duplicates are refused.

From `D:\rnaexpress`:

```powershell
& 'C:\Users\jaisa\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' predict_edit_candidates.py --parent AACGCC --candidates artifacts/srle_synthesis_20260926/increase_success_AACGCC_candidates.txt --direction increase
```

Output JSON lists each candidate's predicted effect, rank, recommendation flag, changed positions, model, domain status and explicit uncertainty scope. Scores are original purged held-out scores; their differences are checked against frozen coefficients. The runtime bundle contains no individual published/replicate outcomes. Aggregate historical wrong-both risk is labeled as cohort information, not the candidate's probability. No exploratory confidence cutoff is deployed. Rankings are forced even when all predicted effects oppose the requested direction; users must not read `recommended` as a guarantee of that direction.

The command above selects **ACCGAC**. Its published effect is +0.05060 and constituent effects +0.19662/+0.20478, yet its published normalized regret is 1.00. “Success” here means correct direction in both constituents, as fixed by the example rule; it does not imply best published candidate. This distinction is intentionally visible.

All four predetermined demos are in `results/srle_synthesis_20260926/prototype_demo_outcomes.csv`:

| Parent | Direction | Selected candidate | Example stratum |
| --- | --- | --- | --- |
| AAAGTC | decrease | AAATGC | correct in both constituents |
| AGCACT | decrease | GACACT | wrong in both constituents |
| AACGCC | increase | ACCGAC | correct in both constituents |
| AATACA | increase | TAAACA | wrong in both constituents |

Their `*_candidates.txt` and `*_prediction.json` files are in `artifacts/srle_synthesis_20260926/`. Reveal measurements only from the separate demo outcome table. The complete analysis includes every candidate set, not just these illustrations. Prototype verification reproduced all 2,368 frozen decisions for 592 anchors × two directions × two models. The SHA-256 manifest detects runtime-bundle changes, and the final evidence package pins both bundle and code.

`--output <unused.json>` writes a new file exclusively and refuses to overwrite an existing result. No files are written by default. Runtime uses Python's standard library; preparation/analysis uses the existing bundled scientific environment. Scoped tests cover domain rejection, U/T normalization, complete-roster enforcement, order/direction behavior, overlapping feature counts and coefficient identities.
