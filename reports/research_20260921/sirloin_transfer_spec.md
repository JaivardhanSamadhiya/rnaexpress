# AI-authored external-assay pilot specification

Written after source/paper/schema/sequence inspection, before reading localization
outcome cells. Prior published qualitative findings are known; this is not an
outcome-naive discovery of SIRLOIN biology. This is a new external pilot, not a
replacement for the failed neuronal transfer or any historical gate.

Use publisher Dataset EV1, NucLibC only. All 4,205 workbook sequences exactly
match the authors' FASTA by ID; none exactly match the certified historical
development sequences. Exclude FASTA-only entries. Restrict to verified single
substitutions of Jpx_9 (162) and NICN1_53 (65). NICN_53 mutant IDs refer to the
NICN1_53 WT; verify Hamming distance directly, not by assuming the ID is correct.

Task: choose a position for a specified base substitution within a fixed parent.
All candidates in each parent x reference-base x alternative-base decision set
have identical mononucleotide composition and edit cost. Require >=5 candidates
with finite replicate-1 and replicate-2 outcomes and a finite WT in both. At
least 6 decision sets per parent must survive for an adequate two-parent pilot.
These sets are not independent genes; do not bootstrap them as biological units.

Freeze predictions before outcomes. Primary: mean of the existing SRLE
1–3-mer model's predicted NRS over all overlapping six-mers of each 109-nt tile.
Secondary source scores: mean published six-mer NRS and mean positional-pair
model predictions. Positive means more nuclear, as in both assays. No fit,
recalibration, sign search, or window search on SIRLOIN. Source model predictions
are exactly those already saved in robustness_predictions.csv.

Baseline scores: count overlapping CCC; count overlapping CCTCCC (the published
SIRLOIN core binding sequence); composition-only/lexical tie baseline. No target
fitting. Evaluate high and low nuclear-enrichment selection symmetrically, with
lexical sequence ties. Compute normalized regret separately per replicate, then
average directions, classes within parent, and parents equally. Report oriented
change from WT and all model/baseline results. All comparisons use identical
candidate sets. Save selected IDs before any confirmation data are read.

Discovery gate (Rep1/2 only): adequate classes in both parents; primary mean
regret advantage >=0.05 over EACH of CCC and CCTCCC; positive advantage over
both baselines separately for EACH parent and EACH replicate. This is a practical
pilot screen, not a significance test. No statistical claim across populations
is possible from two parent contexts.

Only if that gate passes, evaluate the same fixed candidate sets and choices on
Rep3/4 with the same advantage criteria. Missing confirmation values cause the
affected class to be excluded without reselection; >20% lost classes makes
confirmation inadequate. Otherwise Rep3/4 and all NucLibB outcomes remain closed.
If discovery fails, retain the failure and do not search alternate scoring signs
or windows. Any new hypothesis requires a separately justified dataset/design.
