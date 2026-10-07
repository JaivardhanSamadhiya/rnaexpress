"""Postfit arithmetic and preservation audit; no model selection or new fits."""
from .common import *
from .engine import module,features
from src.cross_assay_20260927.models import purge

def preservation():
    from src.generalization_20261007.verify import preservation as prior_preservation
    unchanged, old_members = prior_preservation()
    freeze_check()
    delivery_path = ROOT/'artifacts/generalization_20261007/delivery_receipt.json'
    initial = readj(OUT/'initial_state.json')
    assert sha256(delivery_path) == initial['previous_delivery_sha256']
    delivery = readj(delivery_path)
    assert sha256(ROOT/delivery['archive']) == delivery['sha256']
    for path, entry in delivery['manifest'].items():
        assert sha256(ROOT/path) == entry['sha256'], path
    return unchanged, old_members + [len(delivery['manifest'])]

def run():
    unchanged,old_members=preservation()
    frame,_=load();errors=[];decision_count=0;model_count=0
    for track in TRACKS:
        x=features(track);mod=module(track)
        pred=pd.read_csv(OUT/track/'predictions.csv.gz',float_precision='round_trip')
        d=pd.read_csv(OUT/track/'decisions.csv',float_precision='round_trip')
        inner=pd.read_csv(OUT/track/'inner_selection.csv',float_precision='round_trip')
        for fold in readj(OUT/track/'folds.json'):
            held=fold['held'];test=frame.dataset.eq(held).to_numpy();train=purge(frame,~test,test)
            target=frame.loc[test].reset_index(drop=True)
            expected=hashlib.sha256('|'.join(frame.loc[train].intervention_id).encode()).hexdigest()
            assert expected==fold['training_ids_sha256']
            assert hashlib.sha256('|'.join(target.intervention_id).encode()).hexdigest()==fold['test_ids_sha256']
            assert not set(fold['training_components'])&set(target.biological_component)
            selected=fold['selected_configuration']
            values=inner[inner.outer_held.eq(held)].groupby('configuration').regret.mean()
            minimum=float(values.min())
            choice=next(c for c in mod.CONFIGS if float(values[c['id']])<=minimum+1e-12)
            assert choice==selected
            m=readj(OUT/track/'fits'/(held+'__outer_'+selected['id']+'.json'))
            assert m['_training_ids_sha256']==expected and held not in m['_training_studies']
            actual=mod.predict_model(m,x[test])
            p=pred[pred.dataset.eq(held)].set_index('intervention_id').loc[target.intervention_id]
            error=float(np.max(abs(actual-p.score.to_numpy())));assert error<1e-9;errors.append(error)
            joined=p.reset_index().merge(target[['intervention_id','parent_context_id','biological_component','measured_delta']],on='intervention_id',validate='one_to_one')
            for direction in (-1,1):
                selected_rows=joined.assign(utility=direction*joined.score).sort_values(['parent_context_id','utility','intervention_id'],ascending=[True,False,True]).drop_duplicates('parent_context_id').set_index('parent_context_id')
                dd=d[d.dataset.eq(held)&d.direction.eq(direction)].set_index('parent_context_id').loc[selected_rows.index]
                assert np.array_equal(dd.selected_id.to_numpy(),selected_rows.intervention_id.to_numpy())
                bounds=joined.groupby('parent_context_id').measured_delta.agg(['min','max']).loc[selected_rows.index]
                best=bounds['max'].to_numpy() if direction==1 else -bounds['min'].to_numpy()
                effect=direction*selected_rows.measured_delta.to_numpy()
                regret=(best-effect)/(bounds['max']-bounds['min']).to_numpy()
                np.testing.assert_allclose(regret,dd.regret,atol=1e-12,rtol=0)
                assert np.array_equal((effect<-1e-12).astype(float),dd.wrong_direction.to_numpy())
                assert np.array_equal(((effect<-1e-12)&(best>1e-12)).astype(float),dd.avoidable_wrong.to_numpy())
                decision_count+=len(dd)
        np.testing.assert_allclose(d.wrong_direction,d.avoidable_wrong+d.unavoidable_wrong+d.neutral_only_alternative_wrong,atol=1e-12,rtol=0)
        model_count+=len(list((OUT/track/'fits').glob('*.json')))
        print('Verified',track,flush=True)
    # Independent reconstruction of archived H0 scores and extreme choices.
    previous=pd.read_csv(ROOT/'results/probabilistic_ranking_20260928/predictions.csv',float_precision='round_trip')
    previous=previous[previous.model.eq('H0')]
    old_dec=pd.read_csv(ROOT/'results/probabilistic_ranking_20260928/decision_metrics.csv',float_precision='round_trip')
    old_dec=old_dec[old_dec.model.eq('H0')&old_dec.stage.eq('held_assay')]
    baseline=[]
    for held in STUDIES:
        target=frame[frame.dataset.eq(held)].reset_index(drop=True)
        p=previous[previous.dataset.eq(held)].set_index('intervention_id').loc[target.intervention_id]
        dd=decisions(target,p.score.to_numpy(),'H0')
        old=old_dec[old_dec.dataset.eq(held)].set_index(['parent_context_id','direction']).loc[dd.set_index(['parent_context_id','direction']).index]
        assert list(old.selected_id)==list(dd.selected_id)
        np.testing.assert_allclose(old.regret,dd.regret,atol=1e-12,rtol=0)
        baseline.append(dd)
    csvsave(OUT/'baseline_decisions.csv',pd.concat(baseline,ignore_index=True))
    jsave(OUT/'verification_receipt.json',{'status':'PASS','models':model_count,'candidate_scores_replayed':len(frame)*len(TRACKS),
        'maximum_score_error':max(errors),'selected_decisions_checked':decision_count,'historical_H0_decisions_reproduced':len(old_dec),
        'prior_bundle_members_unchanged':old_members,'unrelated_modified_files_unchanged':unchanged,
        'source_only_selection_checked':True,'source_only_folds_checked':True,'code_sha256':sha256(Path(__file__))})
    print('Independent verification PASS',flush=True)

if __name__=='__main__':run()
