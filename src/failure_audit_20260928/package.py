from .run import *
import zipfile,sys

def run():
    frozen();assert readj(OUT/'verification_receipt.json')['status']=='PASS';assert readj(OUT/'ranking_support_receipt.json')['status']=='PASS'
    previous=readj(ART/'delivery_receipt.json')
    for p,e in previous['manifest'].items():assert sha256(ROOT/p)==e['sha256']
    for p,h in readj(OLD/'initial_state.json')['unchanged_user_files'].items():assert sha256(ROOT/p)==h
    paths=sorted(p for root in (SRC,REP,OUT) for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    manifest={p.relative_to(ROOT).as_posix():{'bytes':p.stat().st_size,'sha256':sha256(p)} for p in paths}
    target=ROOT/'artifacts/failure_audit_20260928';target.mkdir(parents=True,exist_ok=True);dest=target/'failure_diagnostic_evidence.zip';assert not dest.exists()
    with zipfile.ZipFile(dest,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in paths:z.write(p,p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        for p,e in manifest.items():assert hashlib.sha256(z.read(p)).hexdigest()==e['sha256']
    receipt={'status':'PASS','archive':dest.relative_to(ROOT).as_posix(),'sha256':sha256(dest),'bytes':dest.stat().st_size,'manifest':manifest,'files':len(manifest),'result_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'python_executable':sys.executable,'python_version':sys.version,'previous_gate':'NO-GO','new_model_fits':0,'new_datasets':0,'self_contained_runtime':False}
    p=target/'delivery_receipt.json';assert not p.exists();p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print('Archive PASS',len(manifest),'files',receipt['bytes'],'bytes',receipt['sha256'])

if __name__=='__main__':run()
