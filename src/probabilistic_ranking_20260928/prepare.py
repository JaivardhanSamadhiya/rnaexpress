from .common import *

def run():
    legacy_frozen();old=readj(OLD/'initial_state.json')
    for p,h in old['unchanged_user_files'].items():assert sha256(ROOT/p)==h
    receipts=[]
    for path in [OA/'delivery_receipt.json',ROOT/'artifacts/failure_audit_20260928/delivery_receipt.json']:
        r=readj(path)
        for p,e in r['manifest'].items():assert sha256(ROOT/p)==e['sha256'],p
        assert sha256(ROOT/r['archive'])==r['sha256'];receipts.append({'path':path.relative_to(ROOT).as_posix(),'sha256':sha256(path),'members':len(r['manifest'])})
    jsave(OUT/'initial_state.json',{'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'previous_receipts':receipts,'unchanged_user_files':old['unchanged_user_files'],'status':subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True).splitlines()})
    original=pd.read_csv(OA/'canonical_interventions.csv',low_memory=False);order=pd.read_csv(OLD/'model_row_index.csv');original=original.set_index('intervention_id').loc[order.intervention_id].reset_index();keep=original.primary_eligible.to_numpy();f=original[keep].reset_index(drop=True)
    f['feature_row']=np.arange(len(f));f['historical_feature_row']=np.flatnonzero(keep)
    with np.load(OA/'features.npz') as z:x=z['interaction_3'][keep]
    r=np.full((len(f),14),np.nan);long=[]
    for i,row in enumerate(f.itertuples()):
        values=np.array([float(v) for v in str(row.replicate_delta_values).split(';')]) if pd.notna(row.replicate_delta_values) and str(row.replicate_delta_values)!='None' else np.array([])
        labels=[1,2,3,4,5,6,7,8,9,11,12,13,14,15] if row.dataset==STUDIES[0] else list(range(1,({'srle':2,'mikl_gse173098':3,'moffatt_gse334718':4}[row.dataset])+1))
        if len(values):assert len(values)==len(labels);r[i,:len(values)]=values
        for slot,rep in enumerate(labels):
            value=r[i,slot];long.append({'dataset':row.dataset,'assay':row.assay,'parent_context_id':row.parent_context_id,'parent_id':row.parent_id,'candidate_id':row.intervention_id,'replicate_id':rep,'replicate_slot':slot,'measured_localization_value':value,'value_semantics':'paired candidate-minus-WT localization contrast; absolute value unavailable','desired_direction':1,'desired_direction_transformed_value':value,'qc_status':'FINITE_ADMITTED_CONTRAST' if np.isfinite(value) else 'MISSING_ADMITTED_PAIRED_CONTRAST','provenance_status':row.provenance_status,'biological_component':row.biological_component,'gene_transcript':row.gene_transcript,'feature_row':i,'feature_block':'interaction_3','parent_sequence':row.parent_sequence,'mutant_sequence':row.mutant_sequence,'edit_start':row.edit_start,'edit_end':row.edit_end,'substitution_count':row.substitution_count,'delta_A':float(x[i,18]),'delta_C':float(x[i,19]),'delta_G':float(x[i,20]),'delta_T':float(x[i,21])})
    pairs=[]
    for context,g in f.groupby('parent_context_id',sort=True):
        ids=g.index.to_numpy();n=len(ids);total=n*(n-1)//2
        if total<=256:chosen=list(itertools.combinations(range(n),2))
        else:
            rng=np.random.default_rng(int(hashlib.sha256(('20260927'+context).encode()).hexdigest()[:8],16));s=set()
            while len(s)<256:s.add(tuple(sorted(rng.choice(n,2,replace=False).tolist())))
            chosen=sorted(s)
        pairs.extend({'dataset':g.dataset.iloc[0],'parent_context_id':context,'biological_component':g.biological_component.iloc[0],'left':int(ids[a]),'right':int(ids[b])} for a,b in chosen)
    p=pd.DataFrame(pairs);a=p.left.to_numpy();b=p.right.to_numpy();d=r[a]-r[b];s=pair_stats(d);delta=f.measured_delta.to_numpy()[a]-f.measured_delta.to_numpy()[b]
    p['left_id']=f.intervention_id.to_numpy()[a];p['right_id']=f.intervention_id.to_numpy()[b];p['pair_id']=[hashlib.sha256((aa+'|'+bb).encode()).hexdigest()[:20] for aa,bb in zip(p.left_id,p.right_id)]
    p['aggregate_difference']=delta;p['q_H0']=np.where(delta>0,1,np.where(delta<0,0,.5));p['historical_train_eligible']=delta!=0
    for k,v in s.items():p[k]=v
    p['q_P1']=np.where(s['n']>0,s['q1'],p.q_H0);p['q_P2']=np.where(s['n']>0,s['q2'],p.q_H0)
    p['replicate_differences']=[';'.join(str(v) for v in row) for row in d]
    p['target_status']=np.where(s['n']>0,'EMPIRICAL_REPLICATE_SUPPORT','FALLBACK_AGGREGATE_NO_PAIRED_REPLICATES')
    csvsave(OUT/'candidate_index.csv',f,True);csvsave(ART/'replicate_candidate_measurements.csv',pd.DataFrame(long),True);csvsave(ART/'replicate_pairwise_evidence.csv',p,True);npzsave(ART/'data.npz',features=x,replicates=r)
    jsave(OUT/'preparation_receipt.json',{'status':'PASS','rows':len(f),'pair_roster':len(p),'historical_training_pairs':int(p.historical_train_eligible.sum()),'replicate_rows':len(long),'finite_replicate_rows':int(np.isfinite(r).sum()),'feature':'interaction_3','features':x.shape[1],'missing_paired_replicate_assays':['moffatt_gse334718'],'source_files':{p.relative_to(ROOT).as_posix():sha256(p) for p in [OA/'canonical_interventions.csv',OA/'features.npz',OLD/'model_row_index.csv',OLD/'fold_manifest.json']}})
    print('Prepared',len(f),'candidates',len(p),'sampled pairs',len(long),'replicate rows',flush=True)
if __name__=='__main__':run()
