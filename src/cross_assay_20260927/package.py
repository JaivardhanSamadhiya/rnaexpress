from .common import *
import zipfile,subprocess,sys,importlib.metadata

def run():
    frozen();assert readj(OUT/'verification_receipt.json')['status']=='PASS'
    reports=['multi_assay_admission.md','canonical_intervention_dataset.md','cross_assay_protocol.md','leave_one_assay_out_results.md','universal_feature_analysis.md','model_selection_verdict.md','generalizable_predictor_status.md']
    artifacts=['canonical_interventions.csv','leave_one_assay_out_predictions.csv','candidate_rankings.csv','feature_transfer_matrix.csv','model_comparison.csv','evidence_ledger.csv']
    assert all((REPORT/p).exists() for p in reports) and all((ART/p).exists() for p in artifacts)
    jsave(OUT/'runtime_receipt.json',{'python':sys.version,'executable':sys.executable,'packages':{k:importlib.metadata.version(k) for k in ('numpy','pandas','scipy','scikit-learn')},'result_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'new_data_downloaded':False,'paid_compute':False,'scheduled_tasks':False})
    paths=[p for d in (SRC,REPORT,OUT,ART) for p in d.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.zip' and p.name!='delivery_receipt.json']
    manifest={p.relative_to(ROOT).as_posix():{'bytes':p.stat().st_size,'sha256':sha256(p)} for p in sorted(paths)}
    dest=ART/'cross_assay_evidence_20260927.zip';assert not dest.exists()
    with zipfile.ZipFile(dest,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in manifest:z.write(ROOT/p,p)
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None and set(z.namelist())==set(manifest)
        for p,e in manifest.items():assert hashlib.sha256(z.read(p)).hexdigest()==e['sha256']
    jsave(ART/'delivery_receipt.json',{'status':'PASS','archive':dest.relative_to(ROOT).as_posix(),'bytes':dest.stat().st_size,'sha256':sha256(dest),'files':len(manifest),'manifest':manifest,'crc_and_all_member_hashes_verified':True,'gate':readj(OUT/'gate_verdict.json')['status'],'prefit_commit':'d6a0623','derived_exposed_outcomes_included':True,'unrelated_protected_data_included':False,'self_contained_runtime':False,'required_reports':7,'required_artifacts':6})
    print('Package verified',len(manifest),'members',dest.stat().st_size,'bytes',sha256(dest))
if __name__=='__main__':run()
