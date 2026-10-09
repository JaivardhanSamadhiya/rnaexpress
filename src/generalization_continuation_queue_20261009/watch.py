"""Single owned serial background continuation, not a scheduled task."""
from pathlib import Path
import ctypes,datetime,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/generalization_continuation_queue_20261009'
LOG=ROOT/'logs/generalization_campaign_20261007'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
 with p.open('xb') as f:f.write((json.dumps(x,indent=2,sort_keys=True,allow_nan=False)+'\n').encode())
def available():
 class M(ctypes.Structure):
  _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(x,ctypes.c_ulonglong) for x in ('total','available','page_total','page_available','virtual_total','virtual_available','extended')]
 m=M();m.length=ctypes.sizeof(m);assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
 return m.available
def other_workers():
 command="Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^python' -and $_.ProcessId -ne "+str(os.getpid())+" -and ($_.CommandLine -match 'generalization_' -or $_.CommandLine -match '-m src[.]') } | Select-Object -ExpandProperty ProcessId"
 result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',command],capture_output=True,timeout=20)
 assert result.returncode==0,'Cannot certify no competing project Python workers'
 return [int(x) for x in result.stdout.decode().split() if x.strip()]
def run():
 assert sys.argv[1:]==['--root-start'],'Root continuation authorization required'
 manifest=OUT/'queue_manifest.json';m=json.loads(manifest.read_text())
 assert subprocess.check_output(['git','show','HEAD:'+manifest.relative_to(ROOT).as_posix()],cwd=ROOT)==manifest.read_bytes()
 for rel,h in m['files'].items():assert sha(ROOT/rel)==h,rel
 lock=LOG/'continuation_serial_20261009.lock'
 with lock.open('x') as f:f.write(str(os.getpid())+'\n')
 save(OUT/'queue_birth_receipt.json',{'PID':os.getpid(),'manifest_sha256':sha(manifest),'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'ordinary_background_process_not_scheduled_task':True})
 start=time.monotonic();statuses=[]
 for phase in m['phases']:
  receipt=ROOT/phase['receipt']
  if receipt.exists():
   observed=json.loads(receipt.read_text())
   assert observed['status']==phase['expected_status'],'Existing receipt must be reviewed, never overwritten'
   statuses.append({'phase':phase['name'],'status':'ALREADY_COMPLETE_RECEIPT_PRESERVED','receipt_sha256':sha(receipt)});continue
  for rel in phase.get('forbidden_partial_paths',[]):assert not (ROOT/rel).exists(),'Preserve unreviewed partial native output; no automatic attempt'
  print('WAITING',phase['name'],'caller RAM>=3.5GiB and no competing project Python; original worker>=3GiB',flush=True)
  while True:
   if time.monotonic()-start>=6*3600:
    save(OUT/'queue_timeout_receipt.json',{'status':'NO_FURTHER_RESOURCE_ADMISSION_WITHIN_SIX_HOURS','completed_phases':statuses,'next_phase':phase['name'],'all_original_resource_floors_unchanged':True});return
   free=available()
   workers=other_workers() if free>=3.5*2**30 else []
   state={'PID':os.getpid(),'phase':phase['name'],'available_RAM_bytes':free,'caller_floor_bytes':3.5*2**30,'other_project_PIDs':workers,'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()}
   (LOG/'continuation_serial_20261009.latest.json').write_text(json.dumps(state,indent=2)+'\n')
   if free>=3.5*2**30 and not workers:break
   time.sleep(30)
  path=LOG/phase['log'];assert not path.exists();print('STARTING_ONCE',phase['name'],flush=True)
  with path.open('xb') as stream:
   child=subprocess.Popen([sys.executable,'-B','-u','-m',phase['module']]+phase.get('args',[]),cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
   code=child.wait()
  if code!=0 or not receipt.exists():
   save(OUT/'queue_worker_failure_receipt.json',{'status':'FAILED_PHASE_PRESERVED_NO_AUTOMATIC_RETRY','phase':phase['name'],'exit_code':code,'log_sha256':sha(path),'completed_phases':statuses,'original_resource_floors_unchanged':True});return
  data=json.loads(receipt.read_text());assert data['status']==phase['expected_status']
  statuses.append({'phase':phase['name'],'status':'COMPLETE','receipt_sha256':sha(receipt),'log_sha256':sha(path)})
  print('COMPLETE',phase['name'],flush=True)
 save(OUT/'queue_completion_receipt.json',{'status':'COMPLETE_FOUR_SERIAL_FEATURE_AND_SYNTHETIC_PHASES_NO_FITS','phases':statuses,'elapsed_seconds':time.monotonic()-start,'models_fit':0,'ordinary_background_process_not_scheduled_task':True})
if __name__=='__main__':run()
