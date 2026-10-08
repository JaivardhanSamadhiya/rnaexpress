# G-quadruplex backend feasibility, synthetic only

The existing ViennaRNA2.7.2 backend supports a **global modeled probability of
at least one intramolecular GQ** under the declared ordinary/GQ ensemble. This
is a computational feasibility result, not a positive localization result or
evidence of folded GQs in cells. No project alleles, outcomes, feature values,
models or fits were accessed. Project feature production remains unauthorized.

## Why the global ensemble ratio is justified here

The exact official v2.7.2 tree is
`1ffec79f5e258896160f7362ced8263450f371dc`. Thirty inspected text files have
SHA256 receipts and independently verified Git blob identities. The ordinary
parameter generator does not condition on `md.gquad`; its copied model flag
controls the recursion only. The exterior recursion retains its ordinary stem
and unpaired terms and adds a nonnegative GQ term. The internal-loop recursion
adds a GQ alternative after its ordinary contributions. The multiloop recursion
likewise adds a GQ stem contribution. This is source-based reasoning establishing
that GQ-free states keep their original weights under this unconstrained linear
single-sequence model. [Parameter generator](https://github.com/ViennaRNA/ViennaRNA/blob/v2.7.2/src/ViennaRNA/params/params.c),
[exterior](https://github.com/ViennaRNA/ViennaRNA/blob/v2.7.2/src/ViennaRNA/partfunc/pf_exterior.c),
[internal](https://github.com/ViennaRNA/ViennaRNA/blob/v2.7.2/src/ViennaRNA/partfunc/pf_internal.c),
[multiloop](https://github.com/ViennaRNA/ViennaRNA/blob/v2.7.2/src/ViennaRNA/partfunc/pf_multibranch.c).

Write Z_on = Z_off + Z_GQ, where Z_GQ sums extended-model states containing one
or more GQs. With G=-kT log Z, P(at least one GQ)=1-Z_off/Z_on equals
`-expm1((G_on-G_off)/kT)`. Use the native `exp_params.kT/1000` (0.6163207755
kcal/mol at37C), not an independently rounded gas constant. Native returned
ensemble energies remove their numerical partition scaling, so different MFE
rescaling factors do not invalidate the ratio. Raw scaled partition matrices
must not be divided directly. This inference requires the identical ordinary
parameters/constraints and the added nonnegative grammar above. It does not
extend automatically to arbitrary constraints or other models. [Global PF
source](https://github.com/ViennaRNA/ViennaRNA/blob/v2.7.2/src/ViennaRNA/partfunc/partfunc.c),
[official partition probability definition](https://www.tbi.univie.ac.at/RNA/ViennaRNA/refman/partfunc/thermodynamics.html).

This event is global. It is not a site's occupancy or expected number of GQs.
The synthetic two-disjoint-GQ case has modeled event probability1 but expected
count almost2. The ordinary base-pair matrix is not used to infer GQ occupancy.

## Native checks and resource benchmark

The corrected18 synthetic tests passed. A broader audit checked636 exhaustively
enumerated ordinary structures on four invented sequences: all evaluated
ordinary energies were exactly identical with GQ on/off. Twenty-one exposed
ordinary scalar/list parameter fields were exactly equal; nine opaque SWIG
tables were **not compared by value**. Their flag independence relies on the
inspected source plus the native ordinary-energy checks. The initial pointer
address comparison failure and its correction are preserved in
`implementation_incident.md` and the first diagnostic receipt.

Seven A/G-only synthetic sequences admit no ordinary AU/CG/GU pairs. An
independent complete enumeration of admissible GQ boxes, followed by a separate
nonoverlapping-state partition recurrence, reproduced native ensemble energies
and event probabilities at the declared absolute2e-6/relative2e-5 tolerance.
Cases include zero/one/two GQs, disrupting substitutions, three layers, long
linkers and32 consecutive Gs (21,186 admissible boxes). This independently
checks global-state summation while using native GQ elementary Boltzmann weights;
it is not an independent experimental energy calibration. [GQ elementary
enumeration/source](https://github.com/ViennaRNA/ViennaRNA/blob/v2.7.2/src/ViennaRNA/partfunc/pf_gquad.c).

Twelve invented all-A/mixed/variant contexts covered46/150/190/260nt. GQ-off
energy matched the exact original NEXT helper with zero error. Turning ordinary
probability-matrix calculation on/off also gave zero energy error for both
ensembles. The invented parent/mutant delta obeyed exact no-edit zero and
reversal antisymmetry. Fixed NEXT settings remain Turner2004,37C,dangles2,
minimum loop3, GU pairs/closures allowed, linear monomer, salt1.021M,
unrestricted pair span and betaScale1.

An additional fixed15-case one-GQ linker-length roster used the stable exact
reference `w/(1+w)` and `-kT*log1p(w)`. Maximum absolute event error was
7.5128928634e-9. Five very rare positive event masses rounded to zero in the
native energy ratio. Therefore absolute precision passed; relative accuracy of
very rare events is not certified. Do not interpret tiny zeros as proof that
the modeled event is mathematically impossible.

| Input length | Slower sampled mean, two ensembles per invented allele |
| --- | ---: |
|46|0.03250s|
|150|0.15313s|
|190|0.36614s|
|260|0.41126s|

One CPU, one existing native runtime, three timed repetitions per all-A/mixed
case. Applying the slower sampled mean to the previously recorded length counts
742/9318/3991/4169 (18,220 total) gives **77.1 minutes folding only**, or115.7
minutes with50% margin. These are estimates from a tiny synthetic roster under
current contention, not guaranteed wall time; they exclude cache birth hashing,
IO, production checks, feature assembly and model work. No project production
was run and no new dependency was installed.

## Provenance, prior art and remaining admission boundaries

The cached RNA wrapper/native files and distribution metadata exactly match
their installed wheel RECORD hashes. Native PF uses double precision internally.
Wrapper SHA256 is
`a8dab82efec718e2c5bc77767ff17f1f9b91bbfcabb2313ffe4ced1855389406`;
native pyd SHA256 is
`f4527b33266412fbe23b1bc49ddb422693a5d81c3c784c69d8e2ba3d7642b7c2`.
This establishes the admitted cached version/API and synthetic source-rule
parity; the binary was not rebuilt from the inspected source. Free research
use is allowed by the package's attribution/no-fee-redistribution terms.
[Official COPYING](https://github.com/ViennaRNA/ViennaRNA/blob/v2.7.2/COPYING).

Old project v2 already includes normalized overlapping GGAGG counts,
G{3,} run counts and maximal25nt A/G richness in
`src/modeling/v2_features.py`; `reports/v2_rescue_preregistration.md` declared
G-quadruplex-like sequence summaries. GQ/stem competition was already proposed
in this campaign's literature notes. Thus neither G-rich conditioning nor this
known thermodynamic method is novel. The current audit establishes a usable
backend distinction from those raw sequence summaries only.

Vienna's known GQ energy model uses stacked layers and total linker length,
omitting linker identity/asymmetry and orientation. Its GQ table does not gain
a measured cell-specific potassium/protein/helicase state from the ordinary
salt setting. [Official tutorial](https://github.com/ViennaRNA/ViennaRNA/blob/v2.7.2/doc/source/tutorial/RNAfold.rst),
[Lorenz et al.2013](https://pubmed.ncbi.nlm.nih.gov/24334379/).
Neuronal localization papers provide prior mechanism hypotheses, not a new
universal mechanism or proof of this project's endpoints. [Subramanian et
al.2011](https://pmc.ncbi.nlm.nih.gov/articles/PMC3128965/),
[Goering et al.2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7279889/).
Guo/Bartel2016 found potential GQs overwhelmingly unfolded in the tested
eukaryotic cells; any future feature concerns **modeled isolated equilibrium
folding potential**, not observed in-cell occupancy or mechanism.
[Guo/Bartel2016](https://pmc.ncbi.nlm.nih.gov/articles/PMC5367264/).

Root must independently review these source/probability/precision limits, then
declare and freeze any project input, feature, matched raw/ordinary controls,
evaluation grid and gate before extraction or fitting. Whole mature reporter
processing and cellular state remain unknown; SRLE46 is a HBB-vector junction,
not natural full HBB3UTR. Existing negative verdicts and frozen artifacts remain
unchanged. Backend failure or numerical limitations are not negative biology.
