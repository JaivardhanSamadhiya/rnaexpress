"""Process-local operational callbacks; original scientific source is immutable."""
from contextlib import contextmanager
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

from src.generalization_prelib_numpy_profile_v2_20261022.invented import ROOT, sha, current_numpy_payload
from src.generalization_pum_process_probe_20261021 import headless
from src.generalization_splicebert_runtime_compatibility_20261007 import launcher
from src.generalization_current_python_20261022 import attest

OUT = ROOT / 'results/generalization_prelib_bounded_execution_20261022'
BIO = ROOT / 'results/generalization_prelib_pooled_lineage_20261009'
MANIFEST = OUT / 'execution_manifest.json'
AUTH = OUT / 'authorization.json'
PHASES = ('features', 'prefit', 'fit', 'evaluate', 'verify')
COMPLETION = {
    'features': 'feature_receipt.json', 'prefit': 'prefit_manifest.json',
    'fit': 'fit_receipt.json', 'evaluate': 'provisional_verdict.json',
    'verify': 'independent_model_score_and_gate_replay_receipt.json',
}
GUARD_COUNTS = {'features': 10, 'prefit': 1, 'fit': 403, 'evaluate': 1, 'verify': 24}


def save(path, data):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(data, indent=2, allow_nan=False) + '\n')


def committed(path):
    assert headless.GitFacade(subprocess).check_output(
        ['git', 'show', 'HEAD:' + path.relative_to(ROOT).as_posix()], cwd=ROOT
    ) == path.read_bytes(), str(path)


def check_worker_binding(receipt, phase, manifest_sha, completion_sha):
    assert receipt['status'] == 'ORIGINAL_PRELIB_STAGE_COMPLETE_CALLBACKS_RESTORED'
    assert receipt['phase'] == phase
    assert receipt['execution_manifest_sha256'] == manifest_sha
    assert receipt['completion_sha256'] == completion_sha
    assert receipt['scientific_sources_unchanged'] is True and receipt['callbacks_restored'] is True
    assert receipt['fresh_guard_calls'] == GUARD_COUNTS[phase]
    assert receipt['current_python_numpy_bootstraps'] == (1 if phase in ('features', 'fit', 'verify') else 0)


def check_predecessor_binding(receipt, phase, manifest_sha, completion_sha, worker_sha):
    assert receipt['status'] == 'PASS_BOUNDED_ORIGINAL_PRELIB_STAGE'
    assert receipt['phase'] == phase
    assert receipt['execution_manifest_sha256'] == manifest_sha
    assert receipt['scientific_completion_sha256'] == completion_sha
    assert receipt['worker_receipt_sha256'] == worker_sha
    assert receipt['frozen_sources_unchanged'] is True and receipt['exit_code'] == 0


def current_python_identity():
    receipt = json.loads(attest.ATTESTATION.read_bytes())
    assert receipt['python_version'] == sys.version
    assert receipt['source_sha256'] == sha(attest.__file__)
    assert Path(receipt['python_executable']).resolve() == Path(sys.executable).resolve()
    return attest.native_python(receipt['python_native_files'])


def admit(phase):
    assert phase in PHASES
    committed(MANIFEST)
    manifest = json.loads(MANIFEST.read_bytes())
    assert manifest['status'] == 'FROZEN_PRELIB_ONLY_OPERATIONAL_ADAPTER_AWAITING_EXPLICIT_APPROVAL'
    assert Path(sys.executable).resolve() == Path(manifest['python_executable']).resolve()
    assert sha(sys.executable) == manifest['python_executable_sha256']
    for rel, want in manifest['files'].items():
        assert sha(ROOT / rel) == want, rel
    assert headless.native_origins() == manifest['native_origins']
    current_python_identity()
    committed(AUTH)
    authorization = json.loads(AUTH.read_bytes())
    assert authorization['status'] == 'EXACT_USER_APPROVAL_RECORDED'
    assert authorization['execution_manifest_sha256'] == sha(MANIFEST)
    assert authorization['approved_phases'] == list(PHASES)
    assert authorization['spending_authorized'] is False
    earlier = PHASES[:PHASES.index(phase)]
    if earlier:
        previous = earlier[-1]
        committed(OUT / (previous + '_supervisor_receipt.json'))
        receipt = json.loads((OUT / (previous + '_supervisor_receipt.json')).read_bytes())
        completion = BIO / COMPLETION[previous]
        prior_worker = OUT / (previous + '_worker_receipt.json')
        committed(completion)
        committed(prior_worker)
        check_predecessor_binding(receipt, previous, sha(MANIFEST), sha(completion), sha(prior_worker))
        check_worker_binding(json.loads(prior_worker.read_bytes()), previous, sha(MANIFEST), sha(completion))
    assert not (BIO / COMPLETION[phase]).exists(), 'Preserve existing stage completion'
    if phase == 'features':
        assert not (BIO / 'fixed_feature_roster.json.gz').exists()
    elif phase == 'prefit':
        assert not (BIO / 'fold_and_weight_roster.json').exists()
    elif phase == 'fit':
        assert not list(BIO.glob('fit_*.json.gz')), 'No automatic partial-fit resumption'
    elif phase == 'evaluate':
        assert not (BIO / 'evaluation_results.json').exists()
    return manifest


def resource_guard(state=None):
    value = headless.memory() if state is None else state
    assert value['physical_available'] >= 512 * 2**20, 'Fresh512MiB required'
    assert value['commit_headroom'] >= 896 * 2**20 + 2**30, 'Fresh job cap plus1GiB system reserve required'
    assert value['disk_available'] >= 2**30, 'Fresh1GiB disk required'
    return value['physical_available']


@contextmanager
def scoped_callbacks(gate, phase, manifest_sha, guard=resource_guard):
    original_fresh, original_numpy, original_save = gate.fresh, gate.numpy_runtime, gate.save
    counts = {'fresh_guard_calls': 0, 'current_python_numpy_bootstraps': 0}

    def bounded_fresh():
        counts['fresh_guard_calls'] += 1
        return guard()

    def current_runtime():
        counts['current_python_numpy_bootstraps'] += 1
        assert counts['current_python_numpy_bootstraps'] == 1
        bounded_fresh()
        launcher.clean_import_state()
        assert os.environ.get('OMP_NUM_THREADS') == os.environ.get('OPENBLAS_NUM_THREADS') == '2'
        assert os.environ.get('PYTHONUTF8') == os.environ.get('PYTHONDONTWRITEBYTECODE') == '1'
        runtime, python_proof = current_numpy_payload()
        launcher.select_prefix()
        np = importlib.import_module('numpy')
        numpy_proof = launcher.numpy_proof(np, runtime)
        loaded_python = attest.native_python(python_proof['current_python_native_files'])
        bounded_fresh()
        return np, {
            'status': 'PASS_UNCHANGED_NUMPY_PAYLOAD_WITH_SEPARATE_CURRENT_PYTHON_PROVENANCE',
            'old_NumPy_payload_proof': numpy_proof, 'current_python_proof': python_proof,
            'actually_loaded_current_python_DLLs': loaded_python,
            'old_full_runtime_python_identity_passes': False,
            'execution_manifest_sha256': manifest_sha,
            'invented_compatibility_receipt_sha256': sha(ROOT / 'results/generalization_prelib_numpy_profile_v2_20261022/invented_numpy_receipt.json'),
        }

    def transparent_save(path, payload, compressed=False):
        if Path(path) == BIO / COMPLETION[phase]:
            payload = dict(payload)
            payload['operational_admission'] = {
                'original_3GiB_floor_overridden_for_this_named_stage': True,
                'execution_manifest_sha256': manifest_sha, 'stage': phase,
                'scientific_source_targets_features_weights_grid_gate_unchanged': True,
                'current_python_identity_is_additive_not_old_runtime_recertification': True,
                **counts,
            }
        return original_save(path, payload, compressed)

    gate.fresh, gate.numpy_runtime, gate.save = bounded_fresh, current_runtime, transparent_save
    try:
        yield counts
    finally:
        gate.fresh, gate.numpy_runtime, gate.save = original_fresh, original_numpy, original_save


def run(phase, supervisor):
    assert phase in PHASES and os.getppid() == supervisor
    with (OUT / (phase + '_worker.log')).open('x', encoding='utf-8', buffering=1) as log:
        sys.stdout = log
        sys.stderr = log
        try:
            manifest = admit(phase)
            resource_guard()
            gate = importlib.import_module('src.generalization_prelib_pooled_lineage_20261009.pipeline')
            if phase == 'verify':
                entry = importlib.import_module('src.generalization_prelib_pooled_lineage_20261009.verify').run
            else:
                entry = getattr(gate, phase)
            old = (gate.fresh, gate.numpy_runtime, gate.save)
            with headless.scoped_git(gate):
                with scoped_callbacks(gate, phase, sha(MANIFEST)) as counts:
                    entry()
            assert (gate.fresh, gate.numpy_runtime, gate.save) == old
            assert counts['fresh_guard_calls'] == GUARD_COUNTS[phase]
            assert counts['current_python_numpy_bootstraps'] == (1 if phase in ('features', 'fit', 'verify') else 0)
            current_python_identity()
            for rel, want in manifest['scientific_files'].items():
                assert sha(ROOT / rel) == want, rel
            completion = BIO / COMPLETION[phase]
            assert completion.exists()
            save(OUT / (phase + '_worker_receipt.json'), {
                'status': 'ORIGINAL_PRELIB_STAGE_COMPLETE_CALLBACKS_RESTORED', 'phase': phase,
                'execution_manifest_sha256': sha(MANIFEST), 'completion_sha256': sha(completion),
                'scientific_sources_unchanged': True, 'callbacks_restored': True, **counts,
                'biological_fits_performed': 399 if phase == 'fit' else 0,
                'localization_generalization_pass': False,
            })
            print('ORIGINAL_PRELIB_STAGE_COMPLETE', phase, flush=True)
        except BaseException:
            import traceback
            traceback.print_exc()
            raise


if __name__ == '__main__':
    run(sys.argv[1], int(sys.argv[2]))
