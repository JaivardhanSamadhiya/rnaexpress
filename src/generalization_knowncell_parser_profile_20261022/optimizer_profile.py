"""Invented-only checks of the actual separately frozen deferred solver."""
import json
import math
from .common import OPTIONS


def run(np, minimize, expit):
    from src.generalization_knowncell_joint_numeric_20261022 import numeric
    from src.generalization_knowncell_joint_numeric_20261022.spec import CONFIGS
    from src.generalization_knowncell_joint_implementation_20261022 import kernels
    rng = np.random.RandomState(20261022)
    x = rng.normal(0., .05, size=(128, 102))
    x[:,99] *= 1e-12; x[:,100] = 9.; x[:,101] = 0.
    left = np.arange(64, dtype=np.int64); right = left+64
    cells = ['CAD']*32 + ['Neuro-2a']*32
    pair_blocks = ['invented_CAD_A']*16 + ['invented_CAD_B']*16 + ['invented_N2A_A']*16 + ['invented_N2A_B']*16
    row_cells = cells+cells
    labels = np.where(np.arange(64)%3 == 0, -1., 1.)
    one = np.arange(1.,33.); one = .5 * one / one.sum()
    weights = np.concatenate((one, one[::-1]))
    prepared = numeric.prepare_training(np, x, left, right, labels, weights, cells)
    differences = (x[left]-x[right]).tolist()
    scaling = kernels.common_scale(differences, weights.tolist())
    assert prepared['scaling']['active'] == scaling['active']
    assert max(abs(a-b) for a,b in zip(prepared['scaling']['scale'], scaling['scale'])) < 1e-12
    assert prepared['scaling']['active'][-3:] == [False,False,False]
    z, y, w, signs = [prepared[key] for key in ('z','labels','weights','signs')]
    zl, yl, wl = z.tolist(), y.tolist(), w.tolist()
    reference = {'pooled': kernels.pooled_value_gradient,
                 'independent': kernels.independent_value_gradient,
                 'joint_shrink10': kernels.joint_value_gradient}
    calls = []; checks = []

    def checked_minimize(fun, initial, **kwargs):
        assert kwargs == {'jac': True, 'method': 'L-BFGS-B', 'options': OPTIONS}
        assert initial.shape in ((102,), (204,)) and np.all(initial == 0.)
        loss, gradient = fun(initial)
        assert abs(loss-math.log(2.)) < 1e-12, 'Initial conditional weights must sum1'
        assert np.isfinite(gradient).all()
        calls.append({'width': len(initial), 'zero_start_loss': loss,
                      'method': kwargs['method'], 'options': dict(kwargs['options'])})
        return minimize(fun, initial, **kwargs)

    for arm in ('pooled','independent','joint_shrink10'):
        width = 102 if arm == 'pooled' else 204
        theta = np.linspace(-.03,.03,width, dtype=np.float64)
        for config in CONFIGS:
            penalty = config['penalty']
            actual_value, actual_gradient = numeric.objective_value_gradient(np,expit,arm,theta,z,y,w,signs,penalty)
            expected_value, expected_gradient = reference[arm](theta.tolist(),zl,yl,wl,cells,penalty)
            value_difference = abs(actual_value-expected_value)
            gradient_difference = max(abs(a-b) for a,b in zip(actual_gradient.tolist(),expected_gradient))
            assert value_difference < 1e-11 and gradient_difference < 1e-11
            fd = []
            indices = [0,50,99,100,101] + ([102,152,201,202,203] if width == 204 else [])
            for index in indices:
                plus=theta.copy(); minus=theta.copy(); plus[index]+=1e-6; minus[index]-=1e-6
                high=numeric.objective_value_gradient(np,expit,arm,plus,z,y,w,signs,penalty)[0]
                low=numeric.objective_value_gradient(np,expit,arm,minus,z,y,w,signs,penalty)[0]
                fd.append(abs((high-low)/(2e-6)-actual_gradient[index]))
            assert max(fd) < 2e-7
            model=numeric.fit_prepared(np,checked_minimize,expit,prepared,arm,config)
            if arm == 'independent':
                fitted=model['heads']['CAD']+model['heads']['Neuro-2a']
            else: fitted=model['beta']+model.get('delta',[])
            exact_value, exact_gradient=reference[arm](fitted,zl,yl,wl,cells,penalty)
            assert abs(exact_value-model['objective']) < 1e-10
            assert max(abs(value) for value in exact_gradient) < 1e-5
            prediction=numeric.canonical_scores(np,model,x,row_cells)
            scalar=kernels.reference_scores(arm,x.tolist(),row_cells,model)
            prediction_difference=max(abs(a-b) for a,b in zip(prediction.tolist(),scalar))
            assert prediction_difference < 1e-10
            saved=json.loads(json.dumps(model, allow_nan=False))
            replay=numeric.canonical_scores(np,saved,x,row_cells)
            assert np.array_equal(prediction,replay)
            changed=x.copy(); changed[:,99:102]+=1e6
            assert np.array_equal(prediction,numeric.canonical_scores(np,model,changed,row_cells))
            checks.append({'arm':arm,'config':config['id'],'objective_difference':value_difference,
                'gradient_max_abs_difference':gradient_difference,'finite_difference_max_abs_difference':max(fd),
                'fitted_objective_difference':abs(exact_value-model['objective']),
                'fitted_scalar_gradient_max_abs':max(abs(value) for value in exact_gradient),
                'canonical_scalar_score_max_abs_difference':prediction_difference,
                'optimizer_units':model['optimizer_units']})
    assert len(calls)==12 and sum(item['width']==204 for item in calls)==3
    return {'status':'PASS_INVENTED_SCIPY_SOLVER_REFERENCE_AND_SCORER',
            'seed':20261022,'invented_rows':128,'invented_pairs':64,'feature_width':102,
            'invented_balanced_cell_groups':2,
            'invented_pair_blocks':{block:pair_blocks.count(block) for block in sorted(set(pair_blocks))},
            'same_prepared_object_all_arms':True,'scipy_optimizer_units':len(calls),
            'checks':checks,'optimizer_calls':calls,
            'biological_model_fits':0,'project_datasets_loaded':False,
            'scope':'Compatibility on a small invented problem; not actual biological runtime, resource or validation certification.'}
