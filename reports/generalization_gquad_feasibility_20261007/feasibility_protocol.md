# Synthetic G-quadruplex backend feasibility declaration

Declared 7 October 2026 before this namespace's native synthetic folds. This is
an outcome-free backend audit, not a feature-production or model-fitting freeze.
No project allele, label, model or feature array may be opened by this namespace.
No project extraction, fits, installs, paid compute or outcome-driven tuning.
Only invented sequences and the existing ViennaRNA 2.7.2 runtime are used, at one
CPU thread. All outputs are additive and immutable after their first write.

The question is whether enabling intramolecular G-quadruplexes in the global
partition function preserves every ordinary structure and its original weight.
If source inspection plus numerical checks establish this nesting, then
Z_on = Z_off + Z_at_least_one_GQ, and the modeled probability of at least one GQ
is 1-Z_off/Z_on = -expm1((G_on-G_off)/kT). Without nesting certification, report
only the ensemble-energy contrast, never label it a probability. This global
event is neither a local occupancy measure nor a sum of ordinary base-pair
probabilities. A single ordinary base-pair probability matrix cannot certify it.

Fix the original NEXT model: explicit RNA Turner2004, 37 C, dangles2,
minimum-loop-size3, GU pairs/closures allowed, linear monomer, salt1.021 M,
unrestricted maximum ordinary-pair span, betaScale1. Only gquad0/1 differs.
Compute_bpp0/1 parity and native exp_params.kT are audited; numerical scaling is
accounted for rather than equating raw scaled partition matrices across runs.
No hard/soft constraints, probing data or protein binding terms are introduced.

Before any broader inference, inspect exact tagged official source and cached
wrapper/native identities, record source SHA and runtime hashes, and test:

- no-G negatives, an ordinary hairpin, and deliberately designed two-/three-layer
  GQ-positive sequences, variants disrupting G-runs, and stem competition;
- equal-length parent/mutant synthetic pairs, exact no-edit zero and reversal
  antisymmetry of the energy/event-measure deltas;
- short exhaustive ordinary-structure weight equality when gquad toggles, plus
  independently enumerated GQ-only-state partition sums where feasible;
- synthetic contexts at all four available input lengths46/150/190/260,
  independent gquad-off parity against the original NEXT partition helper,
  finite nested energies and fixed numerical bounds;
- small one-thread timing benchmark with no project feature production.

Declare numerical tolerances before folding: ordinary energy equality1e-6
kcal/mol; PF energy/API parity absolute1e-6 plus relative1e-6; independent
Boltzmann sums/event probability absolute2e-6 plus relative2e-5; probability
roundoff bounds[-2e-6,1+2e-6]. Any genuine failure remains recorded and blocks
that claim. Tolerances are not changed in response to outcomes. A backend or
resource failure is not a negative biological result.

Historical v2 already contains normalized GGAGG counts, G{3,} run counts and
maximal25nt A/G richness. These are prior sequence summaries, not equilibrium
GQ/stem competition. This audit is not a new GQ method or biological discovery.
ViennaRNA uses a simplified known GQ energy model. Neuronal GQ localization
papers motivate only a hypothesis; widespread in-cell unfolding reported by
Guo/Bartel2016 prevents treating modeled equilibrium folding potential as actual
in-cell GQ occupancy or transport mechanism. The exact available sequence may
not represent the whole mature reporter; SRLE46 is a HBB-vector junction.

Root review is required before any separate project-production/feature/gate
design. This declaration authorizes synthetic feasibility only.
