"""Fixed metadata orientation; all sequence columns fit, no learned sign."""
from .common import np, label_hash, SHAPES, TRACKS
from src.generalization_polarity_20261007.routes import endpoint_sign, ENDPOINT_SIGNS
from src.generalization_20261007.route_scaling import fit_model as pair_fit, predict_model as pair_predict


def configurations(track):
    assert track in TRACKS
    return [{"id":track + "_l2_" + name, "penalty":penalty, "scaling":"pair"}
            for name, penalty in (("005", .005), ("05", .05), ("5", .5))]


def fit_model(frame, matrix, config, track):
    assert config in configurations(track)
    matrix = np.asarray(matrix, dtype=float)
    assert matrix.shape == (len(frame), SHAPES[track]) and np.isfinite(matrix).all()
    original = frame.measured_delta.to_numpy(float).copy()
    training = frame.copy(deep=True)
    training["measured_delta"] = original * endpoint_sign(frame)
    result = pair_fit(training, matrix, config)
    result.update({"alignment_track":track, "endpoint_signs":dict(ENDPOINT_SIGNS),
                   "fitted_columns":SHAPES[track], "sign_is_learned_feature":False,
                   "training_original_label_sha256":label_hash(original),
                   "training_aligned_label_sha256":label_hash(training.measured_delta)})
    np.testing.assert_array_equal(frame.measured_delta.to_numpy(float), original)
    return result


def predict_model(model, matrix, frame):
    track = model["alignment_track"]
    assert track in TRACKS and model["endpoint_signs"] == ENDPOINT_SIGNS
    assert len(model["beta"]) == SHAPES[track]
    matrix = np.asarray(matrix, dtype=float)
    assert matrix.shape == (len(frame), SHAPES[track]) and np.isfinite(matrix).all()
    return pair_predict(model, matrix) * endpoint_sign(frame)
