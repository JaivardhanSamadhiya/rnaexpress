"""Create a manifest before outcome access. Commit it, then commit the marker."""
from .common import *
from datetime import datetime,timezone
import subprocess,sys

def run():
    assert not (OUT/'outcome_access_started.json').exists()
    assert not (OUT/'prefit_freeze.json').exists()
    result=subprocess.run([sys.executable,'-u','-m','src.generalization_20260926.test_prefit'],cwd=ROOT,capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    save(OUT/'prefit_scoped_tests.txt',(result.stdout+result.stderr).encode())
    paths=[]
    for directory in (ROOT/'src/generalization_20260926',OUT,ART,REPORT):
        paths.extend(p for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    paths.extend([WORKBOOK,SOURCE/'GSE330741_RAW.tar',ROOT/'data/frozen/external_manifest.json',ROOT/'data/frozen/astrocyte_external_features.csv.gz',ROOT/'data/frozen/astrocyte_pairing_audit.json',ROOT/'results/srle_prediction_20260926/fitted_parameters.json',ROOT/'results/srle_prediction_20260926/sequence_inventory.csv'])
    files={p.relative_to(ROOT).as_posix():sha256(p) for p in sorted(set(paths))}
    jsave(OUT/'prefit_freeze.json',{'frozen_utc':datetime.now(timezone.utc).isoformat(),'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'outcomes_opened_in_current_analysis':False,'historical_exposure':'PARTIALLY EXPOSED','files':files,'tests':12,'stage':'before protocol commit and access marker; no outcomes permitted until both are committed'})
    print('Frozen',len(files),'hashes; outcome access still prohibited until commits and marker.')

if __name__=='__main__':run()
