# Mechanism-v2 model implementation checkpoint

Status: prospective implementation and synthetic verification only. **No new
localization outer-fold predictions or final model selection have been produced.**

## Ranking core

The new shared linear score takes numerical delta features only. Fitting uses
within-decision-set pairwise logistic loss, with at most 128 uniformly sampled
unordered pairs per set. Sampling is seeded from the decision ID and does not
use outcomes; exact outcome ties provide no ordering and are omitted. Training
weights balance source, biological unit, decision set and candidate, in that
order. All means/scales and nuisance statistics are fit on training rows only.

The public biological prediction API accepts only the feature matrix. It cannot
accept a source label or a parent ID. Serialized models include feature names,
configuration, training diagnostics, scaling and coefficients. Unit tests verify
the analytical gradient against finite differences, model round trips, repeated
predictions, within-set pairing, and identity separation using synthetic data.

## Four nuisance choices, precisely defined

Candidate modes are none, source, edit-size band, and source plus edit-size band.
The implementation penalizes the training-only linear predictability of the
latent score from centered nuisance indicators. The corresponding positive
semidefinite quadratic form is a closed-form variational linear-predictor
penalty. This is a **restricted linear alternative**, not a neural gradient-
reversal encoder and not proof of disentanglement. Nonlinear held-out nuisance
probes and matched-stratum evaluations remain necessary. Removing legitimate
size-dependent biology could hurt; the mode must be chosen in inner validation.

## Heads and identifiability

Optional positive source-specific ranking temperatures are fit jointly with the
shared score and shrunk toward one. They are training heads, not calibrated
assay-effect regressions. No head label is required at biological-score inference;
an unseen source uses temperature one. A positive affine transformation of a
fixed score cannot change ranking within an assay. Consequently, shuffling such
heads only at inference is an uninformative ranking-necessity control. The valid
comparison retrains the latent model with versus without the training heads and
tests leave-source transfer. A separate assay measurement-calibration analysis
is still pending; temperatures will not be misreported as measured assay units.

## Pending before outer evaluation

The numerical candidate grid, admitted resources, processing treatment, all
null/transfer implementations and acceptance gates must be fully specified and
committed in the final frozen protocol. The current module does not bypass that
condition. M0–M7 assembly and nested evaluation remain to be wired to the final
validated feature manifests. Missing resources are not zero-filled.
