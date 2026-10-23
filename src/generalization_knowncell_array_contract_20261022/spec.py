"""Fixed simple102 contract and bounded, scalar-only ZIP/NPY inspection."""
from pathlib import Path
from src.generalization_knowncell_joint_design_20261009.spec import ALIASES, COUNTS, FEATURE_WIDTH

NS = 'generalization_knowncell_array_contract_20261022'
ROOT = Path(__file__).resolve().parents[2]
SRC, REP, OUT = [ROOT / name / NS for name in ('src', 'reports', 'results')]
SHAPE = (COUNTS['all_rows'], FEATURE_WIDTH)
MAX_NPZ_BYTES = 32 * 2**20
# 11.3 decimal MB is an intentionally concrete bound, also below11.3MiB.
# Canonical full simple102 data occupy11,245,296 bytes, with a small NPY header.
MAX_NPY_BYTES = 11_300_000
MAX_HEADER_BYTES = 4096
NPZ_MEMBER = 'features.npy'
STATUS = 'VALIDATED_SUPPLIED_ARRAY_BYTES_NOT_PROJECT_ADMISSION'
CREATION_RECEIPT = 'results/generalization_crosscell_20261007/prepare_receipt.json'
METADATA_RECEIPT = 'results/generalization_crosscell_20261007/metadata_receipt.json'
SOURCE_PREFIT = 'results/generalization_crosscell_20261007/prefit_manifest.json'
REFERENCE_READY = 'results/generalization_knowncell_joint_implementation_20261022/implementation_readiness.json'
