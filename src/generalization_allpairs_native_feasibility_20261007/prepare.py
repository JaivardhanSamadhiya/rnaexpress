"""Metadata-only preparation; neither imports nor executes native array code."""
import ast
from . import common as c, spec as s

def run():
    c.clean_imports();assert not c.MANIFEST.exists();c.freshness()
    receipt=c.readj(c.TESTS);assert receipt['status']=='PASS_STDLIB_PREPARATION_ONLY' and receipt['tests']==15
    for name,expected in receipt['files'].items():assert c.sha(c.ROOT/name)==expected,name
    scientific=c.readj(c.SCIENTIFIC)
    assert scientific['status']=='PASS' and scientific['numpy_version']==s.EXPECTED_NUMPY and scientific['file_count']==len(scientific['files'])
    proof=c.readj(c.ROOT/'results/generalization_allpairs_feasibility_20261007/synthetic_receipt_v2.json')
    assert proof['tests']==10 and proof['status']=='PASS_STDLIB_SYNTHETIC_OBJECTIVE_FEASIBILITY_ONLY'
    for group in ('source_report_sha256','historical_source_sha256'):
        for name,expected in proof[group].items():assert c.sha(c.ROOT/name)==expected,name
    paths=[*c.SRC.glob('*.py'),c.REP/'plan.md',c.TESTS,*c.PREREQUISITES,*[p/'.gitattributes' for p in (c.SRC,c.ART,c.OUT,c.REP)],
           c.OUT/'preparation_manifest.json',c.OUT/'synthetic_tests_receipt.json']
    files={p.relative_to(c.ROOT).as_posix():c.sha(p) for p in paths}
    for p in c.SRC.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'),filename=str(p))
    own=[name for name in files if s.NS in name]
    c.jsave(c.MANIFEST,{'status':'FROZEN_INVENTED_ALLPAIRS_NATIVE_PREPARATION','files':files,'own_committed_files':own,
        'tests':15,'native_executed':False,'project_data_or_fitting_authorized':False,'numerical_packages_imported':False,
        'generation':2,'initial_source_only_preparation_and_tests_preserved_as_superseded_review_records':True,
        'sizes':s.SIZES,'dimensions':s.WIDTHS,'block':s.BLOCK,'cap':s.CAP,'repeats':s.REPEATS,'threads':1,
        'small_optimizer_shape':s.SMALL_OPTIMIZER_SHAPE,'small_optimizer_calls_planned':4,
        'runtime_file_count':scientific['file_count'],'runtime_bytes':scientific['total_bytes'],
        'runtime_is_installed_observed_bytes_not_reproducible_build':True,
        'root_review_commit_and_explicit_native_start_required':True,'protected_or_project_inputs':0})
    c.clean_imports();print('Native all-pair preparation frozen locally',len(files),c.sha(c.MANIFEST),flush=True)

if __name__=='__main__':run()
