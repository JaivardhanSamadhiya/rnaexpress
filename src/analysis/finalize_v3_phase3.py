"""Assemble the frozen Phase 3 gate, reports, and reproducibility manifest."""

from __future__ import annotations

import hashlib
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
import platform
import subprocess

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/v3_phase3"
REPORTS = ROOT / "reports"
NAME = "remove_motif_interactions_plus_extreme"


def _read_json(name: str):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _package_versions() -> dict[str, str]:
    result = {"python": platform.python_version()}
    for package in (
        "numpy",
        "pandas",
        "scipy",
        "scikit-learn",
        "joblib",
        "torch",
        "transformers",
        "lightgbm",
        "ViennaRNA",
    ):
        try:
            result[package] = version(package)
        except PackageNotFoundError:
            result[package] = "not-installed"
    return result


def _complexity(current: pd.Series, reference: pd.Series) -> dict[str, object]:
    score_gain = float(current["selection_score"] - reference["selection_score"])
    rank_gain = float(current["rank_percentile"] - reference["rank_percentile"])
    regret_gain = float(reference["normalized_regret"] - current["normalized_regret"])
    top5_gain = float(current["oracle_top5"] - reference["oracle_top5"])
    passed = score_gain >= 0.005 and (
        rank_gain >= 0.005 or regret_gain >= 0.010 or top5_gain >= 1.0 / 30.0
    )
    return {
        "selection_score_gain": score_gain,
        "rank_gain": rank_gain,
        "regret_improvement": regret_gain,
        "top5_gain": top5_gain,
        "pass": bool(passed),
    }


def main() -> None:
    selected = pd.read_csv(OUT / "best_ablation_extreme_macro_metrics.csv").iloc[0]
    candidates = pd.read_csv(OUT / "candidate_macro_metrics.csv").set_index("candidate")
    v2 = candidates.loc["v2_6_historical"]
    c2 = candidates.loc["rank_magnitude_stack"]
    ablations = pd.read_csv(OUT / "mechanistic_ablation_macro_metrics.csv").set_index("ablation")
    pruned_c3 = ablations.loc["remove_motif_interactions"]
    forward_name = _read_json("forward_selection.json")["strongest_fair_forward"]
    forward = pd.read_csv(OUT / "forward_macro_metrics.csv").set_index("model").loc[forward_name]
    metadata = pd.read_csv(OUT / "metadata_macro_metrics.csv").iloc[0]
    controls = pd.read_csv(OUT / "negative_control_macro_metrics.csv").set_index("model")
    seed_metrics = pd.read_csv(OUT / "seed_stability_macro_metrics.csv")
    robustness = _read_json("controls_seed_robustness.json")
    selective = _read_json("selective_prediction_gate.json")
    coverage = pd.read_csv(OUT / "selective_coverage_metrics.csv")
    representation = pd.read_csv(OUT / "representation_comparison.csv").set_index("representation")
    rep_ablation = pd.read_csv(OUT / "representation_ablation_macro_metrics.csv")
    random = _read_json("exact_random_expectations.json")

    criteria = {
        "A_rank_preservation": {
            "rank_at_least_0_630": bool(selected["rank_percentile"] >= 0.630),
            "within_0_005_of_v2_6": bool(
                selected["rank_percentile"] >= v2["rank_percentile"] - 0.005
            ),
        },
        "B_material_regret_improvement": {
            "regret_at_most_0_397": bool(selected["normalized_regret"] <= 0.397),
            "improvement_at_least_0_030": bool(
                v2["normalized_regret"] - selected["normalized_regret"] >= 0.030
            ),
        },
        "C_strongest_forward": {
            "rank_gain_at_least_0_030": bool(
                selected["rank_percentile"] - forward["rank_percentile"] >= 0.030
            ),
            "regret_improvement_at_least_0_020": bool(
                forward["normalized_regret"] - selected["normalized_regret"] >= 0.020
            ),
            "utility_gain_at_least_0_020": bool(
                selected["selected_utility"] - forward["selected_utility"] >= 0.020
            ),
        },
        "D_metadata": {
            "rank_gain_at_least_0_020": bool(
                selected["rank_percentile"] - metadata["rank_percentile"] >= 0.020
            ),
            "regret_improvement_at_least_0_020": bool(
                metadata["normalized_regret"] - selected["normalized_regret"] >= 0.020
            ),
        },
        "E_extreme_recovery": {
            "top5_at_least_0_10": bool(selected["oracle_top5"] >= 0.10),
            "near_oracle_at_least_0_20": bool(selected["near_oracle"] >= 0.20),
            "mean_oracle_rank_at_most_90": bool(selected["mean_oracle_rank"] <= 90),
        },
        "F_distribution": {
            "median_gain_positive": bool(
                robustness["parent_robustness"]["median_parent_gain"] > 0
            ),
            "at_least_9_of_15_improve": bool(
                robustness["parent_robustness"]["improved_parent_count"] >= 9
            ),
            "leave_best_one_positive": bool(
                robustness["parent_robustness"]["leave_best_one_mean_gain"] > 0
            ),
            "leave_best_two_positive": bool(
                robustness["parent_robustness"]["leave_best_two_mean_gain"] > 0
            ),
        },
        "G_controls": {
            key: bool(value["pass"])
            for key, value in robustness["control_gate"].items()
        },
        "H_seed_stability": {
            key: value
            for key, value in robustness["seed_gate"].items()
            if key != "pass"
        },
        "I_complexity": {
            "pruned_mechanism_vs_contextual_stack": _complexity(pruned_c3, c2),
            "extreme_head_vs_pruned_mechanism": _complexity(selected, pruned_c3),
        },
        "J_uncertainty": {
            key: value for key, value in selective["gate_J"].items() if key != "pass"
        },
    }
    for name, section in criteria.items():
        if name == "I_complexity":
            section["pass"] = bool(
                section["pruned_mechanism_vs_contextual_stack"]["pass"]
                and section["extreme_head_vs_pruned_mechanism"]["pass"]
            )
        elif name == "H_seed_stability":
            section["pass"] = bool(robustness["seed_gate"]["pass"])
        elif name == "J_uncertainty":
            section["pass"] = bool(selective["gate_J"]["pass"])
        else:
            section["pass"] = bool(all(section.values()))
    failed = [name for name, section in criteria.items() if not section["pass"]]
    gate = {
        "phase": "v3_phase3",
        "decision": "NO-GO",
        "development_best_candidate": NAME,
        "criteria": criteria,
        "failed_criteria": failed,
        "astrocyte_spend_authorized": False,
        "stop_rule": "Phase 3 complete; do not begin prospective validation",
    }
    (OUT / "gate.json").write_text(json.dumps(gate, indent=2) + "\n", encoding="utf-8")

    selected_model = {
        "decision": "NO-GO",
        "development_best_candidate": NAME,
        "selected_for_external_lock": False,
        "architecture": {
            "contextual_representation": "3UTRBERT 3-mer final-layer CLS/global/affected-3-mer/radius-10 mutant-minus-parent deltas plus frozen 590-element edit vector",
            "feature_count": int(selected["feature_count"]),
            "mechanism": "prespecified mechanism block with motif-interaction family removed after grouped ablation",
            "rank_head": "nested StandardScaler + Ridge percentile regression",
            "magnitude_head": "nested raw-delta Ridge/Huber selection",
            "stack": "outer-training-cross-fitted rank+magnitude weights in {0.25,0.50,0.75}",
            "extreme_head": "direction-specific balanced logistic top-decile probability with C in {0.1,1,10} and stack weight in {0.10,0.20}",
            "evaluation": "outer LOPO over 15 N-zip parents; inner LOPO over 14 training parents",
        },
        "metrics": {key: float(selected[key]) for key in (
            "rank_percentile", "normalized_regret", "selected_utility", "oracle_top1",
            "oracle_top3", "oracle_top5", "oracle_top10", "near_oracle",
            "mean_oracle_rank", "spearman_utility", "selection_score"
        )},
        "comparators": {
            "v2_6_historical": {key: float(v2[key]) for key in (
                "rank_percentile", "normalized_regret", "selected_utility", "oracle_top5"
            )},
            forward_name: {key: float(forward[key]) for key in (
                "rank_percentile", "normalized_regret", "selected_utility", "oracle_top5"
            )},
            "metadata_only": {key: float(metadata[key]) for key in (
                "rank_percentile", "normalized_regret", "selected_utility", "oracle_top5"
            )},
        },
        "failed_gate_sections": failed,
        "verification": {
            "test_files_passed": 9,
            "tests_passed": 30,
            "monolithic_pytest_status": "not usable on this Windows host because ViennaRNA DLL initialization fails under combined import order; every file passed in a clean process",
        },
        "protected_data_access": {
            "astrocyte_outcomes_opened": False,
            "moffatt_archive_opened": False,
        },
    }
    (OUT / "model_selection.json").write_text(
        json.dumps(selected_model, indent=2) + "\n", encoding="utf-8"
    )

    rep = representation.loc["3utrbert_3mer"]
    rep_rows = rep_ablation[rep_ablation["target"] == "rank"].set_index(
        "representation_ablation"
    )
    magnitude_report = f"""# RNAddress v3 Phase 3 magnitude-objective results

## Verdict

Direct magnitude learning did **not** fix the compiler regret problem. The strongest development model improved normalized regret from `{v2['normalized_regret']:.6f}` to `{selected['normalized_regret']:.6f}`, an improvement of only `{v2['normalized_regret'] - selected['normalized_regret']:.6f}` versus the frozen `0.030` requirement, and remained above the `0.397` ceiling.

## Candidate results

| Candidate | Rank percentile | Normalized regret | Selected utility | Oracle top-5 | Near oracle | Selection score |
|---|---:|---:|---:|---:|---:|---:|
| v2.6 historical | {v2['rank_percentile']:.6f} | {v2['normalized_regret']:.6f} | {v2['selected_utility']:.6f} | {v2['oracle_top5']:.3f} | {v2['near_oracle']:.3f} | {v2['selection_score']:.6f} |
| Contextual magnitude | {candidates.loc['contextual_magnitude','rank_percentile']:.6f} | {candidates.loc['contextual_magnitude','normalized_regret']:.6f} | {candidates.loc['contextual_magnitude','selected_utility']:.6f} | {candidates.loc['contextual_magnitude','oracle_top5']:.3f} | {candidates.loc['contextual_magnitude','near_oracle']:.3f} | {candidates.loc['contextual_magnitude','selection_score']:.6f} |
| Rank+magnitude stack | {c2['rank_percentile']:.6f} | {c2['normalized_regret']:.6f} | {c2['selected_utility']:.6f} | {c2['oracle_top5']:.3f} | {c2['near_oracle']:.3f} | {c2['selection_score']:.6f} |
| Pruned mechanism C3 | {pruned_c3['rank_percentile']:.6f} | {pruned_c3['normalized_regret']:.6f} | {pruned_c3['selected_utility']:.6f} | {pruned_c3['oracle_top5']:.3f} | {pruned_c3['near_oracle']:.3f} | {pruned_c3['selection_score']:.6f} |
| Pruned mechanism + extreme | {selected['rank_percentile']:.6f} | {selected['normalized_regret']:.6f} | {selected['selected_utility']:.6f} | {selected['oracle_top5']:.3f} | {selected['near_oracle']:.3f} | {selected['selection_score']:.6f} |

The explicit extreme head raised rank percentile by `{selected['rank_percentile'] - pruned_c3['rank_percentile']:.6f}` but recovered the exact oracle in the top five for `0/30` decisions. It therefore improved the frozen composite score without solving extreme-edit recovery.

## Mechanistic ablations

Removing motif interactions improved the C3 selection score from `{ablations.loc['complete_mechanism','selection_score']:.6f}` to `{pruned_c3['selection_score']:.6f}`, so motif interactions were dropped. Removing the stability auxiliary reduced score to `{ablations.loc['remove_stability_auxiliary','selection_score']:.6f}` and worsened regret to `{ablations.loc['remove_stability_auxiliary','normalized_regret']:.6f}`; stability therefore survived its grouped ablation. Parent-state interactions also survived because their removal reduced score to `{ablations.loc['remove_parent_state_interactions','selection_score']:.6f}`. Local accessibility did not show an independent positive contribution in its full-block removal test, and no unplanned joint-pruning search was performed.

Measurement-aware targets were not feasible because deterministic construct-linked replicate uncertainty could not be reconstructed without inventing standard errors.
"""
    (REPORTS / "v3_magnitude_objective_results.md").write_text(
        magnitude_report, encoding="utf-8"
    )

    coverage_lines = "\n".join(
        f"| {int(row.coverage * 100)}% | {int(row.decision_count)} | {row.rank_percentile:.6f} | {row.normalized_regret:.6f} | {row.selected_utility:.6f} | {row.meaningful_effect_rate:.3f} | {row.near_oracle_rate:.3f} |"
        for row in coverage.itertuples()
    )
    selective_report = f"""# RNAddress v3 Phase 3 selective-prediction results

## Verdict

The frozen five-signal confidence score did **not** reliably predict recommendation failure. Confidence versus normalized regret had Spearman rho `{selective['gate_J']['confidence_regret_spearman']:.6f}` (required at most `-0.20`). At 60% coverage, regret improved by only `{selective['gate_J']['regret_improvement_at_60_percent']:.6f}` (required at least `0.030`), and regret was not monotonic from 100% to 80% to 60% coverage.

## Coverage curve

| Coverage | Decisions | Rank percentile | Normalized regret | Selected utility | Meaningful-effect rate | Near-oracle rate |
|---:|---:|---:|---:|---:|---:|---:|
{coverage_lines}

The score used only outcome-free nested signals: rank–magnitude disagreement, base–extreme disagreement, nearest-training-parent contextual distance, top-1/top-2 score margin, and three-seed score standard deviation. Each was converted to an outer-training empirical support percentile and averaged without learned weights. No Astrocyte threshold was selected.

The 80% subset increased selected utility but slightly worsened regret; 60% improved rank substantially but not regret enough; 40% was reported as required but was not used to rescue the failed gate. Abstention is therefore not retained as a validated Phase 3 safeguard.
"""
    (REPORTS / "v3_selective_prediction_results.md").write_text(
        selective_report, encoding="utf-8"
    )

    failed_text = ", ".join(failed)
    final_report = f"""# RNAddress v3 Phase 3 model selection

## Decision

# NO-GO

The development-best architecture was `{NAME}`, but it failed frozen gate sections {failed_text}. It is **not** strong enough to justify spending the untouched Astrocyte benchmark.

## Best candidate

The model uses the pinned 3UTRBERT 3-mer representation with CLS, global, affected-3-mer and radius-10 mutant-minus-parent deltas plus the frozen edit vector; the pruned mechanistic block; nested Ridge rank regression; nested Ridge/Huber raw-magnitude prediction; an outer-cross-fitted rank/magnitude stack; and direction-specific top-decile extreme logistic heads. Evaluation was outer leave-one-parent-out with all learned choices nested inside the 14 training parents.

It reached rank percentile `{selected['rank_percentile']:.6f}`, normalized regret `{selected['normalized_regret']:.6f}`, selected utility `{selected['selected_utility']:.6f}`, near-oracle recovery `{selected['near_oracle']:.3f}`, and mean oracle rank `{selected['mean_oracle_rank']:.3f}`. Exact oracle recovery was top-1 `{selected['oracle_top1']:.3f}`, top-3 `{selected['oracle_top3']:.3f}`, and top-5 `{selected['oracle_top5']:.3f}`—all `0/30`.

## Why it was the development best

It preserved rank and beat the strongest fair forward comparator `{forward_name}` on rank, regret and selected utility. It also beat metadata shortcuts and passed the two frozen complexity comparisons: pruned mechanism over contextual rank+magnitude, and extreme head over pruned mechanism.

## Why it was rejected

The regret gain over v2.6 was only `{v2['normalized_regret'] - selected['normalized_regret']:.6f}` instead of `0.030`. Oracle top-5 remained `0/30`, near-oracle recovery was `3/30` rather than at least `6/30`, and mean oracle rank was `{selected['mean_oracle_rank']:.3f}` rather than at most `90`. Although 9/15 parents improved and median parent gain was positive, removing the best one or two parents made mean gain negative. The shuffled-label control rank was `{controls.loc['within_parent_shuffled_labels_complete_pipeline','rank_percentile']:.6f}`, above the `0.530` ceiling. Seeds 20260829/30 improved regret by only `{v2['normalized_regret'] - seed_metrics.loc[seed_metrics.seed == 20260829,'normalized_regret'].iloc[0]:.6f}`. Confidence failed gate J.

## What changed from v2.6

v3 explicitly separated broad rank, raw effect magnitude, rare extreme-benefit probability and support estimation. It added parent × edit × mechanism interactions and TDP-derived sequence-only stability auxiliary supervision while keeping N-zip as the sole final SNV calibration task. This improved rank and selected utility but did not make experimentally best or near-best edit discovery reliable enough.

## Representation question

3UTRBERT won the matched benchmark with score `{rep['representation_selection_score']:.6f}` versus `{representation.loc['splicebert_1024nt','representation_selection_score']:.6f}` for SpliceBERT. The combined delta-plus-edit rank model reached `{rep_rows.loc['combined_delta_plus_edit','rank_percentile']:.6f}`; parent-only was `{rep_rows.loc['parent_absolute','rank_percentile']:.6f}`, mutant-only `{rep_rows.loc['mutant_absolute','rank_percentile']:.6f}`, global delta `{rep_rows.loc['global_mutant_minus_parent_delta','rank_percentile']:.6f}`, and local delta `{rep_rows.loc['local_edited_region_delta','rank_percentile']:.6f}`. Explicit intervention representation was essential.

## Magnitude, extreme and mechanism questions

Direct magnitude alone failed. Rank+magnitude stacking also underperformed v2.6. Pruning motif interactions revealed a useful mechanism block, and the stability and parent-state families survived grouped ablation, but local accessibility did not show an independent gain. The extreme head improved rank/composite score yet found no exact oracle in the top five. TDP stability was auxiliary development evidence only, never independent validation, and no measured stability is required at inference.

## Uncertainty question

The frozen multi-signal confidence score did not pass its predictive or selective-regret criteria. Coverage results are reported without selecting an Astrocyte threshold.

## Integrity and stop

Astrocyte outcomes were not inspected, analyzed, recorded or used for v3 development; the inherited historical test that programmatically loaded the complete worksheet remains disclosed. The sealed Moffatt archive was not listed, opened, extracted or used. All 30 tests in nine files passed when each file ran in a clean process. Monolithic Windows pytest collection is not usable because combined import order intermittently causes a native ViennaRNA DLL initialization/access-violation failure; the standalone ViennaRNA import and all six v3 tests pass. Phase 3 stops here: no Astrocyte preregistration, predictions, reveal, Moffatt inspection, external-validation claim or UI work is authorized.
"""
    (REPORTS / "v3_phase3_model_selection.md").write_text(
        final_report, encoding="utf-8"
    )

    git_revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    result_hashes = {
        path.relative_to(ROOT).as_posix(): _hash(path)
        for path in sorted(OUT.iterdir())
        if path.is_file() and path.name != "reproducibility_manifest.json"
    }
    source_hashes = {
        path.relative_to(ROOT).as_posix(): _hash(path)
        for path in sorted((ROOT / "src").rglob("*.py"))
        if "v3" in path.name
    }
    report_hashes = {
        path.relative_to(ROOT).as_posix(): _hash(path)
        for path in (
            REPORTS / "v3_phase3_development_protocol.md",
            REPORTS / "v3_representation_benchmark.md",
            REPORTS / "v3_mechanistic_feature_audit.md",
            REPORTS / "v3_magnitude_objective_results.md",
            REPORTS / "v3_selective_prediction_results.md",
            REPORTS / "v3_phase3_model_selection.md",
        )
    }
    representation_manifest = _read_json("representation_manifest.json")
    manifest = {
        "phase": "v3_phase3_complete",
        "decision": "NO-GO",
        "generated_from_git_revision": git_revision,
        "starting_commit": "54fa859ff48b03ddca1d9b15c1f3a46b9b0bfd79",
        "foundation_model": {
            "name": "yangheng/3utrbert",
            "checkpoint_revision": "220d80829deb077d1d640463a4267a96e9e70b1d",
        },
        "rows": 4395,
        "parents": 15,
        "selection_units": 30,
        "seeds": [20260828, 20260829, 20260830],
        "feature_cache_hashes": representation_manifest["feature_cache_hashes"],
        "result_hashes": result_hashes,
        "source_hashes": source_hashes,
        "report_hashes": report_hashes,
        "versions": _package_versions(),
        "test_verification": {
            "test_files_passed": 9,
            "tests_passed": 30,
            "execution": "one clean Python process per test file",
            "monolithic_collection_deviation": "ViennaRNA native DLL initialization/access violation under combined Windows import order",
            "standalone_viennarna_import_passed": True,
            "v3_test_file_passed": True,
        },
        "protected_data_access": {
            "astrocyte_outcomes_opened": False,
            "moffatt_archive_opened": False,
            "historical_inherited_astrocyte_full_worksheet_test_load_disclosed": True,
        },
        "exclusions": {
            "HydraRNA": "official stack incompatible with reproducible Windows CPU host; no performance claim",
            "measurement_aware_target": "deterministic replicate uncertainty reconstruction infeasible",
        },
    }
    (OUT / "reproducibility_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"decision": "NO-GO", "failed": failed}, indent=2))


if __name__ == "__main__":
    main()
