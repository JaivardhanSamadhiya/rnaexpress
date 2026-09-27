from .common import *
from datetime import datetime,timezone
import subprocess,sys
def run():
    assert not (OUT/'fits').exists() and not (OUT/'development_freeze.json').exists()
    test=subprocess.run([sys.executable,'-u','-m','src.cross_assay_20260927.test_scoped'],cwd=ROOT,capture_output=True,text=True);assert test.returncode==0,test.stderr
    save(OUT/'prefit_tests.txt',(test.stdout+test.stderr).encode())
    paths=[p for d in (OUT,ART,REPORT,SRC) for p in d.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    files={str(p.relative_to(ROOT)).replace('\\','/'):sha256(p) for p in sorted(paths)}
    jsave(OUT/'development_freeze.json',{'frozen_utc':datetime.now(timezone.utc).isoformat(),'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'files':files,'all_outcomes_already_exposed':True,'new_grid_not_run':True,'gate_frozen_before_comparison':True,'tests':11,'external_discovery_allowed':False})
    print('Frozen',len(files),'files. Commit before starting development grid.')
if __name__=='__main__':run()
