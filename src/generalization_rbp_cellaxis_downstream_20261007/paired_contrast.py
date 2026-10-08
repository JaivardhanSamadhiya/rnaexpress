"""Secondary shared-shape sequence-tie diagnostic; selects nothing."""
from .common import *
from .evaluate import selected_model
from .numeric import canonical


def run(root_start=False):
    assert root_start;evaluation_check();np,pd,*_=runtime()
    verified=readj(OUT/'represented_verification_receipt.json')
    assert verified['status']=='PASS' and verified['same_checkpoint_both_states_verified']
    assert verified['evaluation_sha256']==sha256(EVALUATION);hash_files(verified['files'])
    assert not (OUT/'canonical_paired_state_contrast.json').exists();frame=load()
    from src.generalization_knowncell_20261007.canonical_paired_contrast import shared_matrix,common_choices
    from src.generalization_crosscell_20261007.bootstrap import shared_bootstrap
    pairs=pd.read_csv(OLD_KNOWN/'exact_menu_pairs.csv')
    assert len(pairs)==2408 and pairs.biological_component.nunique()==s.COMPONENTS
    output=[];files={};calls=0;maximum=0.
    for track in s.TRACKS:
        x=features(track);pieces=[];roster=[]
        for fold in s.FOLDS:
            rows,shared=shared_matrix(frame,x,pairs,fold)
            for task,(_,source_task) in s.KNOWN_TASKS.items():
                model,config,_,_,path=selected_model(track,source_task,fold,frame,x)
                score,error=canonical(model,shared);maximum=max(maximum,error);calls+=1
                pieces.append(common_choices(rows,score,task))
                roster.append({'task':task,'fold':fold,'configuration':config,'checkpoint':path.relative_to(ROOT).as_posix(),
                    'checkpoint_sha256':sha256(path),'common_matrix_sha256':values_hash(shared),
                    'paired_metadata_sha256':hashlib.sha256(rows.to_csv(index=False,lineterminator='\n').encode()).hexdigest(),
                    'paired_full_feature_bytes_equal':True,'predictor_calls':1})
        d=pd.concat(pieces,ignore_index=True);assert len(d)==2408*2*2
        assert not d.duplicated(['task','pair_context','direction']).any()
        gains={task:d[d.task.eq(task)].groupby('biological_component').known_advantage.mean() for task in s.KNOWN_TASKS}
        assert all(len(v)==s.COMPONENTS for v in gains.values());interval=shared_bootstrap(gains,5000,s.SEED)
        output.append({'track':track,'mean_known_advantage':float(np.mean([v.mean() for v in gains.values()])),
            'per_known_cell':{task:float(v.mean()) for task,v in gains.items()},
            'descriptive_CI':[float(np.quantile(interval,.025)),float(np.quantile(interval,.975))],
            'new_fits':0,'menus':2408,'components':s.COMPONENTS})
        csv=OUT/'represented'/track/'canonical_paired_state_contrast.csv'
        receipt=OUT/'represented'/track/'canonical_paired_state_roster.json'
        csvsave(csv,d);jsave(receipt,roster)
        files[csv.relative_to(ROOT).as_posix()]=sha256(csv);files[receipt.relative_to(ROOT).as_posix()]=sha256(receipt)
        if track in s.REUSED_CONTROLS:
            old=pd.read_csv(OLD_KNOWN/track/'canonical_paired_state_contrast.csv',float_precision='round_trip')
            keys=['task','pair_context','direction'];a,b=[v.sort_values(keys).reset_index(drop=True) for v in (d,old)]
            assert list(a.columns)==list(b.columns)
            pd.testing.assert_frame_equal(a.drop(columns='common_score'),b.drop(columns='common_score'),check_exact=False,atol=1e-12,rtol=0)
            np.testing.assert_allclose(a.common_score,b.common_score,atol=1e-9,rtol=0)
        del x
    assert calls==36;evaluation_check()
    jsave(OUT/'canonical_paired_state_contrast.json',{'status':'DESCRIPTIVE','tracks':output,'files':files,
        'predictor_calls':36,'maximum_independent_score_error':maximum,'new_fits':0,
        'full_feature_bytes_certified_equal':True,'tie_policy':'exact canonical score; shared lexical mutant sequence',
        'main_ID_based_gates_unchanged':True,'selects_nothing':True,'causal_cell_state_claim':False,
        'independent_confirmation':False,'evaluation_sha256':sha256(EVALUATION)})


if __name__=='__main__':
    import sys
    run('--root-start' in sys.argv[1:])
