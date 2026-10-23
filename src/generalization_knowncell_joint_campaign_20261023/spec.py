from src.generalization_knowncell_joint_implementation_20261022.spec import (
    ARMS, CELLS, CONFIGS, COUNTS, FOLDS, FEATURE_WIDTH, CANONICAL_MEAN,
)
from src.generalization_knowncell_joint_numeric_20261022.spec import METHOD, OPTIONS, SCORER

NS='generalization_knowncell_joint_campaign_20261023'
PREFIT_STATUS='FROZEN_JOINT_KNOWNCELL_CAMPAIGN_PREFIT_NOT_EXECUTION_AUTHORIZATION'
POOL_HASH_FIELDS=('training_metadata_sha256','training_features_sha256','training_effects_sha256',
                  'original_pair_roster_sha256','pair_weights_sha256','common_scaling_sha256',
                  'validation_metadata_sha256','validation_features_sha256','validation_effects_sha256')
SOURCE_MANIFESTS=(
    'results/generalization_knowncell_joint_design_20261009/design_manifest.json',
    'results/generalization_knowncell_joint_implementation_20261022/implementation_readiness.json',
    'results/generalization_knowncell_joint_numeric_20261022/preparation_manifest.json',
)
