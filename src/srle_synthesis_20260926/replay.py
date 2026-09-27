"""Fresh fixed fits and independent metric replay in a new output namespace."""
from .common import *
import subprocess
import unittest
import importlib
import io
from src.srle_prediction_20260926.fit import design,fit_fold
from src.srle_prediction_20260926.core import SCHEMES,MODELS,training_mask


def run():
    commits={}
    for commit in ('0023b01','e5b9288'):
        paths=subprocess.check_output(['git','diff-tree','--no-commit-id','--name-only','-r',commit],cwd=ROOT,text=True).splitlines()
        for name in paths:
            archived=subprocess.check_output(['git','show',commit+':'+name],cwd=ROOT)
            assert (ROOT/name).read_bytes()==archived,(commit,name)
        commits[commit]={'working_tree_files_matching':len(paths),'paths':paths}
    receipt=readj(OLDART/'srle_prediction_delivery_receipt.json')
    for path,meta in receipt['manifest'].items():assert sha256(ROOT/path)==meta['sha256'],path
    assert sha256(ROOT/receipt['archive'])==receipt['sha256']
    source=pd.read_csv(OLD/'sequence_inventory.csv',dtype={'group':str},float_precision='round_trip')
    expected=pd.read_csv(OLDART/'srle_heldout_predictions.csv',dtype={'group':str,'held_group':str},float_precision='round_trip')
    xs=design(source.kmer);parts=[];max_error=0.;partitions=0
    for scheme in SCHEMES:
        for key in ([None] if scheme=='sequence_holdout' else sorted(source.loc[source.scored,'group'].unique())):
            train=training_mask(source,scheme,key)
            test=source.scored.to_numpy() & (True if key is None else source.group.eq(key).to_numpy())
            prediction,_=fit_fold(source,xs,train);partitions+=1
            for model in MODELS:
                old=expected[(expected.scheme==scheme)&(expected.held_group==(key or 'original_hash'))&(expected.model==model)].set_index('kmer')
                values=prediction[model][test]
                max_error=max(max_error,float(np.max(np.abs(values-old.loc[source.loc[test,'kmer'],'predicted_score'].to_numpy()))))
                parts.append(pd.DataFrame({'scheme':scheme,'held_group':key or 'original_hash','model':model,
                    'kmer':source.loc[test,'kmer'].to_numpy(),'predicted_score':values}))
        print('Fresh fits complete:',scheme,flush=True)
    reproduced=pd.concat(parts,ignore_index=True);assert len(reproduced)==17955 and max_error<1e-12
    csvsave(OUT/'fresh_fit_predictions.csv',reproduced)
    # Independently reconstruct the strict-purge difference and its original RNG bootstrap.
    oldeffect=pd.read_csv(OLD/'edit_effect_predictions.csv',dtype={'group':str},float_precision='round_trip')
    g=oldeffect[(oldeffect.scheme=='purged_composition_holdout')&(oldeffect.model=='2mer')].copy()
    g['sse']=(g.published_delta-g.predicted_delta)**2;g['base_sse']=g.published_delta**2
    totals=g.groupby('group')[['sse','base_sse']].sum();ix=draws(len(totals))
    point=1-totals.sse.sum()/totals.base_sse.sum()
    ci=np.quantile(1-totals.sse.to_numpy()[ix].sum(1)/totals.base_sse.to_numpy()[ix].sum(1),[.025,.975])
    comp=pd.read_csv(OLD/'prediction_comparisons.csv',float_precision='round_trip')
    row=comp[(comp.kind=='edit_delta')&(comp.scheme=='purged_composition_holdout')&(comp.target=='published')&(comp.model=='2mer')&(comp.comparator=='composition')].iloc[0]
    assert np.max(np.abs(np.array([point,*ci])-row[['relative_mse_reduction','ci_low','ci_high']].to_numpy(float)))<1e-12
    choices=pd.read_csv(OLD/'decision_rows.csv',dtype={'group':str},float_precision='round_trip')
    check=choices[choices.scheme.eq('purged_composition_holdout')&choices.model.isin(['kmer123','uniform'])]
    means=check.groupby(['model','group'])[['published_regret','wrong_both']].mean().groupby('model').mean()
    dm=pd.read_csv(OLD/'decision_metrics.csv',float_precision='round_trip')
    for model in means.index:
        saved=dm[(dm.scheme=='purged_composition_holdout')&(dm.direction==0)&(dm.model==model)].iloc[0]
        for metric in means.columns:assert abs(means.loc[model,metric]-saved[metric])<1e-12
    y=source.loc[source.scored,'nrs'];historical=1-np.sum((y-source.loc[source.scored,'position_pair'])**2)/np.sum((y-source.loc[source.scored,'composition'])**2)
    assert abs(historical-.270428705752478)<1e-12
    pair=comp[(comp.kind=='edit_delta')&(comp.scheme=='purged_composition_holdout')&(comp.target=='published')&(comp.model=='position_pair')&(comp.comparator=='composition')].iloc[0]
    assert pair.relative_mse_reduction<0 and pair.ci_high<0
    suite=unittest.TestSuite()
    for package in ('research_20260921','small_edit_20260925','srle_prediction_20260926'):
        for path in sorted((ROOT/'src'/package).glob('test_*.py')):
            suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(importlib.import_module('src.'+package+'.'+path.stem)))
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=1).run(suite)
    assert result.wasSuccessful() and result.testsRun==82
    save(OUT/'replay_scoped_tests.txt',stream.getvalue().encode())
    jsave(OUT/'clean_replay_receipt.json',{'status':'PASS','commits':commits,'prior_bundle_files_checked':len(receipt['manifest']),
        'fresh_training_partitions':partitions,'fresh_ridge_fits':partitions*6,'predictions':len(reproduced),'max_fresh_prediction_error':max_error,
        'historical_score_error_reduction':historical,'strict_2mer_effect_mse_reduction':point,'strict_2mer_ci':ci,
        'strict_pair_mse_reduction':pair.relative_mse_reduction,'strict_kmer123_regret':means.loc['kmer123','published_regret'],
        'uniform_regret':means.loc['uniform','published_regret'],'strict_kmer123_wrong_both':means.loc['kmer123','wrong_both'],
        'tests':result.testsRun,'new_models_searched':0,'scope':'Fresh fixed reconstruction only; separate new outputs'})
    print({'status':'PASS','rows':len(reproduced),'fresh_prediction_error':max_error,'tests':result.testsRun,'strict_2mer_gain':point,'ci':ci.tolist()})


if __name__=='__main__':run()
