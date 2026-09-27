"""No-fit verification of new synthesis, old freezes and bounded prototype."""
from .common import *
import sys,subprocess,unittest,io,importlib
from .controls import verify_freeze

def run():
    verify_freeze()
    checked={}
    for name in ('delivery_receipt.json','srle_prediction_delivery_receipt.json'):
        receipt=readj(OLDART/name)
        for path,meta in receipt['manifest'].items():assert sha256(ROOT/path)==meta['sha256'],path
        assert sha256(ROOT/receipt['archive'])==receipt['sha256']
        checked[name]=len(receipt['manifest'])
    from src.research_20260921.srle_clean_verification_20260925 import preservation
    protected=preservation()
    # Compare every old result-commit member, beyond relying only on earlier receipt.
    for commit in ('0023b01','e5b9288'):
        paths=subprocess.check_output(['git','diff-tree','--no-commit-id','--name-only','-r',commit],cwd=ROOT,text=True).splitlines()
        for path in paths:assert (ROOT/path).read_bytes()==subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT),path
    candidate=pd.read_csv(ART/'all_candidate_recommendations.csv',dtype={'group':str},float_precision='round_trip')
    assert len(candidate)==83712
    original=pd.read_csv(OLDART/'srle_candidate_selection.csv',dtype={'group':str},float_precision='round_trip')
    keys=['evaluation_split','model_name','parent','candidate','direction']
    a=candidate[candidate.model_name.ne('uniform')].set_index(keys).sort_index();b=original.set_index(keys).sort_index()
    assert a.index.equals(b.index) and len(a)==73248
    difference=0.
    for field in ('predicted_delta','measured_delta','rep1_delta','rep2_delta','predicted_rank','measured_rank'):
        difference=max(difference,float(np.max(np.abs(a[field]-b[field]))))
    assert difference<1e-12 and (a.selected==b.selected).all()
    strict=candidate[candidate.evaluation_split.eq('purged_composition_holdout')]
    d=pd.read_csv(ART/'recommendation_decisions.csv',dtype={'group':str},float_precision='round_trip').set_index(['model','parent','direction'])
    errors=[];n=0
    for key,g in strict.groupby(['model_name','parent','direction']):
        old=d.loc[key];direction=key[2];y=direction*g.measured_delta.to_numpy();prob=g.selection_probability.to_numpy()
        assert abs(prob.sum()-1)<1e-12
        if key[0]!='uniform':
            ranked=g.sort_values(['predicted_rank']);assert ranked.iloc[0].candidate==old.selected
            assert (np.diff(direction*ranked.predicted_delta.to_numpy())<=1e-12).all()
        values={'published_regret':np.sum(prob*(y.max()-y)/np.ptp(y)),
            'published_correct_direction':np.sum(prob*(y>TOL)),'published_wrong_direction':np.sum(prob*(y<-TOL)),
            'published_best_choice':np.sum(prob*(y==y.max())),
            'wrong_both':np.sum(prob*((direction*g.rep1_delta.to_numpy()<-TOL)&(direction*g.rep2_delta.to_numpy()<-TOL)))}
        errors.extend(abs(value-old[field]) for field,value in values.items());n+=1
        if key[0]!='uniform':assert abs(old.wrong_both_correct_alternative+old.wrong_both_ambiguous_alternative+old.wrong_both_unavoidable-old.wrong_both)<1e-12
    assert n==9472 and max(errors)<1e-12
    # Recheck aggregation/conditional coverage; do not revise any rule.
    summary=pd.read_csv(OUT/'recommendation_summary.csv',float_precision='round_trip').set_index('model')
    df=d.reset_index();metricerr=[]
    for model,g in df.groupby('model'):
        for field in ('published_regret','wrong_both','published_best_choice','beats_uniform'):
            metricerr.append(abs(g.groupby('group')[field].mean().mean()-summary.loc[model,field]))
    assert max(metricerr)<1e-12
    cov=pd.read_csv(OUT/'confidence_coverage.csv',float_precision='round_trip')
    assert len(cov)==50
    for row in cov.itertuples():
        g=df[df.model.eq(row.model)].sort_values([row.signal,'parent','direction'],ascending=[False,True,True]).iloc[:int(np.ceil(1184*row.requested_coverage))]
        assert len(g)==row.rows and g.group.nunique()==row.statistical_groups
        for field in ('published_regret','wrong_both'):assert abs(g.groupby('group')[field].mean().mean()-getattr(row,field))<1e-12
    controls=pd.read_csv(ART/'control_predictions.csv',float_precision='round_trip');assert len(controls.columns[6:])==34 and len(controls)==1744
    for row in pd.read_csv(OUT/'control_metrics.csv').itertuples():
        y=controls[row.target+'_delta'].to_numpy();p=controls[row.control].to_numpy()
        assert abs(1-np.sum((p-y)**2)/np.sum(y*y)-row.mse_improvement)<1e-12
    import predict_edit_candidates as interface
    bundle=interface.load_bundle();replayed=0
    for row in df[df.model.isin(['2mer','kmer123'])].itertuples():
        result=interface.predict(row.parent,bundle['parents'][row.parent]['candidates'],'increase' if row.direction==1 else 'decrease',row.model,bundle)
        assert result['candidates'][0]['candidate']==row.selected;replayed+=1
    assert replayed==2368
    old=readj(OUT/'verification_receipt.json') if (OUT/'verification_receipt.json').exists() else None
    if old:
        for path,h in old['synthesis_hashes'].items():assert sha256(ROOT/path)==h,path
        print('PASS: all pinned files, 9,472 decisions, 2,368 prototype choices, 50 confidence rows and 34 controls verified without fits or file writes')
        return
    from . import test_synthesis
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_synthesis))
    assert result.wasSuccessful() and result.testsRun==15
    save(OUT/'prototype_scoped_tests.txt',stream.getvalue().encode())
    import sklearn,scipy
    runtime={'python':sys.version,'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,'sklearn':sklearn.__version__}
    paths=list(Path(__file__).parent.glob('*.py'))+[ROOT/'predict_edit_candidates.py']+list(OUT.glob('*'))+list(ART.glob('*'))+[REPORT/name for name in ('small_edit_final_synthesis.md','srle_synthesis_reproducibility.md','srle_synthesis_figure_guide.md','srle_candidate_prototype.md','srle_synthesis_analysis_protocol.md','srle_boundary_decomposition_addendum.md')]
    paths=[p for p in paths if p.is_file() and p.name not in ('verification_receipt.json','delivery_receipt.json') and p.suffix!='.zip']
    jsave(OUT/'verification_receipt.json',{'status':'PASS','candidate_rows':len(candidate),'strict_candidate_rows':len(strict),'decision_metrics_independently_checked':n,
        'candidate_source_max_error':difference,'decision_metric_max_error':max(errors),'group_mean_max_error':max(metricerr),'prototype_decisions_replayed':replayed,
        'new_scoped_tests':result.testsRun,'original_scoped_tests_in_fresh_replay':82,'unfiltered_pytest_run':False,'controls_retained':34,'seed_retries':0,'confidence_rows_verified':50,
        'historical_bundles_unchanged':checked,'protected_manifests':protected,'runtime':runtime,'new_model_search':False,'scope':'Numerical/software verification; not independent biological confirmation',
        'synthesis_hashes':{p.relative_to(ROOT).as_posix():sha256(p) for p in sorted(set(paths))}})
    print({'status':'PASS','candidate_rows':len(candidate),'decisions_verified':n,'max_error':max(errors),'tests':result.testsRun,'prior_tests':82,'prototype_decisions':replayed})

if __name__=='__main__':run()
