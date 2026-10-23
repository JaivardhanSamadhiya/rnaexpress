# Deferred numerical companion for the joint known-cell design

Prepared 22 October 2026. This additive namespace implements numerical function source for the frozen `generalization_knowncell_joint_design_20261009` and its tested `generalization_knowncell_joint_implementation_20261022` reference layer. It has no scientific imports, runtime bootstrap, project reader, sampler, selector, checkpoint writer, campaign runner or gate. This preparation opens source and summary receipts only. It does not authorize native numerical execution or project input admission. Existing scientific resource guards, data, models, gates and source remain unchanged.

The scope remains an exposed known-cell, held-gene reassessment of existing linear methods. No method novelty, unknown-cell transfer, independent biological confirmation or actual benefit is claimed.

## Frozen callable interface and equations

All scientific objects are explicit deferred arguments. Future authorized callers must supply their independently admitted NumPy module, SciPy `minimize` and SciPy `expit`; this source never imports those libraries. The interfaces are:

```
prepare_training(np, x, left, right, labels, weights, cells) -> prepared
objective_value_gradient(np, expit, arm, theta, z, y, w, signs, penalty)
fit_prepared(np, minimize, expit, prepared, arm, config) -> model
canonical_scores(np, model, full_validation_x, cells) -> scores
```

`x` has exactly102 original columns and a fixed row order. `left/right` are the original unique, unordered source-pair index arrays, supplied without filtering or resampling. Labels are ±1 and weights are strictly positive with total1 and cell mass1/2 each. CAD signs are+1; literal Neuro-2a signs are−1. Metadata, original truth differences and complete per-context pair identity require the separately admitted reference preference contract. This numerical layer cannot certify those biological/provenance facts from arrays alone.

`prepare_training` computes the common source pair differences, weighted RMS with no centering, active support RMS>=1e-8, scale equal to RMS when active and1 otherwise, and a102-element zero mean. Pair columns with unsupported RMS are explicitly zeroed. The returned dictionary contains native `z,labels,weights,signs` arrays, serializable `scaling={pair_rms,scale,active,mean}`, and training row/pair counts. All arms must receive the same independently hashed prepared inputs. No cell-specific scale or alternate support threshold is permitted.

Pooled minimizes sum(w logistic(−y zβ))+λ/2||β||². Joint minimizes sum(w logistic(−y z(β+cδ)))+λ/2(||β||²+10||δ||²). Independent is two conditional cell objectives with2w andλ/2||u_cell||², equivalent to the global weighted loss plusλ/4(||u_CAD||²+||u_Neuro-2a||²). One common lambda config is passed to both independent heads. The public objective function implements that global half-sum representation for comparison against the frozen scalar reference. The fitter instead makes two conditional102-coordinate calls. There is no extra head, group-residual solver, intercept, multiplier search or cell-expression substitution.

The original source `src/cross_assay_20260927/models.py:optimize` is read as text and pinned, not imported. Its optimizer convention is preserved: L-BFGS-B, `jac=True`, zero initial values, `maxiter=500`, `ftol=1e-11`, `gtol=1e-7`. No bounds, retry, fallback optimizer or changed stopping tolerance is added. The new source makes full102-coordinate pooled/individual-head calls and one combined204-coordinate joint call. Unsupported pair inputs are zero; starting coefficients and corresponding gradients are exactly zero. Every returned unsupported coefficient must remain exactly zero or execution stops; output clipping cannot hide drift. Even an all-unsupported invented input uses the fixed full dimension and fixed call count. Model objectives and final gradients are recomputed from the returned coefficients and required finite. Maximum gradient is recorded, not represented as a stricter convergence test than the preserved SciPy success criterion.

The returned model is an in-memory serializable dictionary with arm/config/scaling, coefficient vector(s), native optimizer summaries/options, fixed feature width/scorer identity and training counts. No checkpoint is written. A later writer must bind original IDs, source metadata/labels, feature values, pair roster/weights, common scaling, runtime, configuration and committed prefit at creation; those mandatory fields are not replaced by this dictionary.

## Canonical numerical scorer, fixed before outcomes

The complete validation matrix is copied to a C-contiguous float64 matrix with all102 columns. Its full target identity and row order must be certified by the future caller; this function cannot detect a caller passing a subset. Scoring arithmetic is frozen as `z=(full_matrix-zero102)/scale`. There is no active-column compression, row batching or cell-specific matrix subset. Pooled computes `z @ beta`. Independent computes both complete `z @ u_CAD` and `z @ u_Neuro-2a` arrays, then selects each row's actual cell. Joint first constructs both coefficient vectors `beta+delta` and `beta-delta`, computes both full-matrix dot products, then selects actual cells. This explicitly fixes coefficient-addition versus prediction-addition and matrix-shape conventions.

The future primary choices must use these exact canonical outputs and original lexical intervention-ID ties. Independent coefficient-sum arithmetic must be bounded below1e-9 and may not replace canonical ties. Fullshape assertions, exact validation IDs, native float64/C order and score replay remain mandatory in the future campaign. The present Python array double uses loops and `math.fsum`, so it cannot certify BLAS tie parity.

## Preparation, tests and unfinished admissions

The scoped tests execute only invented lists through a deliberately small standard-library array double and optimizer spy. They compare actual deferred objective/gradient code with the frozen scalar reference, finite differences, stable extreme margins, conditional2w losses, common RMS/support, rejection of unsupported coefficient drift, strict optimizer failure, original options/call counts/dimensions, complete-head scorer call shapes, exact zero-score ties and malformed inputs. The spy does not optimize. No NumPy, pandas, SciPy, Torch, OpenVINO or other scientific library is imported, and no native optimizer runs. Passing these tests is not native numerical parity or a successful fit.

`prepare.py` independently verifies all prior reference readiness source/summary pins, its static design chain, original optimizer source text, all own source hashes and scoped test receipt. Its exclusive-write manifest records source preparation only. Root must review and commit exact bytes before any separately frozen, resource-admitted invented native profile. That profile must certify actual package/runtime origins and compare native equations, optimization, support and full-shape canonical predictions against independent references. Actual project inputs remain ineligible until a distinct authorized loader, row/menu/split and feature parity certificate, parsed mean-effect admission, complete prefit and full independently replayable campaign are ready.

All original3-GiB/1-GiB scientific guards and one-thread/one-worker requirements remain. The PUM/PRELib operational exceptions do not apply. No metadata, feature array, effect label, original checkpoint, protected outcome or project model is read or produced here. The full63-arm/84-optimizer-unit nested campaign, source-only selector, immutable checkpoint writer, independent54-inner/9-outer replay, primary paired gates and secondary reports are unfinished and not authorized by this preparation.
