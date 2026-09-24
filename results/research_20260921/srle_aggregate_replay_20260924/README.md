# SRLE measured-swap result: aggregate arithmetic replay

Technical evidence package, 24 September 2026. AI-assisted implementation and
documentation; the student must independently understand, reproduce and interpret
the research. This is not a competition submission or a claim of complete novelty.

## What this reproduces

Run `python replay.py` from this extracted folder using Python 3.12, or pass its
directory to the script. No third-party packages, network, model fitting or raw
sequence-level data are needed. The script verifies each package member against
integrity.json, checks cohort completeness and balance, recalculates the archived
means and descriptive intervals, and compares them to expected_summary.json with
absolute tolerance 1e-12. A successful run prints `"status": "PASS"`.

In this project use the bundled interpreter:

```powershell
& 'C:\Users\jaisa\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -u replay.py
```

The archive holds aggregate records only. It reproduces summary arithmetic; it
does not reproduce the original fit, candidate construction, raw-read counting
or sequence-to-measurement mapping. No sequence candidates are supplied here.
The original hash-pinned research artifacts remain in the repository. A local
file manifest detects modification, but cannot establish authenticity if both
the manifest and its inputs are replaced. The separately committed ZIP receipt
provides the expected release SHA-256.

## Estimand and units

Original choices were made among measured six-mers differing by a swap of two
unequal bases, preserving nucleotide composition. For a fixed parent, candidate
set and direction d (1 for increasing nuclear retention; -1 for decreasing),
oriented outcome is z = d times the reconstructed NRS score. Normalized regret
is (maximum candidate z - selected z) / (maximum z - minimum z). Uniform regret
uses the mean candidate z. Reported gain is uniform regret minus selected regret;
positive gain is better. Uniform regret need not equal 0.5 for an individual set.

Directed NRS change is d times (selected score - parent score), on the original
log2 assay-score scale. It is distinct from normalized regret, and neither is
the proportion of RNA molecules in a compartment. NRS depends on the assay's
normalization and is not a direct cellular fraction.

There are 592 retained parent neighborhoods in 60 composition classes, four
models, both directions and two reconstructed constituent replicates. Seventeen
low-count neighborhoods were excluded in the archived analysis. Each aggregate
row stores its record count and two means. Each composition class receives equal
weight; models, replicates and directions must have identical cohort counts.
Parent and selected sequences, and composition strings, are omitted from this
package. Numeric class IDs retain the original sorted class order.

The file bootstrap_indices.csv stores exactly 2,000 draws of 60 classes generated
with NumPy default_rng(20260921), retaining common indices across models. The
standalone replay uses those saved draws and linear-interpolation quantiles.
It does not search seeds or redefine uncertainty. Confidence intervals are
descriptive composition-class bootstrap intervals conditional on the existing
training and decisions. They do not include full training-sample uncertainty.

## Retained results

| Model | Replicate 1 regret gain | Replicate 2 regret gain |
| --- | ---: | ---: |
| Composition / deterministic tie choice | approximately 0 | approximately 0 |
| Position additive | 0.12186 | 0.07761 |
| Short motifs, 1-3-mer counts | 0.21991 | 0.22129 |
| Position pairs | 0.23103 | 0.25342 |

Position-pair intervals are [0.16399, 0.28942] and [0.19643, 0.30735]. Short-motif
intervals are [0.15269, 0.28093] and [0.15840, 0.27969]. Pair-minus-short-motif
intervals cross zero: [-0.04352, 0.06848] and [-0.02379, 0.09397]. No superiority
of the pair model is established. Pair-model directed NRS changes are 0.11572
and 0.11962 log2-score units. Exact values and direction-specific gains are in
expected_summary.json and the replay output.

The aggregate training labels already incorporated these constituent experiments.
The raw work is an independent counting implementation, not independent biological
validation. Candidate neighborhoods overlap within composition classes. A held-out
six-mer is not a held-out endogenous transcript or gene. Strong short-motif
controls work similarly. Keep the failed external transfer tests visible in
evidence_ledger.md; this package changes none of their decisions.

## Provenance and limits

Source study: [Zeng et al., SRLE-seq](https://pubmed.ncbi.nlm.nih.gov/42179915/).
The published screen, motif discovery and localization prediction are prior art.
This package is a reproducibility aid for a retrospective decision benchmark.
It establishes neither a new predictor nor a biological mechanism.

provenance.json records hashes of the original decision table, summary, freeze
and subsequent checkpoint. The original raw-swap freeze omitted one actual input,
robustness_predictions.csv, and imported modules. The later checkpoint includes
the input hash and it still verifies, but this does not retroactively make the
earlier freeze complete. The old freeze is preserved unchanged.

The unresolved source issues include the published table-generation provenance
and replicate-3 identity. A first-prefix overlap was recorded for replicate 3 and
a different library; this is not a full-file duplication finding. The package
does not use that third replicate. No claim of universal transfer, endogenous
control, therapeutic effect, independent confirmation or STS competitiveness is
supported by an arithmetic replay.
