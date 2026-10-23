"""Pure resource/admission contracts; no system probes or project loaders.

The future controller must supply an actual immediately measured resource
probe and a separately admitted runtime loader. Nothing here overrides the
original three-GiB requirement or authorizes project execution.
"""
import math
from .spec import RAM_BYTES, DISK_BYTES

THREAD_KEYS = ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS')


def require_resources(snapshot, environment):
    assert isinstance(snapshot, dict)
    for key in ('physical_available', 'disk_available'):
        assert isinstance(snapshot[key], int) and snapshot[key] >= 0
    assert snapshot['physical_available'] >= RAM_BYTES, 'Original three-GiB RAM gate'
    assert snapshot['disk_available'] >= DISK_BYTES, 'Original one-GiB workspace disk gate'
    assert all(environment.get(key) == '1' for key in THREAD_KEYS), 'Exactly one numerical thread'
    assert snapshot.get('PUM_resource_exception_applied', False) is False
    return {'fresh_resource_probe_required': True, 'RAM_floor': RAM_BYTES,
            'disk_floor': DISK_BYTES, 'numerical_threads': 1,
            'PUM_resource_exception_applies': False}


def before_action(action, resource_probe, environment):
    """Enforce immediate probe->gate->action ordering; action remains root-owned."""
    assert callable(action) and callable(resource_probe)
    snapshot = resource_probe()
    require_resources(snapshot, environment)
    return action()


def birth_identity(*, arm, phase, outer_fold, inner_fold, configuration,
                   training_ids_sha256, training_metadata_sha256,
                   training_features_sha256, training_effects_sha256,
                   original_pair_roster_sha256, pair_weights_sha256,
                   common_scaling_sha256, runtime_binding_sha256, prefit_sha256):
    """Required future creation identity; no checkpoint is written or loaded."""
    from .spec import ARMS, FOLDS, CONFIGS, FEATURE_WIDTH, DEVIATION_MULTIPLIER
    assert arm in ARMS and phase in ('inner', 'outer') and outer_fold in FOLDS
    assert (phase == 'outer' and inner_fold is None) or (phase == 'inner' and inner_fold in set(FOLDS) - {outer_fold})
    assert configuration in CONFIGS
    hashes = {name: value for name, value in locals().copy().items() if name.endswith('_sha256')}
    for value in hashes.values():
        assert isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)
    return {'arm': arm, 'phase': phase, 'outer_fold': outer_fold, 'inner_fold': inner_fold,
            'configuration': dict(configuration), 'feature_width': FEATURE_WIDTH,
            'deviation_multiplier': DEVIATION_MULTIPLIER if arm == 'joint_shrink10' else None,
            'optimizer_units': 2 if arm == 'independent' else 1,
            'canonical_mean': 'all_zero_102_vector', 'numerical_threads': 1,
            'source_training_both_cells': True, 'original_truth_orientation': True,
            'old_fitted_checkpoint_reuse': False, **hashes}
