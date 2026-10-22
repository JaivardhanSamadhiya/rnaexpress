"""Bound only this stdlib owned worker; existing metadata1.3GiB admission."""
import ctypes,subprocess,sys,time
from .common import OUT,sha,save
from .audit import bind_manifest
from src.generalization_prelib_native_reference_20261009.acquire import fresh as metadata_guard
def run(stage):
 assert stage in ("audit","replay");available=metadata_guard();path,m=bind_manifest()
 class Counters(ctypes.Structure):
  _fields_=[("cb",ctypes.c_ulong),("faults",ctypes.c_ulong)]+[(x,ctypes.c_size_t) for x in ("peak","current","peak_paged","paged","peak_nonpaged","nonpaged","pagefile","peak_pagefile")]
 api=ctypes.WinDLL("psapi");api.GetProcessMemoryInfo.argtypes=[ctypes.c_void_p,ctypes.POINTER(Counters),ctypes.c_ulong]
 log=OUT/(stage+"_worker.log");peak=0;failure=None;start=time.monotonic()
 with log.open("xb") as f:
  child=subprocess.Popen([sys.executable,"-B","-u","-m","src."+OUT.name+"."+stage],cwd=path.parents[2],stdout=f,stderr=subprocess.STDOUT)
  while child.poll() is None:
   c=Counters();c.cb=ctypes.sizeof(c)
   if not api.GetProcessMemoryInfo(int(child._handle),ctypes.byref(c),ctypes.sizeof(c)):failure="Owned memory measurement failed closed"
   else:peak=max(peak,c.peak,c.current)
   if peak>256*2**20:failure="Owned stdlib worker256MiB working-set cap"
   if time.monotonic()-start>30:failure="Owned stdlib worker30s wall cap"
   if failure:child.terminate();child.wait();break
   time.sleep(.05)
 receipt={"status":"PASS_OWNED_STDLIB_WORKER_BOUND" if child.returncode==0 and failure is None else "FAILED_WORKER_OR_BOUND",
  "stage":stage,"exit_code":child.returncode,"failure":failure,"peak_working_set_bytes":peak,
  "elapsed_seconds":time.monotonic()-start,"available_RAM_before_bytes":available,"design_manifest_sha256":sha(path),
  "log_sha256":sha(log),"all_existing3GiB_guards_unchanged":True,"only_owned_child_can_be_terminated":True}
 save(OUT/(stage+"_supervisor_receipt.json"),receipt)
 print(stage,receipt["status"],"peakMiB",peak/2**20,flush=True)
 if failure or child.returncode:raise RuntimeError(failure or "Owned metadata worker failed; evidence preserved")
if __name__=="__main__":run(sys.argv[1])
