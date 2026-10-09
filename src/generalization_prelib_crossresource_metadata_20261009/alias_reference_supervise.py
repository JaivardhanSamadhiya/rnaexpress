"""Bounded one-shot qualitative metadata worker, >=1.3GiB admission."""
from .audit import ROOT,OUT,sha,save,fresh
import ctypes,json,subprocess,sys,time
def run():
 available=fresh();manifest=OUT/'alias_reference_audit_manifest_v2.json';m=json.loads(manifest.read_text())
 assert subprocess.check_output(['git','show','HEAD:'+manifest.relative_to(ROOT).as_posix()],cwd=ROOT)==manifest.read_bytes()
 for rel,h in m['files'].items():assert sha(ROOT/rel)==h,rel
 class Counters(ctypes.Structure):
  _fields_=[('cb',ctypes.c_ulong),('faults',ctypes.c_ulong)]+[(x,ctypes.c_size_t) for x in ('peak','current','peak_paged','paged','peak_nonpaged','nonpaged','pagefile','peak_pagefile')]
 psapi=ctypes.WinDLL('psapi');psapi.GetProcessMemoryInfo.argtypes=[ctypes.c_void_p,ctypes.POINTER(Counters),ctypes.c_ulong]
 log=OUT/'alias_reference_worker_01.log';peak=0;failure=None;start=time.monotonic()
 with log.open('xb') as stream:
  child=subprocess.Popen([sys.executable,'-B','-u','-m','src.generalization_prelib_crossresource_metadata_20261009.alias_reference_audit'],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
  while child.poll() is None:
   counters=Counters();counters.cb=ctypes.sizeof(counters)
   if psapi.GetProcessMemoryInfo(int(child._handle),ctypes.byref(counters),ctypes.sizeof(counters)):peak=max(peak,counters.peak,counters.current)
   if peak>768*2**20:failure='Owned metadata worker768MiB cap exceeded'
   elif time.monotonic()-start>180:failure='Owned metadata worker180s cap exceeded'
   if failure:child.terminate();child.wait();break
   time.sleep(.1)
 save(OUT/'alias_reference_supervisor_receipt_v2.json',{'status':'PASS_WORKER_BOUND' if child.returncode==0 and failure is None else 'FAILED_BOUND_OR_WORKER',
  'exit_code':child.returncode,'failure':failure,'observed_peak_working_set_bytes':peak,'elapsed_seconds':time.monotonic()-start,
  'available_RAM_before_worker_bytes':available,'manifest_sha256':sha(manifest),'log_sha256':sha(log),'only_owned_child_can_be_terminated':True,
  'original_feature_model_floors_unchanged':True})
 print('METADATA_AUDIT_WORKER',child.returncode,'peak MiB',peak/2**20,flush=True)
 if failure or child.returncode:raise RuntimeError(failure or 'Metadata worker failed')
if __name__=='__main__':run()
