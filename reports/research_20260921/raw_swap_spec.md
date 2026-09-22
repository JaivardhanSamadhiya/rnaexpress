# AI-authored fixed-edit replicate consistency check

Post hoc specification after raw score correlations were inspected. Preserve
the previously written robustness_swap_predictions.csv selections exactly;
do not refit, reselect, or search for favorable edits. Use only the documented
forward orientation and the previous raw-count eligibility threshold.

Retain a parent only if it and ALL previously eligible held-out single-swap
candidates pass the >=20-fragment threshold in all four libraries. Reconstruct
the same held-out candidate list from the original partition; assert its count
and selected membership agree with every stored selection record. Evaluate the
stored chosen sequence separately against each replicate's NRS. Compute oriented
NRS change and regret gain over uniform selection, both directions symmetrically.
Average directions/parents within exact composition, then compositions equally.
Bootstrap whole composition classes (2000 draws, seed 20260921), keeping both
replicates and all model predictions together. Also report each direction and
paired pair-model-versus-1–3-mer regret differences.

These measurements test whether an aggregate-derived selection remains useful
in its constituent replicates. They cannot serve as independent validation.
Report all comparators even if the pair model loses. Do not advertise a new
biological mechanism or a universal edit selector.
