"""Archive additive evidence and verify every member; original artifacts stay put."""
from .common import *
from .verify import preservation
import sys, zipfile, importlib.metadata

def run():
    preservation()
    verification=readj(OUT/'verification_receipt.json')
    assert verification['status']=='PASS'
    assert (REP/'final_status.md').exists()
    assert readj(OUT/'quality_receipt.json')['status']=='PASS'
    jsave(OUT/'runtime_receipt.json',{'python':sys.version,'executable':sys.executable,
        'packages':{k:importlib.metadata.version(k) for k in ('numpy','pandas','scipy')},
        'prefit_commit':'53553f2','result_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'no_spending':True,'no_new_biological_outcomes':True,'scheduled_tasks':False,'independent_confirmation':False})
    paths=sorted(p for root in (SRC,OUT,REP,ART) for p in root.rglob('*')
        if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.zip' and p.name!='delivery_receipt.json')
    manifest={p.relative_to(ROOT).as_posix():{'bytes':p.stat().st_size,'sha256':sha256(p)} for p in paths}
    dest=ART/'parallel_generalization_evidence.zip'
    assert not dest.exists(),'Preserve existing archive'
    with zipfile.ZipFile(dest,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for path in paths:archive.write(path,path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(dest) as archive:
        assert archive.testzip() is None and set(archive.namelist())==set(manifest)
        for path,entry in manifest.items():assert hashlib.sha256(archive.read(path)).hexdigest()==entry['sha256'],path
    jsave(ART/'delivery_receipt.json',{'status':'PASS','archive':dest.relative_to(ROOT).as_posix(),
        'bytes':dest.stat().st_size,'sha256':sha256(dest),'files':len(manifest),'manifest':manifest,
        'gate':readj(OUT/'gate_verdict.json')['status'],'crc_and_member_hashes_verified':True,
        'self_contained_runtime':False,'original_canonical_data':'Prior verified evidence archives remain prerequisite inputs'})
    print('Verified archive:',len(paths),'members;',dest.stat().st_size,'bytes',flush=True)

if __name__=='__main__':run()
