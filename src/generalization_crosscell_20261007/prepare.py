"""Metadata-first preparation; matrices require certified existing features."""
from .common import *
from .splits import outer_masks,inner_masks
import sys


def metadata():
    from src.generalization_20261007.verify import preservation
    preservation()
    assert not any((OUT/track/'fits').exists() for track in TRACKS)
    frame,_=load(False)
    csvsave(OUT/'row_index.csv.gz',frame,True)
    counts=[]
    for task in TASKS:
        for fold in FOLDS:
            train,test=outer_masks(frame,task,fold)
            source=frame.loc[train].reset_index(drop=True)
            for inner in sorted(source.held_parent_fold.unique()): inner_masks(source,int(inner))
            counts.append({'task':task,'fold':fold,'source_rows':int(train.sum()),'target_rows':int(test.sum()),
                'source_components':source.biological_component.nunique(),
                'target_components':frame.loc[test].biological_component.nunique(),
                'training_ids_sha256':hashlib.sha256('|'.join(frame.loc[train].intervention_id).encode()).hexdigest(),
                'test_ids_sha256':hashlib.sha256('|'.join(frame.loc[test].intervention_id).encode()).hexdigest()})
    csvsave(OUT/'metadata_fold_audit.csv',pd.DataFrame(counts))
    jsave(OUT/'metadata_receipt.json',{'status':'PASS','rows':len(frame),'components':187,
        'core_sha256':sha256(CORE),'folds':FOLDS,'tasks':TASKS,'tracks':TRACKS,'widths':WIDTHS,
        'row_ids_sha256':hashlib.sha256('|'.join(frame.intervention_id).encode()).hexdigest(),
        'outcome_columns_read':False,'original_alleles_retained':True,'project_fits_run':False,
        'source_only_inner_folds_checked':True,'gene_and_exact_allele_exclusions_checked':True})
    print('Metadata/purge preparation PASS; all target cells/genes/alleles excluded',flush=True)


def matrices():
    metadata()
    next_out=ROOT/'results/generalization_next_20261007'
    prepared=readj(next_out/'prepare_receipt.json')
    assert prepared['status']=='PASS','Wait for complete next-generation preparation'
    manifest=readj(next_out/'prefit_manifest.json')
    assert subprocess.check_output(['git','show','HEAD:results/generalization_next_20261007/prefit_manifest.json'],cwd=ROOT)==(next_out/'prefit_manifest.json').read_bytes()
    frame,_=load(False)
    row=readj(next_out/'short_feature_receipt.json')
    original=pd.read_csv(CORE,usecols=['intervention_id'])
    assert row['row_ids_sha256']==hashlib.sha256('|'.join(original.intervention_id).encode()).hexdigest()
    paths={track:NEXT_ART/(track+'_model_features.npz') for track in TRACKS if track!='simple'}
    for track,path in paths.items():
        assert path.exists(), 'Wait for complete features: '+str(path)
        assert sha256(path)==manifest['files'][path.relative_to(ROOT).as_posix()]
    base=None
    for track,path in paths.items():
        with np.load(path) as archive: matrix=archive['features'].astype(float)
        assert matrix.shape==(26258,WIDTHS[track]) and np.isfinite(matrix).all()
        local=matrix[frame.original_core_row.to_numpy(int)]
        if track=='base': base=local.copy()
        else: np.testing.assert_array_equal(local[:,:246],base)
        matrixsave(ART/(track+'_model_features.npz'),local)
        del matrix,local
    names=row['feature_names']
    assert len(names)==246 and names[:18][-1]=='T>G' and names[18:22]==['delta_A','delta_C','delta_G','delta_T']
    assert len(names[:102])==102 and names[101]=='delta_TTT'
    matrixsave(ART/'simple_model_features.npz',base[:,:102])
    jsave(OUT/'prepare_receipt.json',{'status':'PASS','rows':len(frame),'widths':WIDTHS,
        'row_ids_sha256':hashlib.sha256('|'.join(frame.intervention_id).encode()).hexdigest(),
        'source_feature_hashes':{track:sha256(path) for track,path in paths.items()},
        'simple_control':'Exact corrected interaction_3 prefix102 = metadata18 + delta1-3mer84',
        'outcome_columns_read':False,'new_features_or_outcomes_generated':False,'project_fits_run':False})
    print('Seven aligned feature matrices prepared; no fitting',flush=True)


if __name__=='__main__': {'metadata':metadata,'matrices':matrices}[sys.argv[1]]()
