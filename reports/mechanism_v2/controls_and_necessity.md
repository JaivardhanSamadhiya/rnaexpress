# Mechanism-v2 controls, necessity and integrity

Generated from the committed outer freeze at `04155604d201`. Gate thresholds: `a57dd77f6b13`.

## Prospectively specified nulls

| null | rank gain | regret gain | components | status |
| --- | ---: | ---: | ---: | --- |
| m1_parent_aware_comparator | -0.0069 | +0.0064 | 211 | 445 decisions |
| n0_geometry | +0.0000 | +0.0000 | 211 | eligible cohort |
| n1_edit_descriptors | +0.0152 | +0.0015 | 211 | 445 decisions |
| n2_geometry_source_slopes | +0.0219 | +0.0110 | 211 | 445 decisions |
| n3_parent_identity | ineligible | ineligible | - | not evaluated |
| n4_random_kmer_delta | +0.0286 | +0.0226 | 211 | 445 decisions |
| n5_bijection_edit_band | -0.0254 | -0.0276 | 210 | 443 decisions |
| n5_bijection_global | -0.1142 | -0.0715 | 211 | 445 decisions |
| n5_bijection_parent | -0.0683 | -0.0254 | 211 | 445 decisions |
| n5_bijection_source | -0.0851 | -0.0589 | 211 | 445 decisions |
| n6_absolute_mutant | -0.0211 | -0.0125 | 211 | 445 decisions |
| n6_absolute_reference | +0.0062 | +0.0032 | 211 | 445 decisions |
| n7_broken_reference | -0.0229 | -0.0056 | 183 | 366 decisions |
| n8_bijection_source_edit_band | -0.0526 | -0.0339 | 209 | 441 decisions |
| n9_structure_bijection | -0.0113 | -0.0083 | 167 | 345 decisions |

## Primary necessity comparison

```json
{
  "n5_bijection_global": {
    "detail": {
      "components": 211,
      "destroys_at_least_one_metric_by_half": true,
      "mean_retained_fraction": -3.7019006436102124,
      "mean_retained_within_limit": true,
      "null_meets_both_useful_selection_thresholds": false,
      "point": {
        "rank_gain": -0.11417546112447645,
        "regret_gain": -0.07152813015269176
      },
      "retained_fraction": {
        "rank_gain": -4.565772987167323,
        "regret_gain": -2.8380283000531024
      },
      "retention_defined": true,
      "status": "evaluated"
    },
    "status": "pass"
  },
  "n8_bijection_source_edit_band": {
    "detail": {
      "components": 209,
      "destroys_at_least_one_metric_by_half": true,
      "mean_retained_fraction": -1.724493612967097,
      "mean_retained_within_limit": true,
      "null_meets_both_useful_selection_thresholds": false,
      "point": {
        "rank_gain": -0.05263581716996727,
        "regret_gain": -0.03387669283452767
      },
      "retained_fraction": {
        "rank_gain": -2.1048585206072365,
        "regret_gain": -1.3441287053269575
      },
      "retention_defined": true,
      "status": "evaluated"
    },
    "status": "pass"
  }
}
```

## Block removal family (Holm over seven enumerated hypotheses)

```json
{
  "bert_pooled_delta": {
    "claim": false,
    "companion_not_harmful": true,
    "components": 211,
    "effect_threshold_met": true,
    "harm": {
      "rank_gain": 0.005492337856418296,
      "regret_gain": 0.009700710439871368
    },
    "holm_adjusted_p_value": 0.36846315368463156,
    "p_value": 0.0736926307369263,
    "status": "evaluated",
    "test": {
      "alternative": "greater",
      "observed_mean": 0.009700710439871368,
      "p_value": 0.0736926307369263,
      "resamples": 10000,
      "seed": 20260909,
      "test": "paired component sign-flip randomization",
      "units": 211
    }
  },
  "motif_delta": {
    "claim": false,
    "companion_not_harmful": true,
    "components": 84,
    "effect_threshold_met": true,
    "harm": {
      "rank_gain": 0.0067466572785188535,
      "regret_gain": 0.006210265989402489
    },
    "holm_adjusted_p_value": 0.3734626537346265,
    "p_value": 0.12448755124487551,
    "status": "evaluated",
    "test": {
      "alternative": "greater",
      "observed_mean": 0.006210265989402489,
      "p_value": 0.12448755124487551,
      "resamples": 10000,
      "seed": 20260909,
      "test": "paired component sign-flip randomization",
      "units": 84
    }
  },
  "processing_delta": {
    "claim": false,
    "companion_not_harmful": true,
    "components": 84,
    "effect_threshold_met": true,
    "harm": {
      "rank_gain": 0.014666355900366978,
      "regret_gain": 0.00809054127264134
    },
    "holm_adjusted_p_value": 0.33056694330566944,
    "p_value": 0.055094490550944904,
    "status": "evaluated",
    "test": {
      "alternative": "greater",
      "observed_mean": 0.00809054127264134,
      "p_value": 0.055094490550944904,
      "resamples": 10000,
      "seed": 20260909,
      "test": "paired component sign-flip randomization",
      "units": 84
    }
  },
  "ranking_heads": {
    "claim": false,
    "companion_not_harmful": false,
    "components": 42,
    "effect_threshold_met": false,
    "harm": {
      "rank_gain": -0.018107640506205978,
      "regret_gain": -0.008348568907942453
    },
    "holm_adjusted_p_value": 0.9909009099090091,
    "p_value": 0.8397160283971603,
    "status": "evaluated",
    "test": {
      "alternative": "greater",
      "observed_mean": -0.008348568907942453,
      "p_value": 0.8397160283971603,
      "resamples": 10000,
      "seed": 20260909,
      "test": "paired component sign-flip randomization",
      "units": 42
    }
  },
  "rbp_delta": {
    "claim": false,
    "companion_not_harmful": true,
    "components": 211,
    "effect_threshold_met": true,
    "harm": {
      "rank_gain": 0.02413672925775077,
      "regret_gain": 0.01563600233820781
    },
    "holm_adjusted_p_value": 0.36846315368463156,
    "p_value": 0.0775922407759224,
    "status": "evaluated",
    "test": {
      "alternative": "greater",
      "observed_mean": 0.01563600233820781,
      "p_value": 0.0775922407759224,
      "resamples": 10000,
      "seed": 20260909,
      "test": "paired component sign-flip randomization",
      "units": 211
    }
  },
  "structure_delta": {
    "claim": false,
    "companion_not_harmful": true,
    "components": 169,
    "effect_threshold_met": true,
    "harm": {
      "rank_gain": 0.011309228150049032,
      "regret_gain": 0.008586473081396788
    },
    "holm_adjusted_p_value": 0.2470752924707529,
    "p_value": 0.0352964703529647,
    "status": "evaluated",
    "test": {
      "alternative": "greater",
      "observed_mean": 0.008586473081396788,
      "p_value": 0.0352964703529647,
      "resamples": 10000,
      "seed": 20260909,
      "test": "paired component sign-flip randomization",
      "units": 169
    }
  },
  "trans_aligned": {
    "claim": false,
    "companion_not_harmful": true,
    "components": 42,
    "effect_threshold_met": false,
    "harm": {
      "rank_gain": 0.004095238095238095,
      "regret_gain": 0.0027274685847896605
    },
    "holm_adjusted_p_value": 0.9909009099090091,
    "p_value": 0.49545045495450457,
    "status": "evaluated",
    "test": {
      "alternative": "greater",
      "observed_mean": 0.004095238095238095,
      "p_value": 0.49545045495450457,
      "resamples": 10000,
      "seed": 20260909,
      "test": "paired component sign-flip randomization",
      "units": 42
    }
  }
}
```

## Seed replication

```json
{
  "20260909": {
    "categories": {
      "g1_useful_selection": "pass",
      "g3_matched_edits": "pass",
      "g6_small_edits": "pass"
    },
    "components": 211,
    "point": {
      "rank_gain": 0.025006819534256496,
      "regret_gain": 0.02520345908860507
    }
  },
  "20260910": {
    "categories": {
      "g1_useful_selection": "pass",
      "g3_matched_edits": "fail",
      "g6_small_edits": "fail"
    },
    "components": 211,
    "point": {
      "rank_gain": 0.02665048386181471,
      "regret_gain": 0.01551587456614042
    }
  },
  "20260911": {
    "categories": {
      "g1_useful_selection": "fail",
      "g3_matched_edits": "fail",
      "g6_small_edits": "fail"
    },
    "components": 211,
    "point": {
      "rank_gain": -0.00947226729791256,
      "regret_gain": -0.004399722814807195
    }
  }
}
```

Primary-gain standard deviation: `{"rank_gain": 0.020397557911628863, "regret_gain": 0.015093203170778668}`.

## Shortcut resistance

```json
{
  "biological_unit": {
    "eligible": false,
    "reason": "every evaluation label is unseen because whole connected components are held out, so this classification task is ineligible rather than a zero-accuracy success"
  },
  "cell_type": {
    "accuracy": 0.5339777701484851,
    "balanced_accuracy": 0.6087990318478124,
    "classes": 2,
    "decoder": "grouped out-of-fold nearest-class-mean on the single frozen score",
    "eligible": true,
    "folds": 5,
    "groups": 211,
    "labels_absent_from_some_training_fold": 0,
    "majority_class_accuracy": 0.8733155952278774
  },
  "dataset": {
    "accuracy": 0.36834821045403826,
    "balanced_accuracy": 0.39952172618641174,
    "classes": 3,
    "decoder": "grouped out-of-fold nearest-class-mean on the single frozen score",
    "eligible": true,
    "folds": 5,
    "groups": 211,
    "labels_absent_from_some_training_fold": 0,
    "majority_class_accuracy": 0.6976439790575916
  },
  "direction": {
    "accuracy": 0.32577675735988326,
    "balanced_accuracy": 0.42356985004869047,
    "classes": 3,
    "decoder": "grouped out-of-fold nearest-class-mean on the single frozen score",
    "eligible": true,
    "folds": 5,
    "groups": 211,
    "labels_absent_from_some_training_fold": 0,
    "majority_class_accuracy": 0.5477426830314994
  },
  "direction_identifiability": {
    "note": "the two directional decisions on a set share identical covariates and differ only by the sign applied to the shared latent score, so direction decodability is not separately identifiable from the representation"
  },
  "edit_band": {
    "accuracy": 0.24043000600806796,
    "balanced_accuracy": 0.29390184425768406,
    "classes": 6,
    "decoder": "grouped out-of-fold nearest-class-mean on the single frozen score",
    "eligible": true,
    "folds": 5,
    "groups": 211,
    "labels_absent_from_some_training_fold": 0,
    "majority_class_accuracy": 0.2878508282550854
  },
  "gene_label": {
    "eligible": false,
    "reason": "every evaluation label is unseen because whole connected components are held out, so this classification task is ineligible rather than a zero-accuracy success"
  },
  "intervention_class": {
    "accuracy": 0.2726911853059823,
    "balanced_accuracy": 0.21526801709924934,
    "classes": 7,
    "decoder": "grouped out-of-fold nearest-class-mean on the single frozen score",
    "eligible": true,
    "folds": 5,
    "groups": 211,
    "labels_absent_from_some_training_fold": 0,
    "majority_class_accuracy": 0.2533688095442451
  },
  "reporter": {
    "accuracy": 0.29211011930306413,
    "balanced_accuracy": 0.29686299819959144,
    "classes": 4,
    "decoder": "grouped out-of-fold nearest-class-mean on the single frozen score",
    "eligible": true,
    "folds": 5,
    "groups": 211,
    "labels_absent_from_some_training_fold": 0,
    "majority_class_accuracy": 0.4747231997253455
  }
}
```

decodability is descriptive. Edit size and mutation class are genuinely correlated with mechanism, so a decodable score is not by itself a shortcut, and an undecodable score is not by itself a mechanism.

## Stated limitations

* A single global renaming of a freely learned linear coefficient vector is mathematically invariant and is not used as a necessity test.
* Trans identity controls mismatch externally named RBP availability weights rather than merely relabelling a free coefficient vector.
* These are predictive necessity tests; none of them demonstrates experimentally that an RBP mediates localization.
* N10 is not applicable: independent stability admission failed and no stability block exists. It is never zero-filled or reported as a passed necessity control.
* The inner-selected family differs across outer folds, so a block present in only some selected models is evaluated on the folds that contain it, with the comparison cohort restricted identically on both sides and the coverage stated.
