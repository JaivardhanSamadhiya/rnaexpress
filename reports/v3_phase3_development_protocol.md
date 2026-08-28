# RNAddress v3 Phase 3 development protocol

**Status:** frozen before any new Phase 3 representation or candidate performance comparison

**Analysis class:** DEVELOPMENT

**Starting commit:** `54fa859ff48b03ddca1d9b15c1f3a46b9b0bfd79`

**Primary seed:** `20260828`

**Seed-stability set:** `20260828`, `20260829`, `20260830`

## Scope and protected-data boundary

Phase 3 asks whether a development architecture can preserve out-of-parent exact-SNV ranking while materially improving selected-edit magnitude, regret and extreme-edit recovery. All 4,395 N-zip SNVs and 15 parents are development data. TDP-43 is post-lock auxiliary development data and can never again be called validation.

Astrocyte outcomes may not be opened, inspected, derived, printed, modeled or used. The fail-closed Astrocyte audit remains active. The exact truthful disclosure remains: Astrocyte outcomes were not inspected, analyzed, recorded, or used for v3 development; an inherited test previously loaded the complete worksheet programmatically, and this deviation was disclosed before v3 model development.

The Moffatt `GSE334718_RAW.tar` archive may not be listed, opened, extracted or used. No Phase 3 program may import either protected outcome source.

## Independent unit and data roles

The independent N-zip unit is the parent RNA, not the individual SNV.

* Primary task: 4,395 exact SNVs from 15 N-zip parents.
* Auxiliary task: 4,566 multi-base TDP-43 motif-complement interventions, including 3,117 finite matched stability deltas.
* Selection units: 15 parents × two directions = 30 parent-direction decisions.
* TDP rows will never be pooled as homogeneous observations in the final N-zip output head.

## Preliminary implementation allowance

Before this protocol, only outcome-free feasibility checks were allowed: model download, checkpoint loading, tokenizer/alignment checks, source hashes, cache inventory and N-zip supplement schema/replicate audit. No new Phase 3 candidate prediction or representation performance was computed.

After this commit, implementation debugging may use shape, finiteness, determinism and synthetic tests. Any outcome-bearing result belongs to the definitive analysis unless explicitly marked as a prespecified representation screen below. The candidate or hyperparameter sets will not be expanded after observing performance.

## Representation candidates

Exactly two contextual families enter the matched benchmark.

### R1 — SpliceBERT.1024nt

The frozen official multi-species checkpoint and exact v2.2 construction are retained. For each length-preserving pair, final-layer mutant-minus-parent hidden states are pooled as:

1. CLS delta;
2. global nucleotide-mean delta;
3. edited-position delta;
4. radius-10 edited-window delta.

The established outcome-free 18-element edit vector is appended for historical continuity.

### R2 — 3UTRBERT 3-mer

Use the author-hosted `yangheng/3utrbert` checkpoint pinned at Hugging Face revision `220d80829deb077d1d640463a4267a96e9e70b1d`. It is a standard 12-layer BERT with a 768-dimensional hidden state and sliding 3-mer vocabulary. DNA sequences are converted to RNA spelling before tokenization.

For aligned SNVs, final-layer mutant-minus-parent hidden states are pooled as:

1. CLS delta;
2. global valid-3-mer mean delta;
3. affected-3-mer delta, where an SNV at zero-based position `p` affects 3-mers beginning at `p-2`, `p-1` and `p` when in range;
4. radius-10 local delta, including 3-mers overlapping the nucleotide interval `[p-10, p+10]`.

The same 18-element edit vector is appended. No layer choice, fine-tuning, alternative k-mer checkpoint or additional radius is allowed.

### HydraRNA exclusion

HydraRNA is not a candidate on this host. Its official extraction stack requires Linux, CUDA 11.8, Mamba, FlashAttention and a custom fairseq installation; this Phase 3 host is Windows and CPU-only. Substituting an unverified implementation would violate exact reproducibility. The exclusion is technical and must not be described as evidence of inferior performance.

## Matched representation benchmark

Each representation is evaluated with the same outer leave-one-parent-out procedure and training-fold `StandardScaler`.

Three targets are fixed:

1. within-parent average percentile, using Ridge;
2. raw `delta_localization`, using Ridge;
3. direction-specific extreme-benefit membership, using balanced logistic regression.

The extreme threshold is the top 10% of beneficial utility within each training parent and direction. Thresholds and labels are constructed only from training parents. Held-out outcomes are never used for scaling, thresholding or calibration.

For Ridge, alpha is selected in inner leave-one-parent-out CV from `{0.1d, d, 10d}`, where `d` is the post-feature matrix dimension. Logistic `C` is selected from `{0.1, 1.0, 10.0}` with L2 penalty and balanced classes. Ties select stronger regularization.

Representation selection score is frozen as:

`0.45 × rank_percentile + 0.35 × (1 - magnitude_normalized_regret) + 0.20 × extreme_oracle_top5_rate`

The representation with the larger outer-parent score becomes the contextual family for Candidates 1–4. A score tie within `0.002` selects SpliceBERT because it is smaller, already cached and historically established.

## Outcome scaling and target policy

No held-out-parent outcome scale may be used. The rank head uses training-parent empirical percentiles. The magnitude head predicts raw localization delta. Robust parent scales may be used only as training-loss weights in an explicitly listed model; no such weighting is in the definitive candidate family.

The direct magnitude family compares only:

* Ridge with squared loss and alpha factors `{0.1, 1, 10} × d`;
* `SGDRegressor(loss="huber", epsilon=1.35)` with alpha `{1e-5, 1e-4, 1e-3}`, at most 5,000 iterations and the current seed.

The loss family and regularization are selected strictly by inner parent-held-out predictions using the frozen selection score. No label clipping or winsorization is allowed.

## Mechanistic feature block

The controlled mechanism block contains interactions, not isolated occupancy claims.

### Motif families

Counts before/after, gain, loss and changed-motif fraction are computed for:

1. TDP-like UG-rich motifs: `UGUGU`, `GUGUG`, `GUAUG`;
2. AU-rich elements: `AUUUA` and `UAUUUAU`;
3. Pumilio-like element: `UGU[ACGU]AUA`;
4. cytoplasmic polyadenylation element: `UUUUAU`;
5. DRACH-like m6A sequence context: `[AGU][AG]AC[ACU]`.

These are sequence motifs, not claimed occupancy. No universal CLIP flag is fabricated for N-zip.

### Local accessibility

ViennaRNA-derived parent, mutant and mutant-minus-parent accessibility are used at the edited base and fixed radii 5, 10 and 20. No radius tuning or global MFE summary is allowed.

### Parent state

Outcome-free parent descriptors are GC fraction, AU fraction, mononucleotide entropy, maximum homopolymer fraction and the five parent motif densities above. Parent descriptors alone are permitted for calibration, but parent-dependent edit action must be represented through the interactions below.

### Prespecified interactions

Only these grouped interactions are allowed:

* motif count delta × parent density of the same motif family;
* motif count delta × parent accessibility at the edited site;
* motif count delta × accessibility delta at radius 10;
* reference→alternate substitution class × parent GC and AU fractions;
* local accessibility delta at radii 5/10/20 × parent GC fraction;
* TDP-stability auxiliary prediction × parent AU fraction.

No all-pairs polynomial expansion or outcome-selected motif panel is allowed.

## TDP stability auxiliary feature

TDP stability is tested only under auxiliary Strategy C: a frozen sequence-to-stability Ridge head is trained on all finite post-lock TDP stability pairs using the selected contextual representation, with alpha fixed to its feature dimension. It predicts a stability delta for N-zip sequences and contributes one optional feature plus its prespecified parent-AU interaction. No TDP outcome enters the N-zip output head, no TDP row calibrates N-zip magnitude, and no measured stability is required at inference.

The stability feature survives only if its grouped ablation improves the outer N-zip selection score by at least `0.002` without worsening normalized regret by more than `0.005`. Otherwise it is dropped.

## Definitive candidate family

Exactly five named candidates are compared.

### C0 — `v2_6_historical`

The committed nested contextual/external stack prediction. It is a fixed reference and is not refit or retuned.

### C1 — `contextual_magnitude`

Selected contextual representation with a direct raw-magnitude head. Directional utility is sign × predicted raw delta.

### C2 — `rank_magnitude_stack`

Separate rank-percentile and raw-magnitude heads. Their outer-training cross-fitted predictions are standardized from outer-training values only. The signed score is:

`w_rank × standardized_rank + w_mag × standardized_magnitude`

with `w_mag` in `{0.25, 0.50, 0.75}` and `w_rank=1-w_mag`, selected inside nested CV.

### C3 — `mechanistic_rank_magnitude`

C2 with the complete prespecified mechanism and parent-state interaction block. The same objective and weight grid are used. No new model family is introduced.

### C4 — `mechanistic_rank_magnitude_extreme`

C3 plus separate increase/decrease extreme-benefit logistic heads. Direction-specific utility is:

`(1-w_extreme) × C3_directional_utility + w_extreme × standardized_extreme_probability`

with `w_extreme` in `{0.10, 0.20}` selected in inner grouped CV.

The inner selection score for every candidate is:

`0.45 × rank_percentile + 0.35 × (1 - normalized_regret) + 0.20 × oracle_top5_rate`

All base predictions supplied to a stack or weight selection are cross-fitted. No in-sample base prediction may train or select a meta-combination.

## Strongest fair forward comparator

The forward family contains:

1. committed grouped forward LightGBM;
2. grouped absolute SpliceBERT Ridge;
3. grouped absolute 3UTRBERT Ridge.

For contextual forward Ridge, train on absolute mutant localization with parent-grouped outer/inner splits, predict each mutant and its parent, and subtract `f(mutant)-f(parent)`. Alpha uses `{0.1d, d, 10d}` inside inner LOPO. The strongest fair forward model is the one with the highest frozen selection score; ties within `0.002` prefer the simpler model, then historical LightGBM.

The metadata comparator is the committed strict grouped `metadata_only` prediction. It is not weakened or redefined.

## Oracle-aware definitions

For every held-out parent and direction:

* oracle rank is the model rank of the measured best utility;
* top-1/top-3/top-5/top-10 recovery indicates whether the exact oracle is in that set;
* raw regret is oracle utility minus selected utility;
* normalized regret divides raw regret by the measured utility range;
* near-oracle recovery means selected utility is at least `worst + 0.90 × (oracle - worst)`.

The oracle identity is never a training target. The 90%-of-range definition is frozen here.

## Nested evaluation and leakage controls

Outer CV leaves one of 15 parents out. Every learned operation on the remaining 14 parents is repeated inside leave-one-training-parent-out CV, including:

* scaling and PCA if used;
* alpha/loss/C selection;
* rank/magnitude weighting;
* extreme threshold construction;
* score standardization;
* representation/forward-family comparison;
* uncertainty reference distributions;
* stacking and confidence calibration.

Foundation-model embeddings are frozen and outcome-free. Their extraction may be cached globally by exact sequence SHA-256. Tests must prove outer-parent labels cannot affect training targets, scalers, extreme thresholds or base cross-fits.

## Primary and secondary metrics

Primary metrics, macro-averaged over parent-direction units unless stated otherwise:

1. directional rank percentile;
2. normalized regret;
3. selected measured utility;
4. oracle top-5 recovery;
5. within-parent Spearman, macro over parents.

Secondary metrics are raw regret, oracle top-1/top-3/top-10 recovery, mean and median oracle rank, near-oracle recovery, meaningful-effect rate using the frozen `0.6758642587586807` absolute log2 threshold, exact random expectations and highest-benefit-decile error.

Parent bootstrap confidence intervals use 10,000 resamples and seed `20260828`. Paired differences, parent medians, number improved, leave-one-best-parent-out and leave-two-best-parents-out are mandatory.

## Negative controls and seed stability

The final candidate is rerun under:

* within-parent shuffled edit scores, seed `20260828`;
* within-parent shuffled labels through the complete nested pipeline, seed `20260828`.

Stochastic heads are rerun with seeds `20260828`, `20260829`, `20260830`. Deterministic Ridge results must be identical. No favorable seed is selected.

## Mechanistic and representation ablations

If C3 or C4 is competitive, grouped ablations are limited to:

1. contextual-only;
2. remove motif interactions;
3. remove local accessibility;
4. remove stability auxiliary feature;
5. remove parent-state interactions.

For the selected representation, the only representation ablations are parent absolute, mutant absolute, full mutant-minus-parent delta, local edited-region delta and combined delta. These are explanatory development analyses, not a route to add a sixth candidate.

## Uncertainty and selective prediction

The confidence score uses exactly five outcome-free signals:

1. rank-versus-magnitude score disagreement;
2. rank/magnitude-versus-extreme-head disagreement when C4 is used, otherwise zero with an explicit missing indicator;
3. selected parent nearest-training-parent contextual distance;
4. selected top-1 minus top-2 utility margin;
5. fold/seed prediction standard deviation.

Each signal is converted to an outer-training empirical support percentile. Confidence is the unweighted mean of support percentiles, with disagreement/distance/variance reversed and margin unreversed. No Phase 3 outcome is used to fit signal weights.

Evaluate the 30 decisions at 100%, 80%, 60% and 40% coverage by retaining the highest-confidence decisions. Report rank percentile, normalized regret, selected utility, meaningful-effect rate and bootstrap uncertainty. No Astrocyte threshold is selected.

Uncertainty is considered development-useful only if confidence versus selected normalized regret has Spearman rho at most `-0.20`, 60% coverage improves regret by at least `0.030` versus 100%, and regret does not worsen as coverage falls from 100% to 80% to 60%. The 40% point is reported but not required to be monotonic because it contains only 12 decisions.

## Frozen Phase 3 gate

The selected candidate must satisfy every core criterion for a **GO**.

### A — rank preservation

* directional rank percentile at least `0.630`;
* no more than `0.005` below v2.6 rank (`0.6358`).

### B — material regret improvement

* normalized regret at most `0.397`;
* improvement of at least `0.030` from v2.6 (`0.4273`).

### C — strongest forward comparator

* rank percentile at least `0.030` above the strongest fair forward;
* normalized regret at least `0.020` lower than the strongest fair forward;
* selected utility at least `0.020` higher than the strongest fair forward.

### D — metadata comparator

* rank percentile at least `0.020` above metadata;
* normalized regret at least `0.020` below metadata.

### E — extreme and near-oracle recovery

* exact oracle top-5 recovery at least `0.10` (at least 3/30 decisions), versus 1/30 for v2.6;
* near-oracle recovery at least `0.20` (at least 6/30), versus 4/30 for v2.6;
* mean oracle rank at most `90`, versus 103.3 for v2.6.

### F — distributed improvement

Define parent composite as `0.5 × rank_percentile + 0.5 × (1-normalized_regret)`, averaging directions. Relative to v2.6:

* median parent gain must be positive;
* at least 9/15 parents must improve;
* mean gain remains positive after removing the best parent;
* mean gain remains positive after removing the two best parents.

### G — controls

* shuffled-edit directional rank percentile at most `0.540`;
* shuffled-label directional rank percentile at most `0.530`;
* neither control may have normalized regret more than `0.020` better than exact random expectation.

### H — seed/optimization stability

Across the three fixed seeds:

* rank range at most `0.015`;
* normalized-regret range at most `0.025`;
* every seed preserves rank at least `0.625` and improves regret by at least `0.020` over v2.6.

### I — complexity and mechanism

Mechanism is retained only if C3/C4 beats C2 in selection score by at least `0.005` and satisfies at least one of:

* rank improvement at least `0.005`;
* regret improvement at least `0.010`;
* top-5 oracle recovery improvement at least one decision (`0.0333`).

If not, C2 is preferred. The extreme head is retained under the same rule relative to C3.

### J — uncertainty

The frozen uncertainty-usefulness criteria above must pass for an unqualified GO. If core A–I pass but J fails, the maximum decision is **CONDITIONAL GO**.

## Decision rules and stop rules

* **GO:** one candidate passes A–J and is not complexity-dominated.
* **CONDITIONAL GO:** A–I pass but uncertainty remains unresolved, or a single non-primary operational issue remains that does not undermine rank, regret, forward superiority or extreme recovery.
* **NO-GO:** no candidate passes rank preservation and material regret improvement, or no candidate beats the strongest fair forward and metadata comparators under distributed robustness.

Do not expand grids, replace metrics, change the 10% extreme threshold, change the 90% near-oracle rule or add candidates after results. A near miss is a failure under this protocol. If no candidate passes, report NO-GO and do not spend Astrocyte.

## Reproducibility outputs

All generated predictions and tables go under `results/v3_phase3/`. Gzip output uses `mtime=0`. The final manifest records source, checkpoint, cache and output SHA-256 hashes; package versions; seeds; row and parent counts; protected-data flags; exclusions and deviations. Expensive embeddings are cached by exact normalized-sequence SHA-256 and accompanied by ordered row-hash arrays.

Phase 3 ends after model selection. It does not authorize Astrocyte preregistration, Astrocyte prediction, Moffatt inspection, UI work or external validation.
