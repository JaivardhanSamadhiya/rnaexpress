"""Profile selected invented-case tests only; does not execute guarded workers."""
import ctypes,datetime,hashlib,json,pathlib,subprocess,sys,time
from ctypes import wintypes
ROOT=pathlib.Path('D:/rnaexpress');OUT=ROOT/'results/generalization_resource_synthetic_profile_20261009'
class Counters(ctypes.Structure):
    _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(n,ctypes.c_size_t) for n in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage','PrivateUsage')]
class Memory(ctypes.Structure):
    _fields_=[('length',wintypes.DWORD),('load',wintypes.DWORD)]+[(n,ctypes.c_ulonglong) for n in ('total','available','page_total','page_available','virtual_total','virtual_available','extended')]
psapi=ctypes.WinDLL('psapi',use_last_error=True);psapi.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD];psapi.GetProcessMemoryInfo.restype=wintypes.BOOL
kernel=ctypes.WinDLL('kernel32',use_last_error=True)
def memory():
    m=Memory();m.length=ctypes.sizeof(m);assert kernel.GlobalMemoryStatusEx(ctypes.byref(m));return {'physical_total':m.total,'physical_available':m.available,'commit_headroom':m.page_available}
def main():
    assert sys.version_info[:2]==(3,12)
    OUT.mkdir(parents=True,exist_ok=True);before=memory()
    paths=['src/generalization_pum2_fixed_math_20261008/model.py','src/generalization_pum2_fixed_math_20261008/tests.py','src/generalization_pum2_independent_replay_20261009/numeric.py','src/generalization_pum2_independent_replay_20261009/tests.py']
    t=time.monotonic();cmd=[sys.executable,'-B','-u','-m','unittest','src.generalization_pum2_fixed_math_20261008.tests','src.generalization_pum2_independent_replay_20261009.tests']
    with (OUT/'selected_invented_tests.log').open('xb') as f:
        p=subprocess.Popen(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
        code=p.wait(timeout=120)
    counters=Counters();counters.cb=ctypes.sizeof(counters)
    ok=bool(psapi.GetProcessMemoryInfo(wintypes.HANDLE(int(p._handle)),ctypes.byref(counters),counters.cb))
    log=(OUT/'selected_invented_tests.log').read_text()
    assert code==0 and 'Ran 46 tests' in log and '\nOK\n' in log
    out={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_46_SELECTED_INVENTED_CASE_TESTS_WITH_MEMORY_OBSERVATION','tests':46,'elapsed_seconds':time.monotonic()-t,'process_memory_query_succeeded':ok,'peak_working_set_bytes':counters.PeakWorkingSetSize if ok else None,'peak_private_commit_bytes':counters.PeakPagefileUsage if ok else None,'memory_before':before,'memory_after':memory(),'tested_files_SHA256':{s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in paths},'no_biological_sequences_or_outcomes_read':True,'fixed_358_byte_public_parameter_files_used':True,'scientific_production_workers_executed':False,'existing_RAM_safeguards_changed':False,'limitation':'Invented tests exercise 140nt states but not real cohort loading, production serialization or model training; this is not a production peak-memory bound.'}
    (OUT/'synthetic_profile_receipt.json').open('x',encoding='utf-8',newline='\n').write(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
