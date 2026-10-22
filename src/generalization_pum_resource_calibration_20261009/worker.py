"""Only the two explicitly approved PUM resource callbacks are process-local."""
import datetime,hashlib,importlib,json,os,pathlib,shutil,subprocess,sys,time
from contextlib import contextmanager
from . import winjob
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=ROOT/'results/generalization_pum_resource_calibration_20261009'
MODULES={'production':'src.generalization_pum2_fixed_math_20261008.produce_features','replay':'src.generalization_pum2_independent_replay_20261009.run'}
GUARDS={'production':'fresh_guard','replay':'guard'}
RECEIPTS={'production':ROOT/'results/generalization_pum2_fixed_math_20261008/feature_production_receipt.json','replay':ROOT/'results/generalization_pum2_independent_replay_20261009/independent_feature_replay_receipt.json'}
def sha(path):
 h=hashlib.sha256()
 with pathlib.Path(path).open('rb') as f:
  for x in iter(lambda:f.read(1048576),b''):h.update(x)
 return h.hexdigest()
def save(path,data):
 with pathlib.Path(path).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(data,indent=2,allow_nan=False)+'\n')
def admitted():
 p=OUT/'execution_manifest.json';data=p.read_bytes();m=json.loads(data)
 assert pathlib.Path(sys.executable).resolve()==pathlib.Path(m['python_executable']).resolve() and sha(sys.executable)==m['python_executable_sha256']
 assert sys.implementation.name=='cpython' and sys.version_info[:2]==(3,12) and sys.implementation.cache_tag=='cpython-312'
 helper=pathlib.Path(m['git_helper']['path'])
 assert helper==pathlib.Path('C:/Program Files/Git/mingw64/bin/git.exe') and sha(helper)==m['git_helper']['sha256']
 assert subprocess.check_output([str(helper),'show','HEAD:'+p.relative_to(ROOT).as_posix()],cwd=ROOT)==data
 assert m['status']=='FROZEN_TWO_PUM_CALLBACK_RESOURCE_CALIBRATION_ONLY'
 for rel,want in m['files'].items():assert sha(ROOT/rel)==want,rel
 return p,m
def resource_guard():
 v=winjob.memory()
 assert v['physical_available']>=512*2**20,'Approved fresh512MiB physical admission not met'
 assert v['commit_headroom']>=896*2**20+2**30,'Approved system commit admission not met'
 assert v['disk_available']>=2**30,'Fresh1GiB workspace disk admission not met'
 return v['physical_available']
@contextmanager
def scoped_callbacks(module,phase,manifest_sha):
 name=GUARDS[phase];original_guard=getattr(module,name);original_save=module.save
 def transparent_save(path,payload):
  if pathlib.Path(path)==RECEIPTS[phase]:
   payload=dict(payload)
   if 'all_existing_model_feature_floors_unchanged' in payload:payload['all_existing_model_feature_floors_unchanged']=False
   payload['resource_admission_original_3GiB_overridden']=True
   payload['authorized_resource_calibration_manifest_sha256']=manifest_sha
   payload['scientific_code_data_modes_tolerance_unchanged']=True
  return original_save(path,payload)
 setattr(module,name,resource_guard);module.save=transparent_save
 try:yield
 finally:setattr(module,name,original_guard);module.save=original_save

def run(phase,supervisor):
 assert phase in MODULES and os.getppid()==supervisor
 # Child was created suspended, attached and verified before any Python executes.
 with (OUT/(phase+'_worker.log')).open('x',encoding='utf-8',newline='\n',buffering=1) as log:
  sys.stdout=log;sys.stderr=log
  try:
   p,m=admitted();resource_guard()
   helper=pathlib.Path(m['git_helper']['path']);os.environ['PATH']=str(helper.parent)+os.pathsep+os.environ['PATH']
   assert pathlib.Path(shutil.which('git')).resolve()==helper.resolve(),'Pinned direct Git helper routing failed'
   module=importlib.import_module(MODULES[phase])
   before={rel:sha(ROOT/rel) for rel in m['scientific_files']}
   with scoped_callbacks(module,phase,sha(p)):module.run()
   assert all(sha(ROOT/rel)==want for rel,want in before.items())
   print('ORIGINAL_SCIENTIFIC_BYTES_UNCHANGED',phase,flush=True)
  except BaseException:
   import traceback;traceback.print_exc();raise
if __name__=='__main__':run(sys.argv[1],int(sys.argv[2]))
