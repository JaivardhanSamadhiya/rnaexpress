"""Bounded isolated raw-count reader; original feature/model floors unchanged."""
from .replay import ROOT,OUT,NS,sha,save
import json
def certify():
 p=OUT/"replay_manifest.json";m=json.loads(p.read_text())
 assert subprocess.check_output(["git","show","HEAD:"+p.relative_to(ROOT).as_posix()],cwd=ROOT)==p.read_bytes()
 for name,digest in m["files"].items():assert sha(ROOT/name)==digest,name
 return m
import ctypes,subprocess,sys,time

def run():
 class Memory(ctypes.Structure):
  _fields_=[("length",ctypes.c_ulong),("load",ctypes.c_ulong)]+[(n,ctypes.c_ulonglong) for n in ("total","available","page_total","page_available","virtual_total","virtual_available","extended")]
 memory=Memory();memory.length=ctypes.sizeof(memory)
 assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory))
 assert memory.available>=1.3*2**30,"New bounded source reader floor1.3GiB; original feature/model3GiB floors unchanged"
 m=certify();assert m["worker_RAM_cap_MiB"]==768 and m["worker_wall_time_seconds"]==180
 class Counters(ctypes.Structure):
  _fields_=[("cb",ctypes.c_ulong),("faults",ctypes.c_ulong)]+[(n,ctypes.c_size_t) for n in ("peak_working_set","working_set","peak_paged","paged","peak_nonpaged","nonpaged","pagefile","peak_pagefile")]
 psapi=ctypes.WinDLL("psapi");psapi.GetProcessMemoryInfo.argtypes=[ctypes.c_void_p,ctypes.POINTER(Counters),ctypes.c_ulong]
 log=OUT/"replay_worker_01.log";assert not log.exists();start=time.monotonic();peak=0;failure=None
 with log.open("xb") as stream:
  child=subprocess.Popen([sys.executable,"-B","-u","-m","src."+NS+".replay"],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
  while child.poll() is None:
   counters=Counters();counters.cb=ctypes.sizeof(counters)
   if psapi.GetProcessMemoryInfo(int(child._handle),ctypes.byref(counters),ctypes.sizeof(counters)):peak=max(peak,counters.working_set,counters.peak_working_set)
   if peak>768*2**20:failure="Owned source reader RAM cap exceeded"
   elif time.monotonic()-start>180:failure="Owned source reader time cap exceeded"
   if failure:child.terminate();child.wait();break
   time.sleep(.1)
 status="PASS" if child.returncode==0 and failure is None else "FAILED_SOURCE_READER"
 save(OUT/"replay_supervisor_receipt.json",{"status":status,"exit_code":child.returncode,"failure":failure,"observed_peak_working_set_bytes":peak,
   "elapsed_seconds":time.monotonic()-start,"manifest_sha256":sha(OUT/"replay_manifest.json"),"source_log_sha256":sha(log),
   "available_RAM_before_worker_bytes":memory.available,"only_owned_child_can_be_terminated":True,"original_feature_model_floors_unchanged":True})
 print(status,"bounded source reader; peak MiB",peak/2**20,flush=True)
 if status!="PASS":raise RuntimeError(failure or "Source reader failed; preserve failure and partial artifacts")
if __name__=="__main__":run()
