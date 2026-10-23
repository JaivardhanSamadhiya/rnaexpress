"""Fixed contracts; no numerical library imports or project input access."""
from src.generalization_knowncell_joint_implementation_20261022.spec import (
    ARMS, CELLS, CELL_SIGNS, CONFIGS, DEVIATION_MULTIPLIER, FEATURE_WIDTH,
    SUPPORTED_RMS, CANONICAL_MEAN,
)

NS = 'generalization_knowncell_joint_numeric_20261022'
METHOD = 'L-BFGS-B'
OPTIONS = {'maxiter': 500, 'ftol': 1e-11, 'gtol': 1e-7}
REFERENCE_READINESS = 'results/generalization_knowncell_joint_implementation_20261022/implementation_readiness.json'
DESIGN_MANIFEST = 'results/generalization_knowncell_joint_design_20261009/design_manifest.json'
HISTORICAL_SOLVER_SOURCE = 'src/cross_assay_20260927/models.py'
SCORER = 'float64_C_full102_zero_mean_both_complete_cell_heads_then_select'
