# Post-hoc SEERS read-quality sensitivity audit

AI-authored technical specification, 23 September 2026. The frozen Q30-both-mates
screen failed its coverage requirement (5 eligible groups rather than 20) and
remains inconclusive. This is a diagnostic on the SAME already-open RNA prefixes,
not an enlargement, replacement gate or independent confirmation.

Keep all 241 candidate sequences and predictions from ff42592. Never fit a target
model or reverse a sign. Read only the existing 16 MiB prefixes of HRR1883393 and
HRR1883401, both mates; verify receipt hashes. Fixed sensitivity levels are
minimum insert-base Phred 0, 20, 25 and 30 in each mate. At every level require
exact left and right anchors, exactly 45 unambiguous bases, synchronized mate
IDs, and identical insert calls. These are paired-concordance counts, not exact
reproduction of the author's NGmerge pipeline. No download or new RNA access.

Report count-retention rates and eligible groups at each level using the original
ten-reads-per-fraction and five-candidates-per-group rules. Calculate every frozen
predictor's regret for each level, with 5,000 descriptive group bootstrap draws
seed 20260923, and report the same primary comparisons. Do not promote a quality
threshold into a new primary analysis or call a favorable sensitivity positive
confirmation. Counts and metrics at Q30 must reproduce the existing screen.

For comparison without changing candidate sets, additionally retain exactly the
25 sequences in the five originally eligible Q30 groups and evaluate all levels
on that fixed cohort. Report Q20/Q30 endpoint Spearman over all 241 candidates
and descriptively compare Q30/Q20 retention fractions across sequences and
between nuclear and cytoplasmic libraries. PCR/read observations are not
independent biological replicates. No formal biological significance claim.
