
"""Single isolated metadata worker with bounded memory and elapsed time."""
from .loader import ROOT,OUT,NS,read,sha
import subprocess,sys,time,ctypes,json
def run():
    class Memory(ctypes.Structure):
        _fields_=[("length",ctypes.c_ulong),("load",ctypes.c_ulong)]+[(name,ctypes.c_ulonglong) for name in ("total","available","page_total","page_available","virtual_total","virtual_available","extended")]
    memory=Memory();memory.length=ctypes.sizeof(memory);assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory))
    assert memory.available>=1.3*2**30,"New metadata-only caller floor1.3GiB; existing model/feature floors untouched"
    manifest=read(OUT/"metadata_parse_manifest.json")
    assert manifest["worker_RAM_cap_MiB"]==768 and manifest["worker_wall_time_seconds"]==180
    log=OUT/"metadata_worker_01.log";assert not log.exists()
    class Counters(ctypes.Structure):
        _fields_=[("cb",ctypes.c_ulong),("page_faults",ctypes.c_ulong)]+[(name,ctypes.c_size_t) for name in ("peak_working_set","working_set","peak_paged","paged","peak_nonpaged","nonpaged","pagefile","peak_pagefile")]
    psapi=ctypes.WinDLL("psapi");psapi.GetProcessMemoryInfo.argtypes=[ctypes.c_void_p,ctypes.POINTER(Counters),ctypes.c_ulong]
    start=time.monotonic();peak=0;failure=None
    with log.open("xb") as stream:
        child=subprocess.Popen([sys.executable,"-B","-u","-m","src."+NS+".produce","--root-start"],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
        while child.poll() is None:
            counters=Counters();counters.cb=ctypes.sizeof(counters)
            if psapi.GetProcessMemoryInfo(int(child._handle),ctypes.byref(counters),ctypes.sizeof(counters)):
                peak=max(peak,counters.working_set,counters.peak_working_set)
            if peak>768*2**20:failure="Metadata worker memory cap exceeded"
            elif time.monotonic()-start>180:failure="Metadata worker time cap exceeded"
            if failure:child.terminate();child.wait();break
            time.sleep(.1)
    status="PASS" if child.returncode==0 and failure is None else "FAILED_METADATA_WORKER"
    receipt={"status":status,"worker_pid":child.pid,"exit_code":child.returncode,"failure":failure,
        "observed_peak_working_set_bytes":peak,"elapsed_seconds":time.monotonic()-start,
        "metadata_manifest_sha256":sha(OUT/"metadata_parse_manifest.json"),"worker_log_sha256":sha(log),
        "supervisor_source_sha256":sha(__file__),"existing_model_or_feature_resource_floor_changed":False,
        "only_this_known_child_can_be_terminated":True,"models_fit":0}
    with (OUT/"supervisor_receipt.json").open("xb") as f:f.write((json.dumps(receipt,sort_keys=True,indent=2)+"\n").encode())
    print(status,"metadata worker; peak MiB",peak/2**20,flush=True)
    if status!="PASS":raise RuntimeError(failure or "Metadata parsing failed; preserve log and partial outputs")
if __name__=="__main__":run()
