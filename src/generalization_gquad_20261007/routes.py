"""Fixed endpoint metadata alignment; sign is not a fitted input column."""
from types import SimpleNamespace
from .common import np, label_hash, SHAPES, TRACKS
from .spec import ENDPOINT_SIGNS
from src.generalization_polarity_20261007.routes import endpoint_sign
from src.generalization_20261007.route_scaling import fit_model as pair_fit, predict_model as pair_predict

def configurations(track):
    assert track in TRACKS
    return [{'id': track + '_l2_' + name, 'penalty': p, 'scaling': 'pair'}
            for name, p in (('005', .005), ('05', .05), ('5', .5))]

def fit_model(frame, matrix, config, track):
    assert config in configurations(track) and matrix.shape == (len(frame), SHAPES[track])
    original = frame.measured_delta.to_numpy(float).copy(); signs = endpoint_sign(frame)
    training = frame.copy(deep=True); training['measured_delta'] = original * signs
    result = pair_fit(training, matrix, config)
    result.update({'alignment_track': track, 'endpoint_signs': dict(ENDPOINT_SIGNS),
        'fitted_columns': SHAPES[track], 'sign_is_learned_feature': False,
        'training_original_label_sha256': label_hash(original),
        'training_aligned_label_sha256': label_hash(training.measured_delta)})
    np.testing.assert_array_equal(frame.measured_delta.to_numpy(float), original)
    return result

def predict_model(model, matrix, frame):
    assert model['alignment_track'] in TRACKS and model['endpoint_signs'] == ENDPOINT_SIGNS
    assert not model['sign_is_learned_feature'] and model['fitted_columns'] == SHAPES[model['alignment_track']]
    assert matrix.shape == (len(frame), model['fitted_columns'])
    return pair_predict(model, matrix) * endpoint_sign(frame)

def module(track):
    return SimpleNamespace(CONFIGS=configurations(track), fit_model=lambda f, x, c: fit_model(f, x, c, track), predict_model=predict_model)
