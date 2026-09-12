# Mechanism-v2 purged transfer evaluation

Generated from the committed outer freeze at `04155604d201`. Gate thresholds: `a57dd77f6b13`.

Inventory: `3 leave-source, 15 within-source, 10 cell, 10 reporter and 5 large-to-small held-group tasks`.

| directed transfer | rank gain | regret gain | components | scope |
| --- | ---: | ---: | ---: | --- |
| cross_cell: cross_cell_CAD_to_Neuro-2a (increase) | +0.0171 | +0.0094 | 189 | 189 decisions |
| cross_cell: cross_cell_CAD_to_Neuro-2a (decrease) | -0.0083 | -0.0126 | 189 | 189 decisions |
| cross_cell: cross_cell_Neuro-2a_to_CAD (increase) | -0.0380 | -0.0050 | 189 | 189 decisions |
| cross_cell: cross_cell_Neuro-2a_to_CAD (decrease) | -0.0088 | -0.0035 | 189 | 189 decisions |
| cross_reporter: cross_reporter_Firefly_to_GFP (increase) | -0.0619 | -0.0387 | 8 | 29 decisions |
| cross_reporter: cross_reporter_Firefly_to_GFP (decrease) | -0.0607 | -0.0040 | 8 | 29 decisions |
| cross_reporter: cross_reporter_GFP_to_Firefly (increase) | -0.1415 | -0.0946 | 6 | 22 decisions |
| cross_reporter: cross_reporter_GFP_to_Firefly (decrease) | +0.0278 | +0.0550 | 6 | 22 decisions |
| large_to_small: large_to_small (increase) | +0.0107 | -0.0148 | 211 | 433 decisions |
| large_to_small: large_to_small (decrease) | -0.1370 | -0.0975 | 211 | 433 decisions |
| leave_source: leave_source_mikl_gse173098 (increase) | +0.0080 | -0.0010 | 189 | 378 decisions |
| leave_source: leave_source_mikl_gse173098 (decrease) | -0.0007 | +0.0064 | 189 | 378 decisions |
| leave_source: leave_source_moffatt_gse334718 (increase) | -0.1676 | -0.0829 | 8 | 51 decisions |
| leave_source: leave_source_moffatt_gse334718 (decrease) | +0.0157 | +0.0477 | 8 | 51 decisions |
| leave_source: leave_source_tdp43_gse288185 (increase) | +0.1896 | +0.0616 | 16 | 16 decisions |
| leave_source: leave_source_tdp43_gse288185 (decrease) | +0.0347 | +0.0804 | 16 | 16 decisions |
| within_source: within_mikl_gse173098 (increase) | -0.0049 | +0.0016 | 189 | 378 decisions |
| within_source: within_mikl_gse173098 (decrease) | +0.0090 | -0.0020 | 189 | 378 decisions |
| within_source: within_moffatt_gse334718 (increase) | -0.2438 | -0.1294 | 8 | 51 decisions |
| within_source: within_moffatt_gse334718 (decrease) | -0.1627 | -0.1181 | 8 | 51 decisions |
| within_source: within_tdp43_gse288185 (increase) | -0.0308 | -0.0230 | 16 | 16 decisions |
| within_source: within_tdp43_gse288185 (decrease) | -0.0372 | +0.0038 | 16 | 16 decisions |

## Ineligible folds, reported rather than passed

* `cross_reporter_GFP_to_Firefly_2`: fewer_than_three_training_components_or_empty_test

## Gates

```json
{
  "g4_leave_source": {
    "checks": {
      "all_six_tasks_eligible": true,
      "macro_rank_gain": true,
      "macro_regret_gain": true,
      "no_single_source_dominates": true,
      "tasks_improving_both": false
    },
    "eligible_tasks": [
      "leave_source_mikl_gse173098|decrease",
      "leave_source_mikl_gse173098|increase",
      "leave_source_moffatt_gse334718|decrease",
      "leave_source_moffatt_gse334718|increase",
      "leave_source_tdp43_gse288185|decrease",
      "leave_source_tdp43_gse288185|increase"
    ],
    "gate": "g4_leave_source",
    "largest_source_share_of_positive_regret_gain": 0.7240134283559464,
    "macro_rank_gain": 0.013277432002245702,
    "macro_regret_gain": 0.018702748762608738,
    "per_task_rank_gain": {
      "leave_source_mikl_gse173098|decrease": -0.000683379538841286,
      "leave_source_mikl_gse173098|increase": 0.007991153585093107,
      "leave_source_moffatt_gse334718|decrease": 0.01565420573682811,
      "leave_source_moffatt_gse334718|increase": -0.16759536644043987,
      "leave_source_tdp43_gse288185|decrease": 0.034735129228299064,
      "leave_source_tdp43_gse288185|increase": 0.1895628494425351
    },
    "per_task_regret_gain": {
      "leave_source_mikl_gse173098|decrease": 0.006429967200574744,
      "leave_source_mikl_gse173098|increase": -0.0010049674879598987,
      "leave_source_moffatt_gse334718|decrease": 0.04768536639581257,
      "leave_source_moffatt_gse334718|increase": -0.08285812914981192,
      "leave_source_tdp43_gse288185|decrease": 0.08036580588590503,
      "leave_source_tdp43_gse288185|increase": 0.061598449731131905
    },
    "status": "fail",
    "tasks_improving_both": [
      "leave_source_moffatt_gse334718|decrease",
      "leave_source_tdp43_gse288185|decrease",
      "leave_source_tdp43_gse288185|increase"
    ],
    "thresholds": {
      "macro_rank_gain_minimum_exclusive": 0.0,
      "macro_regret_gain_minimum": 0.01,
      "maximum_single_source_share_of_positive_regret_gain": 0.75,
      "minimum_tasks_improving_both": 4,
      "tasks": "three sources withheld separately with connected-group purging, both directions",
      "total_tasks": 6
    }
  },
  "g5_cross_context": {
    "cross_cell": {
      "checks": {
        "all_tasks_eligible": true,
        "macro_regret_gain": false,
        "tasks_improving_both": false
      },
      "eligible_tasks": [
        "cross_cell_CAD_to_Neuro-2a|decrease",
        "cross_cell_CAD_to_Neuro-2a|increase",
        "cross_cell_Neuro-2a_to_CAD|decrease",
        "cross_cell_Neuro-2a_to_CAD|increase"
      ],
      "macro_rank_gain": -0.009493570054172855,
      "macro_regret_gain": -0.00291165354515074,
      "per_task_rank_gain": {
        "cross_cell_CAD_to_Neuro-2a|decrease": -0.008327655141857158,
        "cross_cell_CAD_to_Neuro-2a|increase": 0.01712610310366782,
        "cross_cell_Neuro-2a_to_CAD|decrease": -0.008821599874733448,
        "cross_cell_Neuro-2a_to_CAD|increase": -0.037951128303768636
      },
      "per_task_regret_gain": {
        "cross_cell_CAD_to_Neuro-2a|decrease": -0.012617805242451692,
        "cross_cell_CAD_to_Neuro-2a|increase": 0.009449762211141171,
        "cross_cell_Neuro-2a_to_CAD|decrease": -0.003527293183617472,
        "cross_cell_Neuro-2a_to_CAD|increase": -0.0049512779656749675
      },
      "status": "fail",
      "tasks_improving_both": [
        "cross_cell_CAD_to_Neuro-2a|increase"
      ]
    },
    "cross_reporter": {
      "checks": {
        "all_tasks_eligible": true,
        "macro_regret_gain": false,
        "tasks_improving_both": false
      },
      "eligible_tasks": [
        "cross_reporter_Firefly_to_GFP|decrease",
        "cross_reporter_Firefly_to_GFP|increase",
        "cross_reporter_GFP_to_Firefly|decrease",
        "cross_reporter_GFP_to_Firefly|increase"
      ],
      "macro_rank_gain": -0.059055324369897556,
      "macro_regret_gain": -0.0205636978917561,
      "per_task_rank_gain": {
        "cross_reporter_Firefly_to_GFP|decrease": -0.06066358233702899,
        "cross_reporter_Firefly_to_GFP|increase": -0.06185007232792572,
        "cross_reporter_GFP_to_Firefly|decrease": 0.027840112895137787,
        "cross_reporter_GFP_to_Firefly|increase": -0.14154775570977332
      },
      "per_task_regret_gain": {
        "cross_reporter_Firefly_to_GFP|decrease": -0.003972056462339382,
        "cross_reporter_Firefly_to_GFP|increase": -0.038691258566593924,
        "cross_reporter_GFP_to_Firefly|decrease": 0.05499479383776979,
        "cross_reporter_GFP_to_Firefly|increase": -0.09458627037586087
      },
      "status": "fail",
      "tasks_improving_both": [
        "cross_reporter_GFP_to_Firefly|decrease"
      ]
    },
    "gate": "g5_cross_context",
    "status": "fail",
    "thresholds": {
      "cell_tasks_improving_both_minimum": 3,
      "cell_tasks_total": 4,
      "macro_regret_gain_minimum": 0.005,
      "paired_context_diagnostic": "labelled diagnostic only, never the zero-shot gate",
      "purging": "connected groups held out across contexts; a measured mutant may never serve as its own transfer",
      "reporter_tasks_improving_both_minimum": 3,
      "reporter_tasks_total": 4
    }
  }
}
```

## Notes

* Held connected groups are purged from the training side of every task, so a measured mutant never serves as its own transfer.
* Both the mechanistic family and the recipe are re-selected inside each task training domain from the full M1-M7 pool; no primary-fold choice is borrowed for a different training domain.
* A directed transfer with no eligible fold is reported as ineligible, never passed.
