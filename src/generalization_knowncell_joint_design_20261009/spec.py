"""Fixed exposed-data reassessment. Constants do not load any project inputs."""
NS = "generalization_knowncell_joint_design_20261009"
PREPARED_DATE = "2026-10-21"
ARMS = ("pooled", "independent", "joint_shrink10")
CELLS = ("CAD", "Neuro-2a")
CELL_SIGNS = {"CAD": 1, "Neuro-2a": -1}
FOLDS = (0, 1, 2)
CONFIGS = (
    {"id": "pair_005", "penalty": .005},
    {"id": "pair_05", "penalty": .05},
    {"id": "pair_5", "penalty": .5},
)
DEVIATION_MULTIPLIER = 10.0
FEATURE_WIDTH = 102
COUNTS = {
    "all_rows": 13781, "CAD_rows": 6889, "Neuro-2a_rows": 6892,
    "components": 187, "paired_menus": 2408, "paired_rows": 13760,
    "paired_contexts": 4816, "paired_directional_decisions": 9632,
    "unmatched_contexts": 9, "unmatched_rows": 21,
    "inner_arm_checkpoints": 54, "outer_arm_checkpoints": 9,
    "arm_checkpoints": 63, "inner_optimizer_units": 72,
    "outer_optimizer_units": 12, "optimizer_units": 84,
}
GATE = {
    "macro_regret_max": .48, "each_cell_regret_strict_max": .5,
    "gain_macro_min": .01, "gain_each_cell_min": .005,
    "bootstrap_lower_strict_min": 0., "wrong_harm_macro_max": .02,
    "wrong_harm_each_cell_max": .05, "leave_best_fold_gain_strict_min": 0.,
    "bootstrap_draws": 5000, "bootstrap_seed": 20261007,
}
ALIASES = {
    "core": "results/probabilistic_ranking_20260928/candidate_index.csv",
    "feature": "artifacts/generalization_crosscell_20261007/simple_model_features.npz",
    "source_prefit": "results/generalization_crosscell_20261007/prefit_manifest.json",
    "source_metadata": "results/generalization_crosscell_20261007/metadata_receipt.json",
    "known_metadata": "results/generalization_knowncell_20261007/metadata_receipt.json",
    "paired_menu_inventory": "results/generalization_knowncell_20261007/exact_menu_pairs.csv",
    "unmatched_inventory": "results/generalization_knowncell_20261007/unmatched_menu_metadata.csv",
}
METADATA_COLUMNS = (
    "intervention_id", "dataset", "cell_type", "endpoint_class", "parent_context_id",
    "biological_component", "gene_transcript", "held_parent_fold",
    "parent_sequence", "mutant_sequence",
)
POLICY = {
    "status": "STATIC_DESIGN_ONLY_NO_PROJECT_INPUT_ADMISSION",
    "scope": "Known represented cells, unseen genes, exposed Mikl development data",
    "novel_method": False, "independent_confirmation": False,
    "unknown_cell_generalization": False,
    "primary": "All exact full paired menus; equal cell/gene/menu/direction regret",
    "training": "All source rows in both represented cells outside held gene folds",
    "secondary": "All13781 rows and unmatched21 rows reported, never used to rescue gate",
    "source_only_selection": "One common lambda per arm chosen from concatenated inner OOF paired decisions",
    "selection_tie": "Within1e-12 of minimum, first fixed config order .005/.05/.5",
    "choice_tie": "Exact canonical scores, original intervention-ID lexical order",
    "unsupported": "Common training pair-RMS<1e-8 freezes shared and all cell coefficients0",
    "new_scientific_entrypoints": False,
    "future_fresh_RAM_GiB": 3., "future_workspace_disk_GiB": 1.,
    "future_numerical_threads": 1,
    "PUM_resource_exception_applies": False,
}
