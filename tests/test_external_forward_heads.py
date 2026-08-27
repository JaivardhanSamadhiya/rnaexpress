import numpy as np

from src.modeling.external_forward_heads import apply_head, representation_matrix


def test_external_head_applies_frozen_scaler_and_multioutput_coefficients() -> None:
    features = np.asarray([[1.0, 4.0], [3.0, 8.0]])
    mean = np.asarray([1.0, 2.0])
    scale = np.asarray([2.0, 2.0])
    coefficient = np.asarray([[1.0, 2.0], [-1.0, 0.5]])
    intercept = np.asarray([0.5, -0.5])

    prediction = apply_head(features, mean, scale, coefficient, intercept)

    assert np.allclose(prediction, [[2.5, 0.0], [7.5, 0.0]])


def test_external_representation_order_is_frozen() -> None:
    embedded = np.arange(2 * 1024, dtype=float).reshape(2, 1024)
    handcrafted = np.arange(6, dtype=float).reshape(2, 3)

    assert np.array_equal(
        representation_matrix("mean", embedded, handcrafted), embedded[:, 512:]
    )
    assert np.array_equal(
        representation_matrix("cls_mean", embedded, handcrafted), embedded
    )
    full = representation_matrix("cls_mean_handcrafted", embedded, handcrafted)
    assert np.array_equal(full[:, :1024], embedded)
    assert np.array_equal(full[:, 1024:], handcrafted)
