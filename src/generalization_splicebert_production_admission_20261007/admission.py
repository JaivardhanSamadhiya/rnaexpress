"""Keep original production freeze unchanged; pin its actual NumPy provenance."""
from pathlib import Path
from contextlib import contextmanager
import hashlib, importlib, json, os, subprocess, sys

ROOT = Path(__file__).resolve().parents[2]
NS = 'generalization_splicebert_production_admission_20261007'
SRC, OUT, REP = [ROOT / base / NS for base in ('src', 'results', 'reports')]
REPAIR = ROOT / 'results/generalization_splicebert_runtime_compatibility_20261007'
BACK = ROOT / 'results/generalization_splicebert_20261007'
IR = ROOT / 'artifacts/generalization_splicebert_20261007/backend/splicebert_1024_fp32.xml'
TARGET = ROOT / 'results/generalization_splicebert_downstream_20261007/feature_production_manifest.json'
MANIFEST = OUT / 'preparation_manifest.json'

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''): h.update(block)
    return h.hexdigest()

def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))

def save(path, value):
    path = Path(path).resolve()
    assert path.is_relative_to(OUT.resolve())
    payload = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n').encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists(): assert path.read_bytes() == payload, 'Preserve admission receipt'
    else:
        with path.open('xb') as f: f.write(payload)

def committed(path):
    assert subprocess.check_output(['git','show','HEAD:'+Path(path).relative_to(ROOT).as_posix()], cwd=ROOT) == Path(path).read_bytes()

def backend_chain():
    """Only metadata/byte checks; never import numerical or model packages."""
    prep = read(REPAIR/'preparation_manifest.json')
    assert prep['status'] == 'FROZEN_ADDITIVE_NUMPY_COMPATIBILITY_PREPARATION'
    paths = {name: digest for name,digest in prep['files'].items()}
    compat = read(REPAIR/'backend_compatibility_receipt.json')
    proof = read(REPAIR/'numpy_import_receipt.json')
    backend = read(BACK/'backend_synthetic_receipt.json')
    assert compat['status'] == 'PASS_SYNTHETIC_BACKEND_WITH_VERIFIED_NUMPY_ORIGIN'
    assert compat['repair_preparation_sha256'] == sha(REPAIR/'preparation_manifest.json')
    assert compat['NumPy_import_receipt_sha256'] == sha(REPAIR/'numpy_import_receipt.json')
    assert compat['original_backend_synthetic_receipt_sha256'] == sha(BACK/'backend_synthetic_receipt.json')
    assert compat['original_guard_binding_restored'] and compat['source_guard_runs'] == 1
    assert compat['synthetic_alleles'] == 16 and compat['models_fit'] == 0 and not compat['outcomes_read']
    assert backend['status'] == 'PASS' and backend['headroom_before_import']['additive_NumPy_runtime_compatibility'] == proof
    assert proof['numpy_version'] == '1.26.4' and proof['original_guard_calls'] == 1
    assert compat['IR_xml_sha256'] == backend['IR_xml_sha256'] == sha(IR)
    assert compat['IR_bin_sha256'] == backend['IR_bin_sha256'] == sha(IR.with_suffix('.bin'))
    for p in (REPAIR/'preparation_manifest.json', REPAIR/'numpy_import_receipt.json',
              REPAIR/'backend_compatibility_receipt.json', BACK/'backend_synthetic_receipt.json', IR, IR.with_suffix('.bin')):
        paths[p.relative_to(ROOT).as_posix()] = sha(p)
    for name,digest in paths.items(): assert sha(ROOT/name) == digest, name
    return paths

def prepare():
    assert not MANIFEST.exists() and not TARGET.exists()
    paths = backend_chain()
    for base in (SRC, REP):
        for p in base.glob('*'):
            if p.is_file(): paths[p.relative_to(ROOT).as_posix()] = sha(p)
    tests = OUT/'scoped_tests_receipt.json'
    assert read(tests)['status'] == 'PASS' and read(tests)['tests'] == 8
    assert read(tests)['source_sha256'] == sha(__file__)
    for p in (tests, OUT/'.gitattributes', ROOT/'src/generalization_splicebert_downstream_20261007/prepare.py',
              ROOT/'results/generalization_splicebert_downstream_20261007/synthetic_tests_receipt_final_review.json'):
        paths[p.relative_to(ROOT).as_posix()] = sha(p)
    save(MANIFEST, {'status':'FROZEN_ADDITIVE_ACTUAL_BACKEND_RUNTIME_ADMISSION', 'files':paths,
        'model_inference':False, 'project_features':False, 'outcomes_read':False, 'models_fit':0,
        'original_freeze_calls_planned':1, 'all_original_checks_retained':True})

def make_saver(original, extra, provenance, target=TARGET, hasher=sha, exists=None):
    exists = (lambda p: Path(p).exists()) if exists is None else exists
    calls = []
    def writer(path, value):
        assert not calls and Path(path).resolve() == Path(target).resolve()
        assert not exists(target), 'Preserve existing production manifest'
        assert value['status'] == 'FROZEN_SPLICEBERT_FEATURE_PRODUCTION'
        assert value['rows'] == 26258 and value['unique_alleles'] == 18220 and value['columns'] == 256
        assert value['threads'] == value['batch_size'] == 2
        assert value['fresh_3GiB_RAM_and_5GiB_disk_required'] and value['root_start_required']
        assert value['native_IR_synthetic_parity_required_and_passed'] and value['no_supervised_fit_authorized']
        assert 'actual_backend_runtime_admission' not in value
        updated = {**value, 'files':dict(value['files'])}
        for name,digest in extra.items():
            assert hasher(ROOT/name) == digest
            if name in updated['files']: assert updated['files'][name] == digest
            updated['files'][name] = digest
        updated['actual_backend_runtime_admission'] = dict(provenance)
        calls.append(True)
        return original(path, updated)
    writer.calls = calls
    return writer

@contextmanager
def temporary_saver(module, writer):
    previous = module.jsave
    module.jsave = writer
    try: yield
    finally: module.jsave = previous

def run():
    assert sys.argv[1:] == ['--root-start']
    assert os.environ.get('PYTHONDONTWRITEBYTECODE') == '1'
    assert all(os.environ.get(v)=='2' for v in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'))
    committed(MANIFEST)
    manifest = read(MANIFEST)
    assert manifest['status'] == 'FROZEN_ADDITIVE_ACTUAL_BACKEND_RUNTIME_ADMISSION'
    for name,digest in manifest['files'].items(): assert sha(ROOT/name) == digest, name
    backend_chain()
    assert not TARGET.exists() and not (OUT/'production_numpy_receipt.json').exists()
    from src.generalization_splicebert_runtime_compatibility_20261007 import common as rc
    from src.generalization_splicebert_runtime_compatibility_20261007.launcher import numpy_proof
    runtime = read(rc.RUNTIME_RECEIPT)
    rc.check_runtime(runtime)
    # Normal experiment bootstrap supplies the same certified CP312 scientific prefix.
    importlib.import_module('src.research_20260921.common')
    np = importlib.import_module('numpy')
    proof = numpy_proof(np, runtime)
    proof['role'] = 'ACTUAL_ORIGINAL_DOWNSTREAM_NUMPY_BEFORE_PROJECT_INFERENCE'
    save(OUT/'production_numpy_receipt.json', proof)
    module = importlib.import_module('src.generalization_splicebert_downstream_20261007.prepare')
    extra = {**manifest['files'], MANIFEST.relative_to(ROOT).as_posix():sha(MANIFEST),
             (OUT/'production_numpy_receipt.json').relative_to(ROOT).as_posix():sha(OUT/'production_numpy_receipt.json')}
    provenance = {'preparation_manifest_sha256':sha(MANIFEST), 'original_freeze_delegated_once':True,
        'original_sources_or_checks_modified':False, 'actual_NumPy_import_receipt_sha256':sha(OUT/'production_numpy_receipt.json'),
        'additional_chain_rechecked_by_original_production_and_prefit':True}
    old = module.jsave
    writer = make_saver(old, extra, provenance)
    with temporary_saver(module, writer): module.freeze_production()
    assert module.jsave is old and len(writer.calls) == 1
    save(OUT/'execution_receipt.json', {'status':'PASS_ORIGINAL_PRODUCTION_FREEZE_WITH_ACTUAL_RUNTIME_CHAIN',
        'production_manifest_sha256':sha(TARGET), 'preparation_manifest_sha256':sha(MANIFEST),
        'original_bindings_restored':True, 'project_features_extracted':0, 'models_fit':0,
        'root_commits_resulting_manifest_before_producer':True})
    print('SpliceBERT production freeze PASS with actual runtime chain; commit before producer',flush=True)

if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']: prepare()
    else: run()
