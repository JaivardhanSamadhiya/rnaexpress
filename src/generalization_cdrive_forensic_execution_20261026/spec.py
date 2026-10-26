"""Prospective fixed forensic owner, software and read-only source bindings."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
EXPECTED_ROOT = Path('C:/Users/jaisa/rnaexpress-recovery-20261025/material_snapshot_20261025/workspace')
NS = 'generalization_cdrive_forensic_execution_20261026'
SRC,REP,OUT,ART = (ROOT/kind/NS for kind in ('src','reports','results','artifacts'))
MANIFEST = OUT/'execution_manifest.json'
BIRTH = OUT/'forensic_attempt_birth.json'
CHILD_IDENTITY = OUT/'owned_child_identity.json'
CHILD_OWNER = OUT/'owned_child_started.json'
REPORT = OUT/'forensic_report.json'
COMPLETION = OUT/'forensic_worker_completion.json'
SUPERVISOR = OUT/'forensic_supervisor_receipt.json'
JOURNAL = OUT/'parent.jsonl'
FAULT_LOG = OUT/'worker_fault.log'
STAGE = 'read_only_checkpoint_forensics'
STATUS = 'FROZEN_CDRIVE_READONLY63_FORENSIC_SOURCE_NOT_FIT_RETRY'
REPORT_STATUS = 'ACTUAL_SEPARATE_READONLY63_FORENSICS_NOT_ACCEPTED_CAMPAIGN'
WORKER_PASS = 'PASS_NEW_FORENSIC_WORKER_NOT_OLD_CAMPAIGN_CLOSURE'
PARENT_PASS = 'PASS_NEW_READONLY_FORENSIC_JOB_NOT_FORMAL_REPLAY_OR_GATE'
CORE_MANIFEST = ROOT/'results/generalization_cdrive_checkpoint_forensics_20261026/source_preparation_manifest.json'
CORE_MANIFEST_SHA = 'c0ca8fcc1e326ac663f7edbd72b35c42a7457b182ebab9d431b0f707be94b60d'
PROFILE_MANIFEST = ROOT/'results/generalization_cdrive_numeric_profile_20261025/preparation_manifest.json'
PROFILE_MANIFEST_SHA = 'd732628ebaaa1840e0f8d173fc03f359729310333fbab3794703742a86b3400b'
PROFILE_CERTIFICATE = ROOT/'results/generalization_cdrive_numeric_profile_20261025/verified_current_status.json'
PROFILE_CERTIFICATE_SHA = 'ff05569d74dfc37a26a3f8ed57ba05549d27dc1abdf41f1e153b8eeeeb02dfed'
PROFILE_RECEIPT = ROOT/'results/generalization_cdrive_numeric_profile_20261025/receipt.json'
PROFILE_RECEIPT_SHA = 'd14659258b5ec76ca2c1e687a55d25352f51cc3296e5663e32bffd1fbddda527'
INVENTORY = ROOT/'results/generalization_cdrive_software_inventory_20261025/current_python_inventory_cdrive.json'
INVENTORY_SHA = '34ff960c2e0a69f724eff36324f72dec8c8208c48c93f6ddfd3ed7db2fa7ee33'
SOURCE_CACHE = ROOT/'results/generalization_knowncell_runtime_provider_20261023/source_cache_must_remain_absent'
THREAD_ENV = {key:'1' for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}
THREAD_ENV.update(PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
PRIVATE_CAP,JOB_CAP,RESIDENT_REQUEST,RESIDENT_CEILING = 768*2**20,896*2**20,190*2**20,192*2**20
DEADLINE = 1800
JOB_LIMITS = {'process_memory_limit':PRIVATE_CAP,'job_memory_limit':JOB_CAP,'active_process_limit':2,'limit_flags':8968}
HISTORICAL_PREFIT='results/generalization_knowncell_prefit_execution_20261024/prefit_manifest.json'
HISTORICAL_PREFIT_SHA='1556b08726430ec5b9d9aca276687b2825ef4d076b01d7bf97ddb9d1fc3ad134'
HISTORICAL_PROJECTION='results/generalization_knowncell_prefit_projection_v2_20261024/root_prefit_admission.json'
HISTORICAL_PROJECTION_SHA='10075cac07c259153d1b223a101a974be3d11f59c3f375e47aa52eef627dfd68'
HISTORICAL_PREFIT_COMMIT='46101eed4a050a954afaa4868a8de3fbb884ec31'
SAVED_AUDIT=ROOT/'results/generalization_knowncell_paged_interruption_audit_20261025/interrupted_fit_audit.json'
SAVED_AUDIT_SHA='e2a58d36e70cb7e1aa54a8ff7b0ae16f21f5efd26b69b0f05abb516efdcdbf8d'
CHECKPOINT_PREFIX='results/generalization_knowncell_fit_paged_execution_20261025/campaign/checkpoints/'
OLD_MISSING=tuple(ROOT/name for name in (
    CHECKPOINT_PREFIX+'campaign_complete.json',
    'results/generalization_knowncell_fit_paged_execution_20261025/fit_lifecycle_report.json',
    'results/generalization_knowncell_fit_paged_execution_20261025/fit_worker_completion.json',
    'results/generalization_knowncell_fit_paged_execution_20261025/fit_supervisor_receipt.json'))
