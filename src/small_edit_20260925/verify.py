"""Replay frozen fits without training; validate grouping and preserved history."""
from .common import *
from .features import features
from scipy.special import expit
import importlib
import io
import unittest


def run():
    freeze=readj(OUT/'prediction_freeze.json')
    for p,h in freeze['files'].items():
        assert sha256(ROOT/p)==h, p
    for p,h in readj(OUT/'inventory_receipt.json')['inputs'].items():
        assert sha256(ROOT/p)==h, p
    for p,h in readj(OUT/'prediction_receipt.json')['outputs'].items():
        assert sha256(OUT/p)==h, p
    data=pd.read_csv(OUT/'small_edit_predictions.csv',float_precision='round_trip')
    for column in ('gene_name','parent_id','parent_sequence','mutant_sequence'):
        assert data.groupby(column).biological_fold.nunique().max()==1, column
    alleles=pd.concat([data[['parent_sequence','biological_fold']].rename(columns={'parent_sequence':'sequence'}),
                       data[['mutant_sequence','biological_fold']].rename(columns={'mutant_sequence':'sequence'})])
    assert alleles.groupby('sequence').biological_fold.nunique().max()==1
    saved=readj(OUT/'fitted_parameters.json')
    scores=pd.read_csv(OUT/'inner_model_selection.csv',float_precision='round_trip')
    errors=[]
    for context,part in data.groupby('cell_type'):
        xs=features(part)
        for coef in [v for v in saved if v['context']==context]:
            name=coef['model']; fold=coef['fold']; mask=part.biological_fold.eq(fold).to_numpy()
            x=xs[name][mask]
            pred=((x-np.array(coef['ridge_mean']))/np.array(coef['ridge_scale']))@np.array(coef['ridge_coef'])+coef['ridge_intercept']
            prob=expit((((x-np.array(coef['logistic_mean']))/np.array(coef['logistic_scale']))@np.array(coef['logistic_coef']).T+np.array(coef['logistic_intercept'])).ravel())
            errors.extend([float(np.max(np.abs(pred-part.loc[mask,'pred_'+name]))),float(np.max(np.abs(prob-part.loc[mask,'prob_'+name])))])
            s=scores[(scores.context==context)&(scores.outer_fold==fold)&(scores.model==name)]
            assert int(s.sort_values(['inner_gene_mse','alpha']).iloc[0].alpha)==coef['alpha']
        for fold,g in part.groupby('biological_fold'):
            s=scores[(scores.context==context)&(scores.outer_fold==fold)&scores.model.isin(freeze['primary_families'])]
            chosen=s.sort_values(['inner_gene_mse','model','alpha']).iloc[0]
            assert (g.selected_family==chosen.model).all()
            assert (g.selected_alpha==chosen.alpha).all()
            assert np.array_equal(g.pred_primary,g['pred_'+chosen.model])
            assert np.array_equal(g.prob_primary,g['prob_'+chosen.model])
    assert max(errors)<1e-12, max(errors)
    ranks=pd.read_csv(OUT/'small_edit_candidate_selection.csv',float_precision='round_trip')
    decisions=pd.read_csv(OUT/'small_edit_decisions.csv.gz',float_precision='round_trip')
    primary=decisions[decisions.model.eq('primary')].set_index(['context','edit_size_band','parent','direction'])
    regret_errors=[]
    for key,g in ranks.groupby(['context','edit_size_band','parent','direction']):
        chosen=g[g.selected.eq(True)]
        assert len(chosen)==1
        row=chosen.iloc[0]; target=primary.loc[key]; sign=key[-1]
        assert row.edit==target.selected_id
        order=g.sort_values(['predicted_rank'])
        assert np.all(np.diff(sign*order.predicted_effect.to_numpy())<=1e-14)
        measured=sign*g.measured_effect.to_numpy()
        regret=(measured.max()-sign*row.measured_effect)/np.ptp(measured)
        regret_errors.append(abs(regret-target.regret))
    assert max(regret_errors)<1e-12
    from src.research_20260921.srle_clean_verification_20260925 import preservation
    preserved=preservation()
    suite=unittest.TestSuite(); names=[]
    for package in ('research_20260921','small_edit_20260925'):
        for path in sorted((ROOT/'src'/package).glob('test_*.py')):
            name='src.'+package+'.'+path.stem; names.append(name)
            suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(importlib.import_module(name)))
    log=io.StringIO(); result=unittest.TextTestRunner(stream=log,verbosity=1).run(suite)
    save(OUT/'scoped_tests.txt',log.getvalue().encode())
    assert result.wasSuccessful(),log.getvalue()
    jsave('verification_receipt.json',{'status':'PASS','rows':len(data),'coefficient_records':len(saved),
        'prediction_replay_max_error':max(errors),'decision_replay_max_error':max(regret_errors),
        'parent_gene_and_all_allele_overlap':False,'models_fit':0,'new_outcomes':0,
        'tests':result.testsRun,'test_modules':names,'preservation':preserved,
        'prediction_freeze_sha256':sha256(OUT/'prediction_freeze.json'),
        'scope':'Saved-coefficient replay and scoped tests; not independent biological confirmation'})
    print(json.dumps({'status':'PASS','tests':result.testsRun,'prediction_error':max(errors),'decision_error':max(regret_errors),'preservation_manifests':len(preserved)}))


if __name__=='__main__': run()
