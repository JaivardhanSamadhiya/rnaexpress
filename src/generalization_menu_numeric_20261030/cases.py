"""Adversarial invented numerical checks; no project data or imports at load."""
import itertools
import json
import math
from src.generalization_menu_comparison_core_20261026 import layout
from src.generalization_menu_comparison_core_20261026.tests import fixture
from src.generalization_menu_comparison_core_20261026.tests import dna
from src.generalization_menu_bound_reference_20261026.reference import evaluate
from . import engine


def problem():
    rows = fixture()
    # Unequal menu sizes, truth ties, unequal component/context weights.
    rows = [r for i,r in enumerate(rows) if i % 9 != 2]
    for row in rows:
        if row['parent_context_id'] == 'context02':row['biological_component'] = 'gene01'
    rows = layout.metadata(rows)
    menus = layout.menus(rows, range(len(rows)))
    y, x = [], []
    for i,row in enumerate(rows):
        candidate = int(row['intervention_id'].rsplit('_',1)[1])
        effect = (-1.,1.,1.)[candidate] if i % 2 else (-1.,0.,1.)[candidate]
        y.append(effect)
        x.append((float(candidate), math.sin(i+.3), 2., 1e-12*candidate))
    sampled = {m['context']:tuple(itertools.combinations(m['indices'],2)) for m in menus}
    return rows, x, y, sampled


def large_problem():
    """Invented capped rosters, not a replacement for the original sampler."""
    rows,x,y = [],[],[]
    for study in layout.STUDIES:
        for context in range(2):
            key = study+'|invented_large'+str(context)
            for candidate in range(1,27):
                rows.append(dict(intervention_id=key+'|'+str(candidate),dataset=study,
                    biological_component=key,parent_context_id=key,
                    parent_sequence='AAAAAAAA',mutant_sequence=dna(candidate)))
                x.append((float(candidate),math.sin(candidate+context),2.,candidate*1e-12))
                y.append(float(candidate//4))
    rows = layout.metadata(rows)
    menus = layout.menus(rows,range(len(rows)))
    sampled = {m['context']:tuple(itertools.islice(itertools.combinations(m['indices'],2),256))
               for m in menus}
    return rows,x,y,sampled


def run(np, minimize, expit):
    rows, x, y, sampled = problem()
    p = engine.prepare(np,features=x,effects=y,source_metadata=rows,sampled_pairs=sampled)
    beta = np.array([.12,-.23,0.,0.], dtype=np.float64)
    checks = []
    for arm in layout.ARMS:
        for _,penalty in layout.PENALTIES:
            ref = evaluate(beta=beta,features=x,effects=y,source_metadata=rows,
                           sampled_pairs=sampled,arm=arm,penalty=penalty)
            value, gradient = engine.objective(np,expit,p,beta,arm=arm,penalty=penalty)
            difference = max(abs(value-ref['objective']),
                             max(abs(a-b) for a,b in zip(gradient,ref['gradient'])))
            assert difference < 1e-10, (arm, 'scalar parity', difference)
            for key in ('mean','scale','pair_rms'):
                actual = p.rms if key == 'pair_rms' else getattr(p,key)
                assert max(abs(a-b) for a,b in zip(actual,ref['source_scaling'][key])) < 1e-10
            finite_difference = []
            for j in (0,1):
                high, low = beta.copy(), beta.copy()
                high[j] += 1e-6; low[j] -= 1e-6
                h = engine.objective(np,expit,p,high,arm=arm,penalty=penalty)[0]
                l = engine.objective(np,expit,p,low,arm=arm,penalty=penalty)[0]
                finite_difference.append(abs((h-l)/2e-6-gradient[j]))
            assert max(finite_difference) < 2e-7
            calls = []
            def checked_minimize(fun, initial, **kwargs):
                assert kwargs == dict(jac=True,method='L-BFGS-B',options=engine.OPTIONS)
                assert initial.shape == (4,) and np.all(initial == 0.)
                calls.append(1)
                return minimize(fun,initial,**kwargs)
            model = engine.fit(np,checked_minimize,expit,p,arm=arm,penalty=penalty)
            assert len(calls) == 1
            fitted = evaluate(beta=model['beta'],features=x,effects=y,source_metadata=rows,
                              sampled_pairs=sampled,arm=arm,penalty=penalty)
            assert abs(fitted['objective']-model['objective']) < 1e-10
            assert max(abs(v) for v in fitted['gradient']) < 1e-5
            assert model['beta'][2:] == [0.,0.]
            prediction = engine.scores(np,model,x)
            replay = engine.scores(np,json.loads(json.dumps(model,allow_nan=False)),x)
            assert np.array_equal(prediction,replay)
            changed = np.array(x); changed[:,2:] += 1e6
            assert np.array_equal(prediction,engine.scores(np,model,changed))
            canonical = []
            for row in x:
                canonical.append(math.fsum((v-m)/s*b if a else 0.
                    for v,m,s,b,a in zip(row,model['mean'],model['scale'],model['beta'],model['active'])))
            score_difference = max(abs(a-b) for a,b in zip(prediction,canonical))
            assert score_difference < 1e-10
            checks.append(dict(arm=arm,penalty=penalty,scalar_max_difference=difference,
                finite_difference_max=max(finite_difference),score_reference_max=score_difference,
                fitted_scalar_gradient_max=max(abs(v) for v in fitted['gradient'])))
    # Caller mutation cannot alter the prepared training matrix.
    original = np.array(x); owned = engine.prepare(np,features=original,effects=y,
        source_metadata=rows,sampled_pairs=sampled)
    before = owned.z.copy(); original[:] = 123.
    assert np.array_equal(before,owned.z) and not owned.z.flags.writeable
    for flag,kwargs in [('omitted_context',dict(sampled_pairs={k:v for k,v in sampled.items()
                                if k != next(iter(sampled))})),
                        ('injected_pair_weights',dict(pair_rows=[(0,1,1.,1.)]))]:
        arguments = dict(features=x,effects=y,source_metadata=rows,sampled_pairs=sampled)
        arguments.update(kwargs)
        try:engine.prepare(np,**arguments)
        except (ValueError,TypeError):pass
        else:raise AssertionError('Invalid preparation accepted: '+flag)
    # Two-candidate identity, including unequal hierarchy, and extreme margins.
    binary_rows = tuple(r for r in rows if r['intervention_id'].endswith(('_0','_1')))
    by_id = {r['intervention_id']:i for i,r in enumerate(rows)}
    indices = [by_id[r['intervention_id']] for r in binary_rows]
    binary_menus = layout.menus(binary_rows,range(len(binary_rows)))
    binary = engine.prepare(np,features=[x[i] for i in indices],effects=[y[i] for i in indices],
        source_metadata=binary_rows,sampled_pairs={m['context']:tuple(itertools.combinations(m['indices'],2))
                                                   for m in binary_menus})
    for vector in (beta,np.array([1000.,-500.,0.,0.])):
        a,ga = engine.objective(np,expit,binary,vector,arm='margin_pair',penalty=.05)
        b,gb = engine.objective(np,expit,binary,vector,arm='menu_cost',penalty=.05)
        assert abs(a-b) < 1e-9 and np.max(np.abs(ga-gb)) < 1e-9
    # Multiple capped menus and >256 valid pairs exercise all RMS scratch blocks.
    lr,lx,ly,ls = large_problem()
    large = engine.prepare(np,features=lx,effects=ly,source_metadata=lr,sampled_pairs=ls)
    assert len(large.weight) > 256 and all(len(v) == 256 for v in ls.values())
    large_checks = []
    for arm in layout.ARMS:
        ref = evaluate(beta=beta,features=lx,effects=ly,source_metadata=lr,
                       sampled_pairs=ls,arm=arm,penalty=.05)
        value,gradient = engine.objective(np,expit,large,beta,arm=arm,penalty=.05)
        difference = max(abs(value-ref['objective']),max(abs(a-b) for a,b in zip(gradient,ref['gradient'])))
        assert difference < 1e-10
        for key in ('mean','scale','pair_rms'):
            actual = large.rms if key == 'pair_rms' else getattr(large,key)
            assert max(abs(a-b) for a,b in zip(actual,ref['source_scaling'][key])) < 1e-10
        assert tuple(bool(v) for v in large.active) == ref['source_scaling']['active']
        large_checks.append(dict(arm=arm,scalar_max_difference=difference))
    corrupted = dict(model,active=[True,True,'False',False])
    try:engine.scores(np,corrupted,x)
    except ValueError:pass
    else:raise AssertionError('String scoring support accepted')
    return dict(status='PASS_INVENTED_THREE_ARM_NUMERICAL_REFERENCE',checks=checks,
                capped_roster_checks=large_checks,capped_menu_count=len(ls),
                capped_valid_pairs=len(large.weight),
                invented_optimizer_units=len(checks),biological_model_fits=0,
                original_numpy_sampler_equivalence_certified=False,
                biological_inputs_admitted=False,full_campaign_ready=False)
