# Processing nuisance and motif-accessibility design

Status: full sequence-feature extraction complete. Inner localization fitting
is running; no processing-based outcome exclusion has occurred.

## Processing: nuisance indicators, not a validated splice model

[Dao et al.](https://doi.org/10.1038/s41467-025-62000-9) motivate treating cryptic
reporter splicing as a possible confound. This is not evidence that any particular
RNAddress intervention is mismeasured. Full reporter/intron architecture is not
available in the certified sequence fragments, so a genomic splice predictor is
not silently applied outside its validated context.

The eight paired nuisance summaries are changes in strict donor and acceptor
consensus densities, two PAS densities, AU-rich-element density, maximum local
CU fraction, maximum local U fraction, and total U fraction. The
[splice-consensus source](https://pmc.ncbi.nlm.nih.gov/articles/PMC86117/) and
[experimental polyadenylation-signal study](https://pmc.ncbi.nlm.nih.gov/articles/PMC307082/)
support motif categories, not the predictive calibration of this implementation.
Strict consensus matches have low sensitivity; lack of a match is not evidence
of absent splice risk. Branchpoint inference is excluded because the relevant
donor/intron context is unresolved. No row is deleted by extraction. Comparison
of nuisance adjustment with a prospectively defined warning/abstention strategy
must take place inside training/inner-validation folds, with unfiltered outer
results retained.

## Compact externally chosen motif block

Four motif categories are fixed in the versioned configuration before model
evaluation: [PUM-family UGUANAUA](https://pmc.ncbi.nlm.nih.gov/articles/PMC3196106/),
[QKI ACUAAY core](https://pmc.ncbi.nlm.nih.gov/articles/PMC3983035/),
[MBNL YGCY](https://pmc.ncbi.nlm.nih.gov/articles/PMC2853123/) and a short
[UG-repeat proxy](https://pmc.ncbi.nlm.nih.gov/articles/PMC3643599/). The UG repeat
length of three is an explicit engineering summary, not an experimentally
validated binding threshold. Motif matches do not establish protein specificity.

For each reference and mutant reporter fragment, use the same ViennaRNA settings
as the local-structure block, now folding the entire supplied fragment. Count
overlapping motif matches, and weight each match by mean marginal unpaired
probability across its bases. Normalize sums per 100 input nucleotides and take
mutant-minus-reference differences: four count-density deltas plus four exposure-
density deltas. This is eight compact features, not thousands of interactions.

These are site-specific **marginal** accessibility proxies, not the probability
that an entire binding site is simultaneously unpaired, calibrated RBP occupancy,
or an in-cell structural measurement. Structure/model/configuration/sequence
hashes identify the cache. Both count and exposure blocks need separate knockout
tests before any mechanistic interpretation. Full extraction completed all
72,998 unique fragments and produced a 62,665 × 8 float32 matrix, SHA-256
`a11c53563bd3c6fd7e4b645fba8c86bf217214615bfdd3c5b0c72ea3ebc54d0e`.
The processing matrix is independently hashed as
`40a7ccbff17ab6f5b2af70e5cbe84931d4681d7e26828bdf4728eb91e3a0fc39`.
Biological necessity remains untested. Covariate versus flag/abstention evaluation
is prospectively specified in the localization design; it may not replace the
full-cohort primary result with a selected favorable subset.
