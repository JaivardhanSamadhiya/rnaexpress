"""Additive final-cap check; preserves original v1 supervisor/design bytes."""
import ctypes,subprocess,sys,time
from .common import ROOT,OUT,sha,read,save
from .audit import bind_manifest
from src.generalization_prelib_native_reference_20261009.acquire import fresh as metadata_guard
WALL_SECONDS=30.;PEAK_BYTES=256*2**20
def completion_failure(elapsed,peak,exit_code,prior_failure,final_query_succeeded):
 if prior_failure:return prior_failure
 if not final_query_succeeded:return "Final lifetime peak-memory query unavailable; cannot certify cap"
 if peak<=0:return "No positive lifetime peak-memory observation"
 if peak>PEAK_BYTES:return "Owned stdlib worker256MiB lifetime working-set cap"
 if elapsed>WALL_SECONDS:return "Owned stdlib worker30s wall cap including final completion"
 if exit_code!=0:return "Owned metadata worker failed"
 return None
def bind_v2():
 p=OUT/"design_manifest_v2.json";m=read(p)
 assert m["status"]=="FROZEN_ADDITIVE_FINAL_RESOURCE_CAP_CHECK"
 assert subprocess.check_output(["git","show","HEAD:"+p.relative_to(ROOT).as_posix()],cwd=ROOT)==p.read_bytes()
 for rel,h in m["files"].items():assert sha(ROOT/rel)==h,rel
 original,_=bind_manifest()
 assert m["original_design_manifest_sha256"]==sha(original)
 return p,original
def run(stage):
 assert stage in ("audit","replay");available=metadata_guard();path,original=bind_v2()
 class Counters(ctypes.Structure):
  _fields_=[("cb",ctypes.c_ulong),("faults",ctypes.c_ulong)]+[(x,ctypes.c_size_t) for x in ("peak","current","peak_paged","paged","peak_nonpaged","nonpaged","pagefile","peak_pagefile")]
 api=ctypes.WinDLL("psapi");api.GetProcessMemoryInfo.argtypes=[ctypes.c_void_p,ctypes.POINTER(Counters),ctypes.c_ulong]
 log=OUT/(stage+"_worker_v2.log");peak=0;failure=None;start=time.monotonic();final_query=False
 with log.open("xb") as f:
  child=subprocess.Popen([sys.executable,"-B","-u","-m","src."+OUT.name+"."+stage],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
  while child.poll() is None:
   c=Counters();c.cb=ctypes.sizeof(c)
   if not api.GetProcessMemoryInfo(int(child._handle),ctypes.byref(c),ctypes.sizeof(c)):failure="Owned memory measurement failed closed"
   else:peak=max(peak,c.peak,c.current)
   if peak>PEAK_BYTES:failure="Owned stdlib worker256MiB working-set cap"
   if time.monotonic()-start>WALL_SECONDS:failure="Owned stdlib worker30s wall cap"
   if failure:child.terminate();child.wait();break
   time.sleep(.05)
  # Keep the child's process handle alive. Fail closed if Windows cannot return lifetime peak after exit.
  c=Counters();c.cb=ctypes.sizeof(c)
  final_query=bool(api.GetProcessMemoryInfo(int(child._handle),ctypes.byref(c),ctypes.sizeof(c)))
  if final_query:peak=max(peak,c.peak,c.current)
  elapsed=time.monotonic()-start
  failure=completion_failure(elapsed,peak,child.returncode,failure,final_query)
 receipt={"status":"PASS_OWNED_STDLIB_FINAL_CAPS" if failure is None else "FAILED_WORKER_OR_BOUND",
  "stage":stage,"exit_code":child.returncode,"failure":failure,"peak_working_set_bytes":peak,
  "final_lifetime_peak_query_succeeded":final_query,"elapsed_seconds":elapsed,"available_RAM_before_bytes":available,
  "v2_design_manifest_sha256":sha(path),"original_design_manifest_sha256":sha(original),"log_sha256":sha(log),
  "final_elapsed_check_after_completion":True,"all_existing3GiB_guards_unchanged":True,
  "only_owned_child_can_be_terminated":True,"v1_supervisor_and_manifest_preserved":True}
 save(OUT/(stage+"_supervisor_receipt_v2.json"),receipt)
 print(stage,receipt["status"],"peakMiB",peak/2**20,flush=True)
 if failure:raise RuntimeError(failure+"; evidence preserved")
if __name__=="__main__":run(sys.argv[1])
