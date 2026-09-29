from .common import *
import zipfile,sys,importlib.metadata

def run():
    frozen();assert readj(OUT/'verification_receipt.json')['status']=='PASS'
    reports=['protocol.md','replicate_reconstruction.md','probabilistic_targets.md','calibration_results.md','cross_replicate_results.md','leave_one_assay_out_results.md','generalization_gate_verdict.md','final_status.md'];artifacts=['replicate_candidate_measurements.csv','replicate_pairwise_evidence.csv','pairwise_probabilities.csv','candidate_rankings.csv','calibration.csv','model_comparison.csv','evidence_ledger.csv']
    assert all((REP/p).exists() for p in reports) and all((ART/p).exists() for p in artifacts)
    jsave(OUT/'runtime_receipt.json',{'python':sys.version,'executable':sys.executable,'packages':{k:importlib.metadata.version(k) for k in ['numpy','pandas','scipy']},'result_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'protocol_commit':'1c1f387','prefit_commit':'033c316','paid_resources':False,'downloads':False,'scheduled_tasks':False})
    paths=sorted(p for root in (SRC,REP,OUT,ART) for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.zip' and p.name!='delivery_receipt.json');manifest={p.relative_to(ROOT).as_posix():{'bytes':p.stat().st_size,'sha256':sha256(p)} for p in paths};dest=ART/'probabilistic_ranking_evidence.zip';assert not dest.exists()
    with zipfile.ZipFile(dest,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in paths:z.write(p,p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None and set(z.namelist())==set(manifest)
        for p,e in manifest.items():assert hashlib.sha256(z.read(p)).hexdigest()==e['sha256']
    jsave(ART/'delivery_receipt.json',{'status':'PASS','archive':dest.relative_to(ROOT).as_posix(),'bytes':dest.stat().st_size,'sha256':sha256(dest),'files':len(manifest),'manifest':manifest,'gate':readj(OUT/'gate_verdict.json')['status'],'crc_and_member_hashes_verified':True,'required_reports':8,'required_artifacts':7,'figure_topics':9,'self_contained_runtime':False})
    print('Evidence archive verified:',len(manifest),'files',dest.stat().st_size,'bytes',flush=True)
if __name__=='__main__':run()
