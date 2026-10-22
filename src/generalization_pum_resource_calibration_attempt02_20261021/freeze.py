"""Freeze exact approved operational exception before real cohort execution."""
import hashlib,json,pathlib,sys
from . import worker
from src.generalization_pum_resource_calibration_20261009 import winjob
ROOT=worker.ROOT;OUT=worker.OUT

def run():
 own=sorted((ROOT/'src'/OUT.name).glob('*.py'))+sorted((ROOT/'reports'/OUT.name).glob('*'))+sorted(p for p in OUT.iterdir() if p.is_file() and p.name!='execution_manifest.json')+[(ROOT/'src'/OUT.name/'.gitattributes')]
 files={p.relative_to(ROOT).as_posix():worker.sha(p) for p in own}
 scientific=set()
 for name in ('results/generalization_pum2_fixed_math_20261008/feature_manifest.json','results/generalization_pum2_independent_replay_20261009/replay_manifest.json'):
  p=ROOT/name;m=json.loads(p.read_text());files[name]=worker.sha(p);scientific.add(name)
  for rel,want in m['files'].items():
   assert worker.sha(ROOT/rel)==want,rel
   files[rel]=want;scientific.add(rel)
 # Pin every explicitly approved scientific entry point and numerical helper too.
 for rel in ('src/generalization_pum2_fixed_math_20261008/produce_features.py','src/generalization_pum2_fixed_math_20261008/model.py','src/generalization_pum2_independent_replay_20261009/run.py','src/generalization_pum2_independent_replay_20261009/numeric.py'):
  files[rel]=worker.sha(ROOT/rel);scientific.add(rel)
 callback=json.loads((OUT/'callback_tests_receipt_v2.json').read_text())
 assert callback['status']=='PASS_3_INVENTED_CALLBACK_SCOPE_AND_TRUTHFUL_RECEIPT_TESTS'
 for rel,h in callback['files'].items():assert worker.sha(ROOT/rel)==h
 kernel=json.loads((OUT/'winjob_synthetic_tests_final_v2.json').read_text())
 assert kernel['failures']==kernel['errors']==kernel['skipped']==0 and kernel['native_invented_child_cases']==3
 for rel,h in kernel['files'].items():assert worker.sha(ROOT/rel)==h,rel
 approval=json.loads((OUT/'explicit_user_approval.json').read_text());assert approval['answer']=='Approve this exact bounded PUM calibration'
 helper=pathlib.Path('C:/Program Files/Git/mingw64/bin/git.exe')
 assert worker.sha(helper)=='51c6331aab2426ae2df187975590587b5a10042e3423f4bc0fdcb54aeb3efab7'
 data={'status':'FROZEN_TWO_PUM_CALLBACK_RESOURCE_CALIBRATION_ONLY','files':files,'scientific_files':sorted(scientific),'git_helper':{'path':str(helper),'sha256':worker.sha(helper),'routing':'Only childPATH to actualGitbinary; active cap2 unchanged'},'python_executable':sys.executable,'python_executable_sha256':worker.sha(pathlib.Path(sys.executable)),'process_cap_bytes':768*2**20,'job_cap_bytes':896*2**20,'active_process_cap':2,'fresh_physical_bytes':512*2**20,'start_system_commit_headroom_bytes':896*2**20+2**30,'stop_physical_bytes':256*2**20,'stop_system_commit_headroom_bytes':2**30,'monitor_interval_seconds':.1,'phase_deadline_seconds':1800,'real_cohort_or_outcomes_read_before_freeze':False,'other_scientific_floors_unchanged':True,'scientific_arithmetic_data_IDs_modes_tolerance_unchanged':True,'only_truthful_resource_disclosure_added_to_original_receipts':True,'requires_commit_before_execution':True}
 worker.save(OUT/'execution_manifest.json',data);print('PUM_EXECUTION_FREEZE',len(files),worker.sha(OUT/'execution_manifest.json'))
if __name__=='__main__':run()
