"""Package this explicitly authorized study; preserve and verify every member."""
from .common import *
import zipfile,sys,platform,importlib.metadata,subprocess

def run():
    assert_frozen();assert readj(OUT/'verification_receipt.json')['status']=='PASS'
    required=['GSE330741_admission_protocol.md','GSE330741_external_test_protocol.md','GSE330741_PREFIT_FREEZE.md','GSE330741_zero_shot_results.md','GSE330741_leave_parent_out_results.md','GSE330741_candidate_selection_results.md','GSE334718_admission.md','generalization_final_synthesis.md']
    assert all((REPORT/name).is_file() for name in required)
    for name in ['GSE330741_zero_shot_predictions.csv','GSE330741_leave_parent_out_predictions.csv','GSE330741_candidate_rankings.csv','generalization_evidence_ledger.csv']:assert (ART/name).is_file()
    jsave(OUT/'runtime_receipt.json',{'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'packages':{p:importlib.metadata.version(p) for p in ('numpy','pandas','scipy','scikit-learn','openpyxl')},'full_runtime_bundled':False,'source_result_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'figure_visual_review':'six-panel contact sheet inspected; no outcome/model changes'})
    paths=[]
    for directory in [ROOT/'src/generalization_20260926',REPORT,OUT,ART]:
        paths.extend(p for p in directory.rglob('*') if p.is_file() and p.suffix!='.zip' and p.name!='delivery_receipt.json' and '__pycache__' not in p.parts)
    manifest={p.relative_to(ROOT).as_posix():{'sha256':sha256(p),'bytes':p.stat().st_size} for p in sorted(paths)}
    archive=ART/'generalization_evidence_20260926.zip';assert not archive.exists()
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for path in manifest:z.write(ROOT/path,path)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and set(z.namelist())==set(manifest)
        for path,entry in manifest.items():assert hashlib.sha256(z.read(path)).hexdigest()==entry['sha256']
    jsave(ART/'delivery_receipt.json',{'status':'PASS','archive':archive.relative_to(ROOT).as_posix(),'bytes':archive.stat().st_size,'sha256':sha256(archive),'files':len(manifest),'manifest':manifest,'crc_and_every_member_sha256_verified':True,'required_reports':8,'prefit_commit':'0b100d32a106d038deedcd98c1cdba2d53c0663e','access_marker_commit':'5ae6d4a','test_a_preservation_commit':'1ff9bc2','protected_unrelated_outcomes_included':False,'authorized_GSE330741_derived_outcomes_included':True,'original_raw_files_bundled':False,'self_contained_runtime':False})
    print('Verified archive:',archive,'members:',len(manifest),'bytes:',archive.stat().st_size,'SHA256:',sha256(archive))

if __name__=='__main__':run()
