from .common import *
import sys

def run():
    legacy_frozen();assert not (OUT/'prefit_manifest.json').exists()
    p=subprocess.run([sys.executable,'-u','-m','src.probabilistic_ranking_20260928.test_scoped'],cwd=ROOT,capture_output=True,text=True);save(OUT/'prefit_tests.txt',(p.stdout+p.stderr).encode());assert p.returncode==0,p.stderr
    paths=[p for d in (SRC,REP,OUT,ART) for p in d.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    files={p.relative_to(ROOT).as_posix():sha256(p) for p in sorted(paths)}
    jsave(OUT/'prefit_manifest.json',{'files':files,'protocol_commit':'1c1f387','comparative_fits_run':False,'primary_models':PRIMARY,'secondary_models':SECONDARY,'fixed_representation':'interaction_3','new_external_data_allowed':False,'tests':9})
    print('Prefit frozen',len(files),'files; commit before run.',flush=True)
if __name__=='__main__':run()
