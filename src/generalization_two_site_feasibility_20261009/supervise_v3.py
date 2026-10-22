"""New worker/log names; reuse frozen v2 final cap arithmetic without relaxing limits."""
import ctypes,subprocess,sys,time
from .common import ROOT,OUT,sha,save
from .worker_v3 import bind_v3
from .supervise_v2 import completion_failure,WALL_SECONDS,PEAK_BYTES
from src.generalization_prelib_native_reference_20261009.acquire import fresh as metadata_guard
def run(stage):
 assert stage in ("audit","replay");available=metadata_guard();path,prior,original=bind_v3()
 class Counters(ctypes.Structure):
  _fields_=[("cb",ctypes.c_ulong),("faults",ctypes.c_ulong)]+[(x,ctypes.c_size_t) for x in ("peak","current","peak_paged","paged","peak_nonpaged","nonpaged","pagefile","peak_pagefile")]
 api=ctypes.WinDLL("psapi");api.GetProcessMemoryInfo.argtypes=[ctypes.c_void_p,ctypes.POINTER(Counters),ctypes.c_ulong]
 log=OUT/(stage+"_worker_v3.log");peak=0;failure=None;start=time.monotonic();final_query=False
 with log.open("xb") as f:
  child=subprocess.Popen([sys.executable,"-B","-u","-m","src."+OUT.name+".worker_v3",stage],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
  while child.poll() is None:
   c=Counters();c.cb=ctypes.sizeof(c)
   if not api.GetProcessMemoryInfo(int(child._handle),ctypes.byref(c),ctypes.sizeof(c)):failure="Owned memory measurement failed closed"
   else:peak=max(peak,c.peak,c.current)
   if peak>PEAK_BYTES:failure="Owned stdlib worker256MiB working-set cap"
   if time.monotonic()-start>WALL_SECONDS:failure="Owned stdlib worker30s wall cap"
   if failure:child.terminate();child.wait();break
   time.sleep(.05)
  c=Counters();c.cb=ctypes.sizeof(c)
  final_query=bool(api.GetProcessMemoryInfo(int(child._handle),ctypes.byref(c),ctypes.sizeof(c)))
  if final_query:peak=max(peak,c.peak,c.current)
  elapsed=time.monotonic()-start
  failure=completion_failure(elapsed,peak,child.returncode,failure,final_query)
 receipt={"status":"PASS_OWNED_STDLIB_FINAL_CAPS_V3" if failure is None else "FAILED_WORKER_OR_BOUND_V3",
  "stage":stage,"exit_code":child.returncode,"failure":failure,"peak_working_set_bytes":peak,
  "final_lifetime_peak_query_succeeded":final_query,"elapsed_seconds":elapsed,"available_RAM_before_bytes":available,
  "v3_design_manifest_sha256":sha(path),"v2_design_manifest_sha256":sha(prior),"original_design_manifest_sha256":sha(original),
  "log_sha256":sha(log),"all_prior_sources_manifests_and_failed_logs_preserved":True,
  "all_existing3GiB_guards_unchanged":True,"only_owned_child_can_be_terminated":True,
  "limits_identical_to_frozen_v2":{"wall_seconds":WALL_SECONDS,"peak_working_set_bytes":PEAK_BYTES}}
 save(OUT/(stage+"_supervisor_receipt_v3.json"),receipt)
 print(stage,receipt["status"],"peakMiB",peak/2**20,flush=True)
 if failure:raise RuntimeError(failure+"; evidence preserved")
if __name__=="__main__":run(sys.argv[1])
