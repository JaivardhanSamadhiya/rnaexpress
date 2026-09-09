# FinalShot Mikl matched-mechanism result

**September 9 integrity qualification:** the implemented analysis below omits
the written two-candidates-per-gene cap, which also conflicts with the written
minimum of four candidates per within-gene matched subset. The archived numeric
Gate C pass is not an unqualified protocol-compliant pass. See
`reports/finalshot_integrity_review.md`; no archived predictions were changed.

The primary matched test used the fully nested M1/M2/M3 held-fold predictor.
Candidate eligibility was determined without outcomes from cell line, motif
family, intervention class, operation signature, and frozen edit-size band. A
cross-parent stratum required at least 20 candidates and five held genes;
within-gene matched decision subsets required at least four candidates.

There were 284 eligible cross-parent strata, 9,834 retained candidates, 1,600
matched decision subsets, and 120 held genes. Macro-averaging by motif family
and direction gave rank ContextValue `+0.01582` and regret ContextValue
`+0.01785` over M0 geometry. The frozen thresholds were `+0.010` and `+0.005`,
so Gate C passes. Positive signs occurred in 76/146 motif-direction rank tasks
and 80/146 motif-direction regret tasks; the effect is positive in aggregate,
not universal across motif strata.

This records predictive value in the implemented repeated-Mikl motif
stratification, subject to the integrity qualification above. It does not
establish genuine RBP-specific mechanism or override failures
in distributed-unit or small-edit gates and does not establish direct TDP-43
binding, because RBPNet lacks a TARDBP checkpoint.

Machine-readable details are in `results/finalshot/mikl_matching_audit.csv`,
`mikl_matched_motif_metrics.csv`, and `grouped_gate_summary.json`.
