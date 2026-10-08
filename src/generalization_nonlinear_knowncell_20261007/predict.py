"""Independent numeric model arithmetic; canonical scores retain exact ties."""
from .common import np
from src.generalization_nonlinear_crosscell_20261007.routes import validate_model as validate_hgb
from src.generalization_nonlinear_crosscell_20261007.ridge import validate_model as validate_ridge

def independent_hgb(model, matrix):
    """Partition row subsets down each numeric tree; no native predictor call."""
    validate_hgb(model)
    matrix = np.asarray(matrix, dtype=np.float64)
    assert matrix.ndim == 2 and matrix.shape[1] == model['width'] and np.isfinite(matrix).all()
    score = np.full(len(matrix), model['baseline'], dtype=np.float64)
    for tree in model['trees']:
        values = np.empty(len(matrix), dtype=np.float64)
        visited = np.zeros(len(matrix), dtype=int)
        stack = [(0, np.arange(len(matrix), dtype=int))]
        while stack:
            node, rows = stack.pop()
            if not len(rows):
                continue
            if tree['is_leaf'][node]:
                values[rows] = tree['value'][node]; visited[rows] += 1
            else:
                left = matrix[rows, tree['feature_idx'][node]] <= tree['num_threshold'][node]
                stack.append((tree['left'][node], rows[left]))
                stack.append((tree['right'][node], rows[~left]))
        assert (visited == 1).all()
        score += values
    return score

def independent_ridge(model, matrix):
    validate_ridge(model)
    matrix = np.asarray(matrix, dtype=np.float64)
    assert matrix.ndim == 2 and matrix.shape[1] == model['width'] and np.isfinite(matrix).all()
    supported = np.asarray(model['supported'], dtype=bool)
    beta, scale, mean = [np.asarray(model[field], dtype=np.float64) for field in ('beta', 'scale', 'mean')]
    result = np.empty(len(matrix), dtype=np.float64)
    for first in range(0, len(matrix), 1024):
        block = matrix[first:first + 1024]
        result[first:first + len(block)] = model['intercept'] + np.sum((block[:, supported] - mean[supported]) * (beta[supported] / scale[supported]), axis=1)
    return result

def canonical_scores(track, model, matrix, predictor):
    matrix = np.asarray(matrix, dtype=np.float64)
    # One unchanged complete target shape; never split native BLAS scoring.
    canonical = np.asarray(predictor(model, matrix), dtype=np.float64)
    independent = independent_hgb(model, matrix) if track.startswith('hgb/') else independent_ridge(model, matrix)
    assert canonical.shape == independent.shape == (len(matrix),) and len(matrix)
    assert np.isfinite(canonical).all() and np.isfinite(independent).all()
    error = float(np.max(np.abs(canonical - independent)))
    assert error < 1e-9, 'Independent model arithmetic differs from canonical source predictor'
    return canonical, error

def score_match(actual, saved):
    actual, saved = np.asarray(actual, dtype=float), np.asarray(saved, dtype=float)
    assert actual.shape == saved.shape and np.isfinite(actual).all() and np.isfinite(saved).all()
    error = float(np.max(np.abs(actual - saved)))
    assert error < 1e-9
    return error
