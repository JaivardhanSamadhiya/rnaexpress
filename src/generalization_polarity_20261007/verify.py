"""Postfit arithmetic and preservation audit; no model selection or new fits."""
from .common import *
from .engine import module,features
from .routes import endpoint_sign
from src.cross_assay_20260927.models import purge

def preservation():
    from src.generalization_20261007.verify import preservation as prior_preservation
    unchanged, old_members = prior_preservation()
    freeze_check()
    delivery_path = ROOT/'artifacts/generalization_20261007/delivery_receipt.json'
    delivery = readj(delivery_path)
    assert sha256(ROOT/delivery['archive']) == delivery['sha256']
    for path, entry in delivery['manifest'].items():
        assert sha256(ROOT/path) == entry['sha256'], path
    return unchanged, old_members + [len(delivery['manifest'])]

def run():
    unchanged,old_members=preservation()
    frame,_=load();errors=[];decision_count=0;model_count=0;inner_replayed=0
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
            source=frame.loc[train].reset_index(drop=True);source_x=x[train]
            for config in mod.CONFIGS:
                for held_inner in sorted(source.dataset.unique()):
                    validation=source.dataset.eq(held_inner).to_numpy()
                    inner_train=purge(source,~validation,validation)
                    tr=source.loc[inner_train].reset_index(drop=True)
                    va=source.loc[validation].reset_index(drop=True)
                    saved=readj(OUT/track/'fits'/(held+'__inner__'+held_inner+'_'+config['id']+'.json'))
                    ids=hashlib.sha256('|'.join(tr.intervention_id).encode()).hexdigest()
                    assert saved['_training_ids_sha256']==ids and saved['_config']==config
                    assert saved['track']==track and saved['_prefit_manifest_sha256']==sha256(OUT/'prefit_manifest.json')
                    assert not {held,held_inner}&set(saved['_training_studies'])
                    assert not set(tr.biological_component)&set(va.biological_component)
                    original=tr.measured_delta.to_numpy(float)
                    used=original*endpoint_sign(tr) if track=='polarity' else original
                    assert saved['training_original_effect_sha256']==hashlib.sha256(original.tobytes()).hexdigest()
                    assert saved['training_used_effect_sha256']==hashlib.sha256(used.tobytes()).hexdigest()
                    actual_inner=mod.predict_model(saved,source_x[validation])
                    replay_regret=inner_regret(va,actual_inner)
                    row=inner[inner.outer_held.eq(held)&inner.inner_held.eq(held_inner)&inner.configuration.eq(config['id'])]
                    assert len(row)==1 and abs(float(row.regret.iloc[0])-replay_regret)<1e-12
                    assert row.training_ids_sha256.iloc[0]==ids
                    inner_replayed+=1
            selected=fold['selected_configuration']
            values=inner[inner.outer_held.eq(held)].groupby('configuration').regret.mean()
            minimum=float(values.min())
            choice=next(c for c in mod.CONFIGS if float(values[c['id']])<=minimum+1e-12)
            assert choice==selected
            m=readj(OUT/track/'fits'/(held+'__outer_'+selected['id']+'.json'))
            assert m['_training_ids_sha256']==expected and held not in m['_training_studies']
            assert m['track']==track and m['_prefit_manifest_sha256']==sha256(OUT/'prefit_manifest.json')
            original=source.measured_delta.to_numpy(float)
            used=original*endpoint_sign(source) if track=='polarity' else original
            assert m['training_original_effect_sha256']==hashlib.sha256(original.tobytes()).hexdigest()
            assert m['training_used_effect_sha256']==hashlib.sha256(used.tobytes()).hexdigest()
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
        assert len(list((OUT/track/'fits').glob('*.json')))==40
        print('Verified',track,flush=True)
    # Holding SRLE leaves projection-only training: identical selection and
    # coefficients must yield exact opposite known-nuclear scores.
    controls={}
    for track in TRACKS:
        fold=next(f for f in readj(OUT/track/'folds.json') if f['held']=='srle')
        model=readj(OUT/track/'fits'/('srle__outer_'+fold['selected_configuration']['id']+'.json'))
        controls[track]=(fold,model)
    assert controls['unflipped'][0]['selected_configuration']==controls['polarity'][0]['selected_configuration']
    for key in ('beta','mean','scale','active','pair_rms'):
        np.testing.assert_array_equal(controls['unflipped'][1][key],controls['polarity'][1][key])
    srle_x=features('unflipped')[frame.dataset.eq('srle').to_numpy()]
    a=module('unflipped').predict_model(controls['unflipped'][1],srle_x)
    b=module('polarity').predict_model(controls['polarity'][1],srle_x)
    np.testing.assert_array_equal(a,-b)
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
        'source_only_selection_checked':True,'source_only_folds_checked':True,
        'inner_checkpoints_and_original_truth_regret_replayed':inner_replayed,
        'training_orientation_hashes_checked':True,'srle_inversion_identity_checked':True,
        'code_sha256':sha256(Path(__file__))})
    print('Independent verification PASS',flush=True)

if __name__=='__main__':run()
