"""One owned, kernel-limited PUM phase; no queue modification or retries."""
import argparse,ctypes,datetime,json,os,subprocess,sys,time
from . import worker,winjob
ROOT=worker.ROOT;OUT=worker.OUT

def competing_workers():
 command="Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^python' -and $_.CommandLine -match 'generalization_' } | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress"
 p=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',command],capture_output=True,timeout=20)
 assert p.returncode==0,'Could not certify no competing scientific worker'
 rows=json.loads(p.stdout.decode('utf-8-sig')) if p.stdout.strip() else []
 if isinstance(rows,dict):rows=[rows]
 queue=json.loads((ROOT/'results/generalization_continuation_queue_20261009/queue_birth_receipt.json').read_text())['PID']
 bad=[]
 for row in rows:
  pid=row['ProcessId'];cmd=row['CommandLine'] or ''
  if pid==os.getpid():continue
  if pid==queue and 'src.generalization_continuation_queue_20261009.watch --root-start' in cmd:continue
  if 'src.generalization_github_publication_20261009.publish --execute-authorized-push' in cmd:continue
  bad.append(pid)
 assert not bad,('Competing scientific worker PIDs',bad)
 return [r['ProcessId'] for r in rows]

def run(phase):
 assert phase in worker.MODULES
 manifest,m=worker.admitted();manifest_hash=worker.sha(manifest)
 assert not (OUT/(phase+'_controller_receipt.json')).exists(),'Preserve prior controller result, no automaticretry'
 assert not (OUT/(phase+'_worker.log')).exists(),'Preserve prior worker log, no automaticretry'
 assert not worker.RECEIPTS[phase].exists(),'Original completion exists; review without duplicate execution'
 if phase=='replay':
  prior=json.loads((OUT/'production_controller_receipt.json').read_text())
  assert prior['status']=='PASS_OWNED_PUM_PHASE_WITH_KERNEL_LIMITS'
  assert worker.sha(worker.RECEIPTS['production'])==prior['original_scientific_receipt_sha256']
  assert subprocess.check_output(['git','show','HEAD:'+worker.RECEIPTS['production'].relative_to(ROOT).as_posix()],cwd=ROOT)==worker.RECEIPTS['production'].read_bytes(),'Root commit production receipt before independent replay'
 before=winjob.memory();worker.resource_guard();observed_workers=competing_workers()
 original={rel:worker.sha(ROOT/rel) for rel in m['scientific_files']}
 started=time.monotonic();last=started;maximum_gap=0.;peak_private=0;peak_working=0;minimum_physical=before['physical_available'];minimum_commit=before['commit_headroom']
 job=None;child=None;failure=None;code=None;limits=None;accounting=None;after=None;final_process=None
 try:
  job=winjob.Job();limits=job.limits()
  assert limits['process_memory_limit']==768*2**20 and limits['job_memory_limit']==896*2**20 and limits['active_process_limit']==2
  command=[sys.executable,'-B','-u','-m','src.generalization_pum_resource_calibration_20261009.worker',phase,str(os.getpid())]
  child=job.spawn(command,str(ROOT))
  worker.save(OUT/(phase+'_birth_receipt.json'),{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'supervisor_PID':os.getpid(),'child_PID':child.pid,'manifest_sha256':manifest_hash,'kernel_limits':limits,'suspended_attached_and_verified_before_resume':True})
  worker.resource_guard();child.resume()
  while True:
   now=time.monotonic();maximum_gap=max(maximum_gap,now-last);last=now
   state=winjob.memory();process=winjob.process_memory(child.process_handle);accounting=job.accounting()
   minimum_physical=min(minimum_physical,state['physical_available']);minimum_commit=min(minimum_commit,state['commit_headroom'])
   peak_private=max(peak_private,process['peak_private_commit'],process['private_commit']);peak_working=max(peak_working,process['peak_working_set'],process['working_set'])
   if now-started>1800:failure='Original approved30minute phase deadline exceeded'
   elif state['physical_available']<256*2**20:failure='Physical RAM below approved256MiB stop floor'
   elif state['commit_headroom']<2**30:failure='System commit headroom below approved1GiB reserve'
   elif state['disk_available']<256*2**20:failure='Workspace disk below256MiB stop floor'
   elif peak_private>768*2**20 or accounting['peak_job_memory_used']>896*2**20:failure='Owned kernel memory cap exceeded'
   elif accounting['active_processes']>2:failure='Owned active-process cap exceeded'
   code=child.exit_code()
   if failure:
    job.terminate();
    for _ in range(100):
     code=child.exit_code()
     if code is not None:break
     time.sleep(.01)
    break
   if code is not None:break
   time.sleep(.1)
  # Final resource/deadline check after exit and provenance hashing; a loop snapshot alone cannot certify PASS.
  final_process=winjob.process_memory(child.process_handle);accounting=job.accounting()
  assert all(worker.sha(ROOT/rel)==h for rel,h in original.items()),'Scientific source or frozen input changed'
  after=winjob.memory();elapsed=time.monotonic()-started
  peak_private=max(peak_private,final_process['peak_private_commit']);peak_working=max(peak_working,final_process['peak_working_set'])
  if elapsed>1800:failure=failure or 'Final deadline exceeded'
  if after['physical_available']<256*2**20 or after['commit_headroom']<2**30 or after['disk_available']<256*2**20:failure=failure or 'Final system resource reserve violated'
  if peak_private>768*2**20 or accounting['peak_job_memory_used']>896*2**20:failure=failure or 'Final kernel memory cap exceeded'
 except BaseException as e:
  failure=failure or ('Failed closed: '+type(e).__name__+': '+str(e))
  if job:job.terminate()
 finally:
  try:
   if child:child.close()
  finally:
   if job:job.close()
 path=worker.RECEIPTS[phase];receipt_ok=False
 if code==0 and path.exists() and failure is None:
  data=json.loads(path.read_text());expected={'production':'COMPLETE_FIXED_PUM2_POINT_FRAGMENT_FEATURES_ONLY_NOT_LOCALIZATION_OR_TRAINING_ADMISSION','replay':'PASS_ALL_PRODUCTION_ALLELES_DIRECT_CONTACT_AND_ORDINARY_PARTITION_REPLAY'}[phase]
  receipt_ok=data['status']==expected and data['authorized_resource_calibration_manifest_sha256']==manifest_hash and data['resource_admission_original_3GiB_overridden'] is True
 if not receipt_ok:failure=failure or 'Original scientific completion receipt missing or invalid'
 # Compute every receipt/source hash and controller observation before the LAST admission/deadline decision.
 original_intact=all(worker.sha(ROOT/rel)==h for rel,h in original.items())
 receipt_digest=worker.sha(path) if path.exists() else None
 controller_memory=winjob.process_memory(-1)
 try:
  after=winjob.memory()
  minimum_physical=min(minimum_physical,after['physical_available']);minimum_commit=min(minimum_commit,after['commit_headroom'])
  if time.monotonic()-started>1800:failure=failure or 'Final complete-provenance deadline exceeded'
  if after['physical_available']<256*2**20 or after['commit_headroom']<2**30 or after['disk_available']<256*2**20:failure=failure or 'Final complete-provenance reserve violated'
 except Exception as e:failure=failure or ('Final resource measurement failed: '+type(e).__name__)
 if not original_intact:failure=failure or 'Final scientific source/input bytes changed'
 result={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_OWNED_PUM_PHASE_WITH_KERNEL_LIMITS' if receipt_ok and failure is None else 'FAILED_PHASE_PRESERVED_NO_AUTOMATIC_RETRY','phase':phase,'failure':failure,'exit_code':code,'manifest_sha256':manifest_hash,'kernel_limits':limits,'job_accounting':accounting,'peak_worker_working_set_bytes':peak_working,'peak_worker_private_commit_bytes':peak_private,'minimum_available_physical_bytes':minimum_physical,'minimum_system_commit_headroom_bytes':minimum_commit,'maximum_monitor_gap_seconds':maximum_gap,'monitor_target_interval_seconds':.1,'elapsed_seconds':time.monotonic()-started,'memory_before':before,'memory_after':after,'controller_process_memory':controller_memory,'observed_other_project_PIDs':observed_workers,'original_scientific_receipt_sha256':receipt_digest,'original_scientific_bytes_unchanged':original_intact,'other_worker_and_queue_guards_changed':False,'only_owned_job_terminated_on_failure_or_close':True,'models_fit':0,'outcomes_read':False}
 worker.save(OUT/(phase+'_controller_receipt.json'),result);print(json.dumps(result,indent=2),flush=True)
 assert result['status']=='PASS_OWNED_PUM_PHASE_WITH_KERNEL_LIMITS',failure
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=sorted(worker.MODULES),required=True);a=p.parse_args();run(a.phase)
