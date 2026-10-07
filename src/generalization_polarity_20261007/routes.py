"""Fixed biological endpoint orientation; sign is never a learned coefficient."""
from types import SimpleNamespace
import hashlib
from .common import np, TRACKS
from src.generalization_20261007.route_scaling import (
    fit_model as pair_fit, predict_model as pair_predict,
)

CONFIGS = [
    {'id':'pair_005', 'penalty':.005, 'scaling':'pair'},
    {'id':'pair_05', 'penalty':.05, 'scaling':'pair'},
    {'id':'pair_5', 'penalty':.5, 'scaling':'pair'},
]
ENDPOINT_SIGNS = {'projection':1., 'nuclear_cytoplasmic':-1.}


def endpoint_sign(frame):
    """Use canonical biological endpoint metadata only, never source or effect."""
    if 'endpoint_class' not in frame:
        raise ValueError('Known endpoint_class is required; no source-ID fallback')
    values = frame.endpoint_class.astype(str).str.strip().str.lower()
    unsupported = sorted(set(values)-set(ENDPOINT_SIGNS))
    if unsupported:
        raise ValueError('Unsupported endpoint classes: '+str(unsupported))
    signs = values.map(ENDPOINT_SIGNS).to_numpy(float)
    if 'parent_context_id' in frame:
        constant = frame.assign(_routing_sign=signs).groupby('parent_context_id')._routing_sign.nunique()
        assert constant.eq(1).all(), 'One candidate set must have one declared endpoint'
    return signs


def build_features(frame, base246):
    base = np.asarray(base246, dtype=float)
    assert base.shape == (len(frame),246) and np.isfinite(base).all()
    return np.column_stack([base, endpoint_sign(frame)])


def checked_matrix(matrix):
    matrix = np.asarray(matrix, dtype=float)
    assert matrix.ndim == 2 and matrix.shape[1] == 247 and np.isfinite(matrix).all()
    assert np.isin(matrix[:,-1],[-1.,1.]).all(), 'Endpoint sign must be declared +/-1'
    return matrix


def fit_model(frame, matrix, config, track):
    assert track in TRACKS and config in CONFIGS
    matrix = checked_matrix(matrix)
    signs = endpoint_sign(frame)
    np.testing.assert_array_equal(matrix[:,-1], signs)
    original = frame.measured_delta.to_numpy(float)
    training = frame.copy(deep=True)
    if track == 'polarity':
        training['measured_delta'] = original * signs
    fitted = pair_fit(training, matrix[:,:246], config)
    fitted['track'] = track
    fitted['endpoint_signs'] = dict(ENDPOINT_SIGNS)
    fitted['fitted_columns'] = 246
    fitted['metadata_sign_is_learned_feature'] = False
    fitted['training_original_effect_sha256'] = hashlib.sha256(original.tobytes()).hexdigest()
    fitted['training_used_effect_sha256'] = hashlib.sha256(training.measured_delta.to_numpy(float).tobytes()).hexdigest()
    np.testing.assert_array_equal(frame.measured_delta.to_numpy(float), original)
    return fitted


def predict_model(model, matrix):
    matrix = checked_matrix(matrix)
    assert model['track'] in TRACKS and model['endpoint_signs'] == ENDPOINT_SIGNS
    assert len(model['beta']) == 246
    utility = pair_predict(model, matrix[:,:246])
    return utility * matrix[:,-1] if model['track'] == 'polarity' else utility


def module(track):
    assert track in TRACKS
    return SimpleNamespace(CONFIGS=CONFIGS,
        fit_model=lambda frame, matrix, config:fit_model(frame,matrix,config,track),
        predict_model=predict_model)
