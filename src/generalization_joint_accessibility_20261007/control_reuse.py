"""Reuse frozen RBP controls only after complete source-only canonical replay."""
from .common import *
from .assemble import source_controls

def checked_files(receipt):
    assert receipt['status'] == 'PASS' and receipt['models_fit'] == 0
    for name, expected in receipt['files'].items():
        path = (ROOT / name).resolve()
        assert path.is_relative_to(ROOT.resolve()) and sha256(path) == expected, name

def prepare_reference():
    source_controls()
    freeze = readj(RBP_OUT / 'prefit_manifest.json'); freeze_sha = sha256(RBP_OUT / 'prefit_manifest.json')
    replay_path = RBP_OUT / 'canonical_source_only_replay.json'; replay = readj(replay_path)
    checked_files(replay)
    assert replay['namespace'] == 'generalization_rbp_20261007'
    assert replay['prefit_manifest_sha256'] == freeze_sha and replay['inner_checkpoints_checked'] == 108 and replay['outer_checkpoints_checked'] == 12
    assert replay['replicate_evidence_opened'] is False and replay['historical_data_npz_loaded'] is False
    assert replay['core_sha256'] == sha256(certified_core())
    assert replay['numerical_threads'] == 1 and replay['maximum_independent_arithmetic_error'] <= 1e-9
    assert replay['loaded_numeric_libraries']['numpy_version'] == np.__version__
    assert replay['loaded_numeric_libraries']['pandas_version'] == pd.__version__
    assert replay['loaded_numeric_libraries']['numpy_init_sha256'] == sha256(np.__file__)
    assert replay['loaded_numeric_libraries']['pandas_init_sha256'] == sha256(pd.__file__)
    files = {replay_path.relative_to(ROOT).as_posix(): sha256(replay_path),
             (RBP_OUT / 'prefit_manifest.json').relative_to(ROOT).as_posix(): freeze_sha}
    for track in CONTROLS:
        complete = readj(RBP_OUT / track / 'run_complete.json')
        assert complete['status'] == 'PASS' and complete['fit_files'] == 40 and complete['prediction_rows'] == 26258 and complete['prefit_manifest_sha256'] == freeze_sha
        fitting = list((RBP_OUT / track / 'fits').glob('*.json')); assert len(fitting) == 40
        for path in fitting + [RBP_OUT / track / filename for filename in ('predictions.csv.gz', 'decisions.csv', 'comparison.csv', 'inner_selection.csv', 'folds.json', 'run_complete.json')]:
            name = path.relative_to(ROOT).as_posix(); assert replay['files'][name] == sha256(path), name
            files[name] = sha256(path)
        path = RBP_ART / (track + '_model_features.npz'); name = path.relative_to(ROOT).as_posix()
        assert freeze['files'][name] == sha256(path); files[name] = sha256(path)
    for name in ('src/generalization_rbp_20261007/routes.py', 'src/generalization_20261007/route_scaling.py', 'src/cross_assay_20260927/models.py'):
        assert freeze['files'][name] == sha256(ROOT / name); files[name] = sha256(ROOT / name)
    jsave(OUT / 'control_reuse_receipt.json', {'status': 'PASS', 'policy': 'REUSE_ORIGINAL_THREE_RBP_CONTROLS_NO_REFIT',
        'control_prefit_sha256': freeze_sha, 'control_canonical_source_only_replay_sha256': sha256(replay_path),
        'original_labels_sha256': replay['mean_effect_float64_sha256'], 'core_sha256': replay['core_sha256'],
        'standalone_new_tracks': TRACKS, 'reused_control_tracks': CONTROLS, 'reused_control_fits': 120,
        'new_fits_required': 80, 'files': files, 'models_fit': 0,
        'scope': 'Previously exposed development controls, byte-identical feature/label/config/solver/source purges certified by original freeze and independent canonical nested replay; not new evidence or retroactive checkpoint birth digests'})

def check():
    receipt = readj(OUT / 'control_reuse_receipt.json'); checked_files(receipt)
    assert receipt['policy'] == 'REUSE_ORIGINAL_THREE_RBP_CONTROLS_NO_REFIT'
    assert receipt['control_prefit_sha256'] == sha256(RBP_OUT / 'prefit_manifest.json')
    assert receipt['control_canonical_source_only_replay_sha256'] == sha256(RBP_OUT / 'canonical_source_only_replay.json')
    return receipt

if __name__ == '__main__':
    prepare_reference()
