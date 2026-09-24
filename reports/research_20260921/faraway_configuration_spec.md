# Fixed intron-configuration selection experiment

AI-authored pre-outcome specification, 23 September 2026 local date. This new
experiment uses the independent public Faraway et al. 2025 reporter library.
The paper's aggregate mechanisms are already known; no claim of new biology or
new machine-learning methodology is made. Existing failed gates remain closed.

Question: can dependence on the synonymous sequence improve selection among
tested intron configurations, beyond a universally preferred intron pattern?
Every candidate panel has four introns and an identical designed mature RNA
sequence and encoded protein. Each site has its own intron identity and length;
configuration effects cannot be attributed to physical position alone.

Only Supplementary Table 3, transfection_1 (16-hour transient transfection), is
admitted. Read CPM nucleus/cytoplasm and nc_ratio only for explicitly whitelisted
rows. Verify positive finite CPMs and ratio agreement; fail on inconsistency.
The other experiment sheets, stability values and confirmation rows remain closed.
The table is the author's processed/filtered data, not a reconstruction from raw
UMIs. Three replicate labels are retained; barcode replicates are not independent
genotypes or genes. Generalization is within one synthetic protein context.

The ordered fragments, not the discrepant GA-poor example sequence, define the
design. Unique minimum-edit exon excision reconstructs a 545-aa shared protein.
DeO fragments 1 and 7 have a linked synonymous exonic change in their intron-bearing
versions. Hold those intron statuses fixed whenever the relevant GA bit is DeO;
within each resulting panel the reconstructed mature RNA is exactly identical.
This is design-based reconstruction, not raw-read validation of every construct.

Partition the 125 eligible GA patterns by SHA256 of
`faraway-placement-20260923|` plus the 8-bit GA pattern. First 25 are confirmation,
next 25 development, remaining 75 training. All 131 GA patterns without an eligible
four-intron panel also train. All rows for a GA pattern stay together, including
all barcodes and intron patterns. Metadata yields 206/25/25 GA patterns and
93/26/33 eligible panels in training/development/confirmation. Eligibility requires
at least five distinct four-intron genotypes per exact-mature-RNA panel.

Outcome per barcode/replicate is log2(nucleus/cytoplasm). Average barcodes equally
within genotype/replicate, then average the three replicates for training only.
Center both target and feature columns within each exact-mature-RNA panel in
training, removing RNA-specific intercepts. Weight each GA pattern equally across
its genotype rows. Standardize centered feature columns on training rows only,
without subtracting another intercept; use weighted Ridge without intercept.

Primary `interaction`: 8 intron-presence bits, their 28 pair products, and all
64 products of a GA bit and an intron bit (100 features). Controls are `additive`
(8 intron bits), `quadratic` (36 intron-only features), and `pattern` (256 one-hot
intron-pattern indicators, allowing an arbitrary common preference over complete
patterns). All controls use identical labels, centering, weighting and tuning.
Random selection has exactly expected two-direction normalized regret 0.5.
Mature-sequence scores, including global GeRM and GA counts, cannot distinguish
these within-panel choices; number-of-introns scores also tie.

Choose alpha independently for each model from 0.1, 1, 10, 100, 1000 by fivefold
cross-validation of training GA patterns, hash ordered using
`faraway-inner-20260923|`. Minimize mean within-panel-centered squared error,
averaged equally across GA patterns. Ties choose larger alpha. No development
outcomes inform model fitting, tuning, filtering, feature selection or signs.
Generate and commit predictions before opening development outcomes.

Evaluate only predeclared four-intron candidate rows. All candidates must have
valid outcomes in all three replicates; after exclusions require five candidates
and a nonconstant outcome in each replicate. Select maximum and minimum predicted
localization, averaging outcomes over exact prediction ties. Compute normalized
regret per direction, then average directions, panels within GA pattern, GA
patterns, and replicates equally. Preserve every comparison and exclusion.
Bootstrap whole GA patterns 5,000 times, seed 20260923. These are descriptive
intervals over engineered sequence patterns, not independent genes or a new
biological study; training uncertainty is omitted.

Development promotion requires at least twenty eligible GA patterns, primary
regret improvement >=0.03 over EACH additive, quadratic, pattern and random
control, every paired interval lower bound >0, and positive gain in each of the
three replicates against every control. Only if all pass may the frozen model
score confirmation under the identical rules. Failure keeps confirmation closed.
No post-result threshold adjustment, favorable subgroup promotion or model search.

Freeze code, tests, specification, input checksums and partition before any
localization values are parsed. Commit the prediction record before evaluation.
The single-protein setting, genotype relatedness, linked intron identities and
processed-table provenance limit the interpretation even if the gate passes.
