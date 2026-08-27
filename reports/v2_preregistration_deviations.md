# RNAddress v2 preregistration deviations

## 2026-08-26 — first-pass fixed-center screening

Recorded before fitting a v2 model or generating any v2 outer-fold prediction.

The first development pass uses the prespecified grid-center configurations for `factorized_context_ranker`, `context_lambdamart`, and `forward_lightgbm` rather than running the full nested grid. This is a compute-screening pass: bilinear rank 8, hidden width 32, learning rate `1e-3`, L2 `1e-3`; LambdaMART/forward LightGBM use 15 leaves, 30 minimum child samples, learning rate 0.03 and 300 trees.

No fixed value was chosen from v2 performance. All predictions remain strict outer leave-one-parent-out. If no custom candidate approaches the frozen gate, the expensive nested grid is scientifically uninformative and will not be used to search for a lucky configuration. If a candidate approaches or passes the gate, the full inner-parent selection required by the preregistration will be run and only those nested predictions can authorize the TDP-43 lock.
