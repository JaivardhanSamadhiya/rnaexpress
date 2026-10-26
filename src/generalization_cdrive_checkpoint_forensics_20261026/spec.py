"""Source-only forensic scope; none of these declarations grants execution."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NS = 'generalization_cdrive_checkpoint_forensics_20261026'
SRC, REP, OUT, ART = (ROOT/kind/NS for kind in ('src','reports','results','artifacts'))
C_WORKSPACE = Path('C:/Users/jaisa/rnaexpress-recovery-20261025/material_snapshot_20261025/workspace')
SOFTWARE_INVENTORY = 'results/generalization_cdrive_software_inventory_20261025/current_python_inventory_cdrive.json'
SOFTWARE_INVENTORY_SHA = '34ff960c2e0a69f724eff36324f72dec8c8208c48c93f6ddfd3ed7db2fa7ee33'
NUMERICAL_PROFILE = 'results/generalization_cdrive_numeric_profile_20261025/receipt.json'
NUMERICAL_PROFILE_SHA = 'd14659258b5ec76ca2c1e687a55d25352f51cc3296e5663e32bffd1fbddda527'
SOFTWARE_CERTIFICATE = 'results/generalization_cdrive_numeric_profile_20261025/verified_current_status.json'
SOFTWARE_CERTIFICATE_SHA = 'ff05569d74dfc37a26a3f8ed57ba05549d27dc1abdf41f1e153b8eeeeb02dfed'
STAGE = 'read_only_checkpoint_forensics'
NUMERICAL_STATUS = 'PASS_READONLY_SAVED_CHECKPOINT_NUMERIC_CONSISTENCY_NOT_CAMPAIGN'
SUPPLIED_STATUS = 'PASS_FORENSIC_SAVED63_NUMERIC_CONSISTENCY_NOT_CLOSED_CAMPAIGN'
SOURCE_STATUS = 'PREPARED_FORENSIC_SUPPLIED_KERNELS_NOT_EXECUTION_OR_DATA_ADMISSION'
TOLERANCE = 1e-9
CHECKPOINTS, INNER, OUTER, POOLS, RECORDED_UNITS = 63, 54, 9, 9, 84
SOURCE_SELECTIONS = 9
RESOURCE_POLICY = {
    'startup_physical_floor':512*2**20,'live_physical_floor':256*2**20,
    'startup_commit_headroom':1920*2**20,'live_commit_and_disk_floor':2**30,
    'private_process_cap':768*2**20,'job_cap':896*2**20,'active_process_limit':2,
    'requested_resident_maximum':190*2**20,'measured_resident_ceiling':192*2**20,
    'numerical_threads':1,'total_deadline_seconds':1800,
}
MISSING_OLD_TERMINALS = ('campaign_complete.json','fit_report.json',
                         'worker_completion.json','supervisor_receipt.json')
