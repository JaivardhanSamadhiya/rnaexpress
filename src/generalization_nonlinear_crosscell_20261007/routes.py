"""Fixed pointwise histogram boosting; safe numeric JSON tree checkpoints."""
from types import SimpleNamespace
import hashlib
import inspect
import os
from .common import np, pd, TRACKS, ROOT, OUT, sha256, readj

CONFIGS = [{'id': 'hgb_7', 'max_leaf_nodes': 7},
           {'id': 'hgb_15', 'max_leaf_nodes': 15},
           {'id': 'hgb_31', 'max_leaf_nodes': 31}]
FIXED = {'loss': 'squared_error', 'learning_rate': .05, 'max_iter': 200,
         'max_bins': 64, 'min_samples_leaf': 20, 'l2_regularization': 1.,
         'early_stopping': False, 'random_state': 20261007, 'categorical_features': None,
         'max_depth': None, 'max_features': 1., 'monotonic_cst': None,
         'interaction_cst': None, 'warm_start': False, 'verbose': 0}
FIELDS = ('value', 'feature_idx', 'num_threshold', 'missing_go_to_left',
          'left', 'right', 'is_leaf')


def runtime_binding():
    import sklearn
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.ensemble._hist_gradient_boosting import predictor, common
    from sklearn.utils import _openmp_helpers
    import threadpoolctl
    assert sklearn.__version__ == '1.5.2'
    runtime = ROOT / 'data/interim/mechanism_v2/runtime'
    classfile = inspect.getfile(HistGradientBoostingRegressor)
    assert str(classfile).startswith(str(runtime))
    files = [sklearn.__file__, classfile, predictor.__file__, common.__file__,
             _openmp_helpers.__file__, threadpoolctl.__file__]
    hist = runtime / 'sklearn/ensemble/_hist_gradient_boosting'
    files += [str(p) for p in hist.glob('*.py')]
    files += [str(p) for p in hist.glob('*.pyd')]
    files += [str(p) for p in (runtime/'sklearn/_loss').glob('*.py')]
    files += [str(p) for p in (runtime/'sklearn/_loss').glob('*.pyd')]
    assert common.PREDICTOR_RECORD_DTYPE.names is not None
    return {'version': sklearn.__version__, 'class': 'sklearn.ensemble.HistGradientBoostingRegressor',
            'runtime': str(runtime), 'node_dtype': [list(field) for field in common.PREDICTOR_RECORD_DTYPE.descr],
            'files': {str(p): sha256(p) for p in sorted(set(files))}}


def row_weights(frame):
    """Equal gene -> equal candidate context -> equal candidate; mean one."""
    assert len(frame) and frame.intervention_id.is_unique
    assert frame.groupby('parent_context_id').biological_component.nunique().eq(1).all()
    counts = frame.groupby('parent_context_id').size()
    per_gene = frame.groupby('biological_component').parent_context_id.nunique()
    weights = 1. / (frame.biological_component.map(per_gene).to_numpy(float) *
                    frame.parent_context_id.map(counts).to_numpy(float))
    weights *= len(frame) / weights.sum()
    assert np.isfinite(weights).all() and (weights > 0).all()
    np.testing.assert_allclose(weights.mean(), 1., atol=1e-12)
    return weights


def make_estimator(config):
    from sklearn.ensemble import HistGradientBoostingRegressor
    assert config in CONFIGS
    return HistGradientBoostingRegressor(**FIXED, max_leaf_nodes=config['max_leaf_nodes'])


def export_model(estimator, width):
    assert estimator.n_trees_per_iteration_ == 1 and estimator.n_iter_ == FIXED['max_iter']
    assert estimator._baseline_prediction.shape == (1, 1)
    trees = []
    for iteration in estimator._predictors:
        assert len(iteration) == 1
        tree = iteration[0]
        assert not tree.nodes['is_categorical'].any()
        trees.append({field: tree.nodes[field].tolist() for field in FIELDS})
    model = {'kind': 'numeric_hgb_json_v1', 'width': width,
             'baseline': float(estimator._baseline_prediction[0, 0]),
             'trees': trees, 'sklearn_version': '1.5.2', 'iterations': len(trees)}
    validate_model(model)
    return model


def validate_model(model):
    assert model['kind'] == 'numeric_hgb_json_v1' and model['sklearn_version'] == '1.5.2'
    assert model['width'] > 0 and np.isfinite(model['baseline'])
    assert model['iterations'] == len(model['trees']) and model['iterations'] > 0
    for tree in model['trees']:
        assert set(tree) == set(FIELDS)
        n = len(tree['value']); assert n and all(len(tree[field]) == n for field in FIELDS)
        assert np.isfinite(tree['value']).all() and np.isfinite(tree['num_threshold']).all()
        for field in ('feature_idx','missing_go_to_left','left','right','is_leaf'):
            assert all(isinstance(value,int) for value in tree[field]), field
        reached = set(); pending = [0]
        while pending:
            node = pending.pop(); assert node not in reached and 0 <= node < n
            reached.add(node)
            assert tree['is_leaf'][node] in (0, 1) and tree['missing_go_to_left'][node] in (0, 1)
            if not tree['is_leaf'][node]:
                assert 0 <= tree['feature_idx'][node] < model['width']
                pending += [int(tree['left'][node]), int(tree['right'][node])]
        assert len(reached) == n, 'All numeric tree nodes must be reachable exactly once'


def predict_model(model, matrix):
    """Pinned native numeric TreePredictor, reconstructed from JSON only."""
    from sklearn.ensemble._hist_gradient_boosting.predictor import TreePredictor
    from sklearn.ensemble._hist_gradient_boosting.common import PREDICTOR_RECORD_DTYPE
    validate_model(model)
    x = np.ascontiguousarray(matrix, dtype=np.float64)
    assert x.ndim == 2 and x.shape[1] == model['width'] and np.isfinite(x).all()
    result = np.full(len(x), model['baseline'], dtype=float)
    known = np.zeros((0, 8), dtype=np.uint32); mapping = np.zeros(x.shape[1], dtype=np.uint32)
    for tree in model['trees']:
        nodes = np.zeros(len(tree['value']), dtype=PREDICTOR_RECORD_DTYPE)
        for field in FIELDS: nodes[field] = tree[field]
        predictor = TreePredictor(nodes, known, known)
        result += predictor.predict(x, known, mapping, n_threads=1)
    assert np.isfinite(result).all()
    return result


def independent_predict(model, matrix):
    """Independent vectorized raw-threshold traversal; no sklearn prediction."""
    validate_model(model)
    x = np.asarray(matrix, dtype=np.float64)
    assert x.ndim == 2 and x.shape[1] == model['width'] and np.isfinite(x).all()
    result = np.full(len(x), model['baseline'], dtype=float)
    for tree in model['trees']:
        leaf = np.asarray(tree['is_leaf'], dtype=bool)
        feature = np.asarray(tree['feature_idx'], dtype=int)
        threshold = np.asarray(tree['num_threshold'], dtype=float)
        left, right = np.asarray(tree['left'], dtype=int), np.asarray(tree['right'], dtype=int)
        node = np.zeros(len(x), dtype=int)
        for _ in range(len(leaf)):
            active = np.flatnonzero(~leaf[node])
            if not len(active): break
            current = node[active]
            go_left = x[active, feature[current]] <= threshold[current]
            node[active] = np.where(go_left, left[current], right[current])
        assert leaf[node].all()
        result += np.asarray(tree['value'], dtype=float)[node]
    return result


def fit_model(frame, matrix, config):
    from .common import freeze_check
    freeze_check()
    for variable in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
        assert os.environ.get(variable) == '1', variable
    assert frame.cell_type.nunique() == 1 and config in CONFIGS
    assert runtime_binding() == readj(OUT/'runtime_binding.json')
    x = np.ascontiguousarray(matrix, dtype=np.float64)
    y = frame.measured_delta.to_numpy(float)
    assert len(x) == len(y) and np.isfinite(x).all() and np.isfinite(y).all()
    weights = row_weights(frame)
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=1):
        estimator = make_estimator(config)
        estimator.fit(x, y, sample_weight=weights)
        model = export_model(estimator, x.shape[1])
        original = estimator.predict(x)
    replay = predict_model(model, x)
    error = float(np.max(np.abs(original - replay)))
    assert error < 1e-9, 'Numeric JSON export must reproduce native fitted scores'
    model.update({'native_export_max_error': error,
                  'training_weights_sha256': hashlib.sha256(weights.tobytes()).hexdigest(),
                  'training_weights_mean': float(weights.mean())})
    return model


def module(track):
    assert track in TRACKS
    if track.startswith('ridge/'):
        from . import ridge
        return ridge
    return SimpleNamespace(CONFIGS=CONFIGS, fit_model=fit_model, predict_model=predict_model,
                           independent_predict=independent_predict)
