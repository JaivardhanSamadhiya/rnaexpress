"""Only immutable source constants are imported; no scientific bootstrap."""
from pathlib import Path
from src.generalization_knowncell_joint_design_20261009.spec import ALIASES, METADATA_COLUMNS, COUNTS

NS = 'generalization_knowncell_joint_loader_20261022'
ROOT = Path(__file__).resolve().parents[2]
SRC, REP, OUT = [ROOT / name / NS for name in ('src', 'reports', 'results')]
REFERENCE_READY = 'results/generalization_knowncell_joint_implementation_20261022/implementation_readiness.json'
DESIGN_MANIFEST = 'results/generalization_knowncell_joint_design_20261009/design_manifest.json'
KNOWN_EVALUATION = 'results/generalization_knowncell_20261007/evaluation_manifest.json'
ALL_CORE_ROWS = 26258
FIRST_READY_PATH = 'results/' + NS + '/readiness_manifest.json'
READY_PATH = 'results/' + NS + '/readiness_manifest_reviewed.json'
METADATA_ADMISSION = 'results/' + NS + '/metadata_admission_manifest.json'
FIT_ADMISSION = 'results/' + NS + '/fit_label_admission_manifest.json'
METADATA_BUNDLE = 'results/' + NS + '/admitted_metadata.json'
PANDAS_ADMISSION = 'results/' + NS + '/pandas_admission.json'
ARRAY_ADMISSION = 'results/' + NS + '/simple102_array_admission.json'
METADATA_STATUS = 'FROZEN_METADATA_ADMISSION_JOINT_KNOWNCELL'
FIT_STATUS = 'FROZEN_MIKL_MEAN_EFFECT_ADMISSION_JOINT_KNOWNCELL'
PANDAS_STATUS = 'PASS_PINNED_PANDAS223_CURRENT_PYTHON_AND_INVENTED_ORIGINAL_PARSER'
PANDAS_TEST_STATUS = 'PASS_PINNED_PANDAS_DEFAULT_CSV_OPTIONS_RESULTS'
ARRAY_STATUS = 'PASS_EXACT_FROZEN_SIMPLE102_ROWS_VALUES_AND_ALLELE_PARITY'
# Already certified by the earlier owned-process helper. A later mismatch
# stops admission; there is no PATH/shim/fallback helper selection.
DIRECT_GIT = Path('C:/Program Files/Git/mingw64/bin/git.exe')
DIRECT_GIT_SHA256 = '51c6331aab2426ae2df187975590587b5a10042e3423f4bc0fdcb54aeb3efab7'
