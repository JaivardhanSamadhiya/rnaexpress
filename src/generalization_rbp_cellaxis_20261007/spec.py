"""Fixed existing representations and existing cell-axis numerical policy."""
NS = 'generalization_rbp_cellaxis_20261007'
TRACKS = ['simple', 'base', 'raw', 'access', 'duplicate_marginal', 'joint']
WIDTHS = dict(zip(TRACKS, [102, 246, 502, 758, 1014, 1014]))
NEW_FIT_TRACKS = ['raw', 'access', 'duplicate_marginal', 'joint']
REUSED_CONTROLS = ['simple', 'base']
INFORMED = ['raw', 'access', 'joint']
INFORMATION_CONTROLS = {'raw': [], 'access': ['raw'],
                        'joint': ['access', 'duplicate_marginal']}
CONFIGS = [{'id': 'pair_005', 'penalty': .005, 'scaling': 'pair'},
           {'id': 'pair_05', 'penalty': .05, 'scaling': 'pair'},
           {'id': 'pair_5', 'penalty': .5, 'scaling': 'pair'}]
TASKS = {'CAD_to_N2A': ('CAD', 'Neuro-2a'), 'N2A_to_CAD': ('Neuro-2a', 'CAD')}
KNOWN_TASKS = {'CAD_known': ('CAD', 'CAD_to_N2A'),
               'N2A_known': ('Neuro-2a', 'N2A_to_CAD')}
FOLDS = [0, 1, 2]
SEED = 20261007
ROWS = 13781
COMPONENTS = 187
CORE_ROWS = 26258
META = ['intervention_id', 'dataset', 'cell_type', 'endpoint_class',
        'parent_context_id', 'biological_component', 'gene_transcript',
        'held_parent_fold', 'parent_sequence', 'mutant_sequence']
IDENTITY = ['intervention_id', 'dataset', 'biological_component',
            'parent_context_id', 'parent_sequence', 'mutant_sequence']
NEW_CHECKPOINTS = 168
NEW_INNER_CHECKPOINTS = 144
NEW_OUTER_CHECKPOINTS = 24
REUSED_CHECKPOINTS = 84
REUSED_OUTER_CHECKPOINTS = 12
NUMERICAL_THREADS = 1

# Unchanged crossed-cell AND represented-cell main numerical thresholds.
GATE = {'macro_regret_max': .48, 'each_cell_regret_strict_max': .5,
        'baseline_macro_gain_min': .01, 'baseline_each_cell_gain_min': .005,
        'bootstrap_lower_strict_min': 0., 'macro_wrong_harm_max': .02,
        'each_cell_wrong_harm_max': .05, 'leave_best_gain_strict_min': 0.,
        'information_macro_gain_min': .01, 'information_leave_best_strict_min': 0.,
        'bootstrap_draws': 5000, 'bootstrap_seed': SEED}
