# Mechanism-v2 outer evaluation

Status: frozen outer evaluation, executed once. Astrocyte remains sealed.

Generated from the committed outer freeze at `04155604d201`. Gate thresholds: `a57dd77f6b13`.

Primary selected family: **M4**. Per-fold primary recipes: `{"0": "M4_C", "1": "M4_E", "2": "M7_E", "3": "M1_F", "4": "M6_E"}`. Family agreement across folds: `{"M1": 1, "M4": 2, "M6": 1, "M7": 1}`.

## Selector versus the geometry baseline

| comparison | rank gain | regret gain | components | scope |
| --- | ---: | ---: | ---: | --- |
| primary selector vs M0 (full coverage) | +0.0250 | +0.0252 | 211 | 445 decisions |
| M1 vs M0 | +0.0200 | +0.0190 | 211 | 445 decisions |
| M2 vs M0 | -0.0553 | -0.0421 | 211 | 445 decisions |
| M3 vs M0 | -0.0415 | -0.0266 | 211 | 445 decisions |
| M4 vs M0 | +0.0140 | +0.0193 | 211 | 445 decisions |
| M5 vs M0 | +0.0045 | +0.0109 | 211 | 445 decisions |
| M6 vs M0 | +0.0065 | +0.0136 | 211 | 445 decisions |
| M7 vs M0 | +0.0174 | +0.0184 | 211 | 445 decisions |
| primary vs M0 | +0.0250 | +0.0252 | 211 | 445 decisions |

## Absolute selected performance

* selector: regret 0.4074, rank 0.6271, Good@3 0.2417, Good@5 0.3082, random expected regret 0.5000
* M0 baseline: regret 0.4326, rank 0.6021

## Distributed benefit

```json
{
  "components": 211,
  "direction_fractions": {
    "decrease": 0.5355450236966824,
    "increase": 0.5213270142180095
  },
  "fraction_improved": 0.5687203791469194,
  "leave_best_one_out_mean": 0.024167585950473955,
  "median": 0.01754597225673414,
  "quartiles": [
    -0.07392874498816474,
    0.09995206330334466
  ],
  "source_fractions": {
    "mikl_gse173098": 0.5661375661375662,
    "moffatt_gse334718": 0.5,
    "tdp43_gse288185": 0.6875
  },
  "worst_decile_mean": -0.25150612017023344,
  "worst_decile_quantile": -0.18912558699719784
}
```

## Paired component bootstrap

```json
{
  "components": 211,
  "confidence95": {
    "rank_gain": [
      -0.029521678194969248,
      0.08460035338947829
    ],
    "regret_gain": [
      -0.007569182554345502,
      0.05922753917990739
    ]
  },
  "eligible": true,
  "missing_context_replicates": 2,
  "point": {
    "rank_gain": 0.025006819534256496,
    "regret_gain": 0.02520345908860507
  },
  "resamples_requested": 10000,
  "resamples_valid": 9998,
  "seed": 20260909,
  "unit": "connected biological component; all directions and cross-source occurrences together"
}
```

## Matched-edit and small-edit analyses

| analysis | rank gain | regret gain | components | scope |
| --- | ---: | ---: | ---: | --- |
| matched: cap_plus_four_candidate_minimum | ineligible | ineligible | - | a two-per-gene cap leaves at most two candidates in a single-parent decision set, so a four-candidate minimum is arithmetically unevaluable |
| matched: edit_band|intervention_class|biological_unit | +0.0320 | +0.0210 | 211 | 1141 decisions |
| matched: edit_band|intervention_class|dataset | +0.0320 | +0.0210 | 211 | 1141 decisions |
| matched: literal_two_per_gene_cap | +0.0674 | +0.0674 | 156 | 211 decisions |
| matched: mikl_motif_family_macro | +0.0154 | +0.0138 | 142 | 1902 decisions |
| matched: primary | +0.0320 | +0.0210 | 211 | 1141 decisions |
| edit band 0 | ineligible | ineligible | - | no candidate rows in this band |
| edit band 1 | +0.0250 | +0.0820 | 2 | 4 decisions |
| edit band 11-25 | +0.0699 | +0.0547 | 85 | 177 decisions |
| edit band 2-10 | +0.0137 | +0.0166 | 211 | 433 decisions |
| edit band 2-5 | +0.0057 | +0.0039 | 208 | 421 decisions |
| edit band 26-50 | -0.0731 | -0.0998 | 22 | 58 decisions |
| edit band 6-10 | -0.0061 | -0.0049 | 205 | 423 decisions |
| edit band >50 | +0.0442 | +0.0289 | 15 | 58 decisions |
| restricted domain 2-10 nt | +0.0137 | +0.0166 | 211 | 433 decisions |

## Declared sensitivities

| sensitivity | rank gain | regret gain | components | scope |
| --- | ---: | ---: | ---: | --- |
| annotated_gene_groups | +0.0250 | +0.0252 | 211 | 445 decisions |
| sequence90 | +0.0250 | +0.0252 | 211 | 445 decisions |

## Uncertainty and coverage

```json
{
  "0": {
    "options": [
      {
        "coverage_achieved": 1.0,
        "coverage_requested": 1.0,
        "decisions": 718,
        "rank": 0.6497153954885562,
        "regret": 0.40267425251837935
      },
      {
        "coverage_achieved": 0.8997214484679665,
        "coverage_requested": 0.9,
        "decisions": 646,
        "rank": 0.6558407030311277,
        "regret": 0.40091211940417687
      },
      {
        "coverage_achieved": 0.7493036211699164,
        "coverage_requested": 0.75,
        "decisions": 538,
        "rank": 0.6819599887243561,
        "regret": 0.3851425938569173
      }
    ],
    "recipe_id": "M4_C",
    "selected_coverage": 0.75,
    "selection_rule": "inner-only minimum covered regret within the 0.002 tolerance, then greater coverage"
  },
  "1": {
    "options": [
      {
        "coverage_achieved": 1.0,
        "coverage_requested": 1.0,
        "decisions": 700,
        "rank": 0.6146121513162683,
        "regret": 0.41757233499338714
      },
      {
        "coverage_achieved": 0.9028571428571428,
        "coverage_requested": 0.9,
        "decisions": 632,
        "rank": 0.6281382164828974,
        "regret": 0.4097383249444238
      },
      {
        "coverage_achieved": 0.7542857142857143,
        "coverage_requested": 0.75,
        "decisions": 528,
        "rank": 0.6433769307931645,
        "regret": 0.3991756997730507
      }
    ],
    "recipe_id": "M4_E",
    "selected_coverage": 0.75,
    "selection_rule": "inner-only minimum covered regret within the 0.002 tolerance, then greater coverage"
  },
  "2": {
    "options": [
      {
        "coverage_achieved": 1.0,
        "coverage_requested": 1.0,
        "decisions": 728,
        "rank": 0.6233796914824971,
        "regret": 0.4229005875971868
      },
      {
        "coverage_achieved": 0.9010989010989011,
        "coverage_requested": 0.9,
        "decisions": 656,
        "rank": 0.6273983243613026,
        "regret": 0.4147339546060527
      },
      {
        "coverage_achieved": 0.7527472527472527,
        "coverage_requested": 0.75,
        "decisions": 548,
        "rank": 0.6348981396538694,
        "regret": 0.40160178369274147
      }
    ],
    "recipe_id": "M7_E",
    "selected_coverage": 0.75,
    "selection_rule": "inner-only minimum covered regret within the 0.002 tolerance, then greater coverage"
  },
  "3": {
    "options": [
      {
        "coverage_achieved": 1.0,
        "coverage_requested": 1.0,
        "decisions": 698,
        "rank": 0.5962031300553132,
        "regret": 0.4229692120472697
      },
      {
        "coverage_achieved": 0.9025787965616046,
        "coverage_requested": 0.9,
        "decisions": 630,
        "rank": 0.577303164337862,
        "regret": 0.44172219551294695
      },
      {
        "coverage_achieved": 0.7535816618911175,
        "coverage_requested": 0.75,
        "decisions": 526,
        "rank": 0.5821364858021058,
        "regret": 0.4213703566981652
      }
    ],
    "recipe_id": "M1_F",
    "selected_coverage": 1.0,
    "selection_rule": "inner-only minimum covered regret within the 0.002 tolerance, then greater coverage"
  },
  "4": {
    "options": [
      {
        "coverage_achieved": 1.0,
        "coverage_requested": 1.0,
        "decisions": 716,
        "rank": 0.6220803939800431,
        "regret": 0.39740171920144807
      },
      {
        "coverage_achieved": 0.8994413407821229,
        "coverage_requested": 0.9,
        "decisions": 644,
        "rank": 0.6275217404286481,
        "regret": 0.3935942494814813
      },
      {
        "coverage_achieved": 0.7513966480446927,
        "coverage_requested": 0.75,
        "decisions": 538,
        "rank": 0.6380029559534458,
        "regret": 0.38326392596604036
      }
    ],
    "recipe_id": "M6_E",
    "selected_coverage": 0.75,
    "selection_rule": "inner-only minimum covered regret within the 0.002 tolerance, then greater coverage"
  }
}
```

Full coverage remains the gate. these development datasets have been examined repeatedly in earlier RNAddress experiments; nested estimates on a reused benchmark are not fresh independent confirmation
