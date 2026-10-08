"""Standard-library metadata identities; this module never imports a model."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
NS = 'generalization_masked_likelihood_feasibility_20261007'
SRC, ART, OUT, REP = [ROOT / folder / NS for folder in ('src', 'artifacts', 'results', 'reports')]
MODEL = ROOT / 'data/external/splicebert/models/SpliceBERT.1024nt'
OLD_OUT = ROOT / 'results/generalization_splicebert_20261007'
REPAIR_OUT = ROOT / 'results/generalization_splicebert_runtime_compatibility_20261007'
CHECKPOINT_SHA = '2ad91428c318e6c49233154073ca7a35f5f7899c9f4be3444775bae3dba0149d'
VOCAB = ['[PAD]', '[UNK]', '[CLS]', '[SEP]', '[MASK]', 'N', 'A', 'C', 'G', 'T']
BLOCKED = ('numpy', 'torch', 'transformers', 'openvino', 'scipy', 'sklearn', 'pandas')
HEAD_KEYS = {
    'cls.predictions.transform.dense.weight': (512, 512),
    'cls.predictions.transform.dense.bias': (512,),
    'cls.predictions.transform.LayerNorm.weight': (512,),
    'cls.predictions.transform.LayerNorm.bias': (512,),
    'cls.predictions.decoder.weight': (10, 512),
    'cls.predictions.decoder.bias': (10,),
    'cls.predictions.bias': (10,),
}


def clean_imports(modules=None):
    modules = sys.modules if modules is None else modules
    assert not any(n == p or n.startswith(p + '.') for n in modules for p in BLOCKED), 'Fresh standard-library-only preparation required'


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def readj(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def jsave(path, value):
    path = Path(path).resolve()
    assert any(path.is_relative_to(folder.resolve()) for folder in (SRC, ART, OUT, REP))
    payload = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == payload, 'Preserve earlier preparation artifact'
    else:
        with path.open('xb') as stream:
            stream.write(payload)


def certify_alias_metadata(fields, tied=True):
    """Mockable admission contract; actual tensor metadata is not extracted here.

    A future restricted load must construct these records from actual tensors,
    before a tied stock loader can overwrite any inconsistent checkpoint alias.
    """
    required = dict(HEAD_KEYS)
    required['bert.embeddings.word_embeddings.weight'] = (10, 512)
    assert set(fields) == set(required), 'Exact selected head/embedding metadata required'
    for name, shape in required.items():
        row = fields[name]
        assert tuple(row['shape']) == shape and row['dtype'] == 'float32' and row['finite'] is True
        assert isinstance(row['sha256'], str) and len(row['sha256']) == 64 and set(row['sha256']) <= set('0123456789abcdef')
    assert tied is True, 'This fixed stock-head plan requires tied input/output embeddings'
    assert fields['cls.predictions.decoder.weight']['sha256'] == fields['bert.embeddings.word_embeddings.weight']['sha256'], 'Reject inconsistent tied checkpoint weights before loading'
    assert fields['cls.predictions.decoder.bias']['sha256'] == fields['cls.predictions.bias']['sha256'], 'Reject inconsistent decoder/bias aliases before loading'
    return True


def certify_encoder_metadata(backend, compatibility, numpy_proof, observed):
    """Validate only supplied receipt metadata; not a fresh native admission.

    observed must be independently measured by the later root-start probe.
    No numeric import, checkpoint read or backend invocation happens here.
    """
    assert backend['status'] == 'PASS' and backend['scope'] == 'SYNTHETIC_CPU_BACKEND_ADMISSION_ONLY'
    assert backend['checkpoint_sha256'] == CHECKPOINT_SHA and backend['synthetic_alleles'] == 16
    assert backend['project_alleles_inferred'] == backend['models_fit'] == 0 and backend['outcomes_used'] is False
    assert set(backend['unused_MLM_head_keys']) == set(HEAD_KEYS), 'Previously omitted head must have the exact planned keys'
    assert len(backend['comparisons']) == 8 and sorted(row['length_nt'] for row in backend['comparisons']) == [46,46,150,150,190,190,260,260]
    for row in backend['comparisons']:
        assert row['maximum_hidden_absolute_difference'] <= .001 and row['mean_hidden_absolute_difference'] <= .0001 and row['minimum_token_cosine'] >= .999999
        assert all(row['checks'].values())
    assert compatibility['status'] == 'PASS_SYNTHETIC_BACKEND_WITH_VERIFIED_NUMPY_ORIGIN'
    assert compatibility['full_production_authorized'] is False and compatibility['project_alleles'] == compatibility['models_fit'] == 0
    assert compatibility['outcomes_read'] is False and compatibility['original_guard_binding_restored'] is True
    assert numpy_proof['status'] == 'PASS' and numpy_proof['numpy_version'] == '1.26.4'
    assert numpy_proof['model_packages_imported_before_NumPy_verification'] is False
    assert Path(numpy_proof['numpy_origin']).resolve() == Path(observed['numpy_origin']).resolve()
    assert Path(numpy_proof['native_core_origin']).resolve() == Path(observed['native_core_origin']).resolve()
    assert numpy_proof['native_core_sha256'] == observed['native_core_sha256']
    for key in ('IR_xml_sha256', 'IR_bin_sha256'):
        assert backend[key] == compatibility[key] == observed[key]
    links = {'original_backend_synthetic_receipt_sha256':'backend_sha256', 'NumPy_import_receipt_sha256':'numpy_proof_sha256', 'repair_preparation_sha256':'repair_preparation_sha256'}
    for left, right in links.items():
        assert compatibility[left] == observed[right]
    assert numpy_proof['repair_preparation_sha256'] == observed['repair_preparation_sha256']
    assert numpy_proof['scientific_runtime_receipt_sha256'] == observed['scientific_runtime_receipt_sha256']
    return True
