# RNAddress v2.1 stability preregistration

Frozen on 2026-08-27 after the v2 nested, structure and TDP-auxiliary development candidates failed, and before fitting any v2.1 model. TDP-43 locked outcomes and Astrocyte outcomes remain sealed.

## Rationale

The outcome-independent fixed-center factorized architecture produced 0.662 strict LOPO rank percentile, but fold-specific inner hyperparameter selection produced 0.588. The selected configurations varied widely despite only 14 available training parents. This suggests optimization/model-selection variance, but does not authorize using the favorable single seed.

V2.1 tests a variance-reduction method with no performance-based hyperparameter choice: average within-parent percentile ranks from seven predetermined fits of the original fixed-center architecture.

## Frozen method

- Architecture: sequence-only factorized context ranker, bilinear rank 8, hidden width 32.
- Training: learning rate `1e-3`, L2 `1e-3`, 200 epochs, 600 high-versus-low pairs per training parent.
- Seeds: `20260826`, `124347`, `910243`, `451921`, `778103`, `330817`, `602911`.
- Each seed gets an independent deterministic pair sample, parameter initialization and batch order.
- Within each outer parent, convert each seed's scores to percentile ranks from 0 to 1, then average the seven percentile ranks. No seed is dropped or weighted.
- Evaluation: strict 15-parent N-zip LOPO. No hyperparameter or seed selection is performed, so an inner selection layer is not applicable.

## Gate

The original v2 development thresholds remain unchanged: rank percentile at least 0.630; gains of at least 0.030 over strongest forward and 0.020 over metadata; improvement on at least 9/15 parents; positive gain after removing two best parents; shuffled-edit at most 0.540; shuffled-label ensemble at most 0.530.

Only if every criterion passes will complete v2.1 TDP-lock predictions, code, environment and hashes be frozen before opening the 1,006 locked outcomes. This new iteration increases development adaptivity and must be disclosed in any final competition claim.
