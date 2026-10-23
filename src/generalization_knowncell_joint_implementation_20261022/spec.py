"""Import only the immutable, standard-library design constants."""
from src.generalization_knowncell_joint_design_20261009.spec import (
    ARMS, CELLS, CELL_SIGNS, FOLDS, CONFIGS, DEVIATION_MULTIPLIER,
    FEATURE_WIDTH, COUNTS, GATE, ALIASES, METADATA_COLUMNS,
)

NS = 'generalization_knowncell_joint_implementation_20261022'
DESIGN_NS = 'generalization_knowncell_joint_design_20261009'
DESIGN_MANIFEST = 'results/' + DESIGN_NS + '/design_manifest.json'
SUPPORTED_RMS = 1e-8
REPLAY_TOLERANCE = 1e-9
RAM_BYTES = 3 * 2**30
DISK_BYTES = 2**30
# This permitted design choice is now fixed for a future, separately frozen fitter.
# A common zero mean avoids an extra preprocessing convention. Pair scores are
# identical to any common translation; primary exact-tie semantics still use
# the eventual canonical full-matrix numerical scorer.
CANONICAL_MEAN = 'all_zero_102_vector'


def fixed_contract():
    assert ARMS == ('pooled', 'independent', 'joint_shrink10')
    assert CELL_SIGNS == {'CAD': 1, 'Neuro-2a': -1}
    assert FOLDS == (0, 1, 2) and FEATURE_WIDTH == 102
    assert CONFIGS == ({'id': 'pair_005', 'penalty': .005},
                       {'id': 'pair_05', 'penalty': .05},
                       {'id': 'pair_5', 'penalty': .5})
    assert DEVIATION_MULTIPLIER == 10.
    return True
