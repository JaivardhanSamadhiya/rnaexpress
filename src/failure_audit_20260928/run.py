"""Diagnose exposed-data repeatability and representation support; no fitting."""
from src.cross_assay_20260927.common import ROOT,sha256,readj,clean,np,pd,frozen
from src.cross_assay_20260927.models import purge
from pathlib import Path
from scipy.stats import kendalltau,spearmanr
import itertools,json,hashlib,gzip,subprocess

OUT=ROOT/'results/failure_audit_20260928'
REP=ROOT/'reports/failure_audit_20260928'
SRC=ROOT/'src/failure_audit_20260928'
OLD=ROOT/'results/cross_assay_20260927'
ART=ROOT/'artifacts/cross_assay_20260927'
MODELS=['metadata','composition','kmer123','interaction_3','interaction_full']

def save(p,data):
    assert p.resolve().is_relative_to(OUT) or p.resolve().is_relative_to(REP)
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==data,'Preserve '+str(p)
    else:p.write_bytes(data)

def jsave(p,x):save(p,(json.dumps(clean(x),indent=2,sort_keys=True,allow_nan=False)+'\n').encode())
def csv(name,x):
    f=pd.DataFrame(x)
    save(OUT/name,f.to_csv(index=False,lineterminator='\n').encode())
    return f

def agreement(x,y):
    x,y=np.asarray(x,float),np.asarray(y,float);ok=np.isfinite(x)&np.isfinite(y);x,y=x[ok],y[ok];n=len(x);total=n*(n-1)//2
    if not total:return np.nan,np.nan,n,0,total
    def ties(a):
        _,c=np.unique(a,return_counts=True,axis=0);return int(np.sum(c*(c-1)//2))
    tx,ty,txy=ties(x),ties(y),ties(np.column_stack([x,y]));usable=total-tx-ty+txy
    if not usable:return np.nan,np.nan,n,0,total
    tau=float(kendalltau(x,y).statistic);signed=tau*np.sqrt(float(total-tx)*float(total-ty))
    return float(np.clip(.5+.5*signed/usable,0,1)),float(spearmanr(x,y).statistic),n,usable,total

def tests():
    # Compare tie-aware fast ordering arithmetic with literal unordered pairs.
    cases=[([0,1,2],[0,1,2]),([0,1,2],[2,1,0]),([0,0,1,2],[0,1,1,0]),([1,1],[2,2]),([0,np.nan,2],[1,0,2])]
    for x,y in cases:
        votes=[]
        for i,j in itertools.combinations(range(len(x)),2):
            if np.isfinite([x[i],x[j],y[i],y[j]]).all() and x[i]!=x[j] and y[i]!=y[j]:votes.append((x[i]-x[j])*(y[i]-y[j])>0)
        a,_,_,n,_=agreement(x,y);assert n==len(votes)
        assert (np.isnan(a) if not votes else abs(a-np.mean(votes))<1e-12)
    return len(cases)

def macro(frame,values):
    return frame.groupby(['dataset','biological_component','parent_context_id'])[values].mean().groupby(['dataset','biological_component']).mean().groupby('dataset').mean().reset_index()

def table(f):
    def fmt(v):
        if isinstance(v,(float,np.floating)):return f'{v:.4f}' if np.isfinite(v) else 'unavailable'
        return str(v).replace('|',' / ')
    return '\n'.join(['| '+' | '.join(f.columns)+' |','| '+' | '.join(['---']*len(f.columns))+' |']+['| '+' | '.join(fmt(v) for v in row)+' |' for row in f.itertuples(index=False,name=None)])

def run():
    freeze=frozen();before=readj(OLD/'initial_state.json')
    for p,h in before['unchanged_user_files'].items():assert sha256(ROOT/p)==h
    delivery=readj(ART/'delivery_receipt.json')
    for p,e in delivery['manifest'].items():assert sha256(ROOT/p)==e['sha256'],p
    assert sha256(ROOT/delivery['archive'])==delivery['sha256']
    assert readj(OLD/'gate_verdict.json')['new_dataset_discovery_allowed'] is False
    inputs={p.relative_to(ROOT).as_posix():sha256(p) for p in [ART/'canonical_interventions.csv',ART/'features.npz',OLD/'model_row_index.csv',OLD/'gate_verdict.json',REP/'protocol.md',Path(__file__)]}
    jsave(OUT/'input_manifest.json',{'inputs':inputs,'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'retrospective_exposed_diagnosis':True})
    count=tests();f=pd.read_csv(ART/'canonical_interventions.csv',low_memory=False);f=f[f.primary_eligible].reset_index(drop=True)
    pairs=[];choices=[];aggregation=[];availability=[]
    for (study,context),g in f.groupby(['dataset','parent_context_id']):
        base={'dataset':study,'parent_context_id':context,'biological_component':g.biological_component.iloc[0],'candidates':len(g)}
        parsed=[np.array([float(v) for v in str(s).split(';')]) if pd.notna(s) and str(s) not in ('','None') else np.array([]) for s in g.replicate_delta_values]
        widths={len(v) for v in parsed if len(v)};assert len(widths)<=1
        nr=max(widths,default=0);r=np.full((len(g),nr),np.nan)
        for i,v in enumerate(parsed):
            if len(v):r[i]=v
        availability.append({**base,'replicate_slots':nr,'rows_with_two_replicates':int((np.isfinite(r).sum(axis=1)>=2).sum()),'status':'AVAILABLE' if nr>=2 else 'NO_ADMITTED_PAIRED_REPLICATE_DELTAS'})
        if nr<2:continue
        for a,b in itertools.combinations(range(nr),2):
            acc,rho,n,k,total=agreement(r[:,a],r[:,b]);pairs.append({**base,'replicate_a_slot':a+1,'replicate_b_slot':b+1,'ordering_agreement':acc,'spearman':rho,'common_candidates':n,'comparable_pairs':k,'all_pairs':total})
        raw=np.divide(np.nansum(r,axis=1),np.isfinite(r).sum(axis=1),out=np.full(len(r),np.nan),where=np.isfinite(r).sum(axis=1)>0)
        acc,rho,n,k,total=agreement(raw,g.measured_delta.to_numpy());aggregation.append({**base,'ordering_agreement':acc,'spearman':rho,'common_candidates':n,'comparable_pairs':k,'all_pairs':total})
        ids=g.intervention_id.to_numpy()
        for j in range(nr):
            rest=np.delete(r,j,axis=1);number=np.isfinite(rest).sum(axis=1);score=np.divide(np.nansum(rest,axis=1),number,out=np.full(len(g),np.nan),where=number>0)
            ok=np.isfinite(score)&np.isfinite(r[:,j]);y=r[ok,j];s=score[ok];cid=ids[ok]
            if len(y)<2 or np.ptp(y)<=1e-12:continue
            for direction in (-1,1):
                ix=np.lexsort((cid,-direction*s))[0];effect=direction*y;regret=(effect.max()-effect[ix])/np.ptp(effect)
                choices.append({**base,'held_replicate_slot':j+1,'direction':direction,'evaluated_candidates':len(y),'selected_id':cid[ix],'regret':regret,'uniform_regret':float(np.mean((effect.max()-effect)/np.ptp(effect))),'wrong_direction':float(effect[ix]<-1e-12),'correct_direction':float(effect[ix]>1e-12),'feasible':float((effect>1e-12).any())})
        if len(pairs)%1000<nr:print('Replicate diagnostics',study,context,flush=True)
    pa=csv('replicate_pair_contexts.csv',pairs);ch=csv('replicate_choice_contexts.csv',choices);ag=csv('processed_vs_raw_contexts.csv',aggregation);av=csv('replicate_availability.csv',availability)
    pm=macro(pa,['ordering_agreement','spearman']);cm=macro(ch,['regret','uniform_regret','wrong_direction','correct_direction']);am=macro(ag,['ordering_agreement','spearman'])
    csv('replicate_pair_summary.csv',pm);csv('replicate_choice_summary.csv',cm);csv('processed_vs_raw_summary.csv',am)
    print('Replicate diagnostics complete',flush=True)
    idx=pd.read_csv(OLD/'model_row_index.csv');frame=pd.read_csv(ART/'canonical_interventions.csv',low_memory=False).set_index('intervention_id').loc[idx.intervention_id].reset_index();core=frame.primary_eligible.to_numpy();xs=np.load(ART/'features.npz');schema=readj(OLD/'feature_schema.json')['columns'];support=[];dims=[];collisions=[]
    for study in sorted(f.dataset.unique()):
        te=core&frame.dataset.eq(study).to_numpy();tr=purge(frame,core&frame.dataset.ne(study).to_numpy(),te);train=frame[tr];test=frame[te]
        assert not set(train.biological_component)&set(test.biological_component)
        metadata=pd.DataFrame({'dataset':study,'parent_context_id':test.parent_context_id,'biological_component':test.biological_component,'unsupported_edit_size':~test.substitution_count.isin(train.substitution_count),'parent_length_outside_training_range':~test.parent_sequence.str.len().between(train.parent_sequence.str.len().min(),train.parent_sequence.str.len().max())})
        for model in MODELS:
            a,b=xs[model][tr],xs[model][te];low=a.min(axis=0);high=a.max(axis=0);constant=(high-low)<=1e-12
            # Constant training dimensions differing from any test candidate are support gaps.
            novel=constant & np.any(abs(b-low)>1e-12,axis=0)
            local=metadata.copy();local['any_feature_outside_training_range']=((b<low-1e-12)|(b>high+1e-12)).any(axis=1);local['any_unlearnable_constant_feature']=np.any(abs(b[:,constant]-low[constant])>1e-12,axis=1) if constant.any() else False
            summary=macro(local,['unsupported_edit_size','parent_length_outside_training_range','any_feature_outside_training_range','any_unlearnable_constant_feature']).iloc[0].to_dict();summary.update(model=model,training_rows=int(tr.sum()),test_rows=int(te.sum()),train_constant_dimensions=int(constant.sum()),unsupported_constant_dimensions=int(novel.sum()));support.append(summary)
            for j in np.flatnonzero(novel):dims.append({'dataset':study,'model':model,'feature':schema[model][j],'training_constant':float(low[j]),'test_min':float(b[:,j].min()),'test_max':float(b[:,j].max())})
            for context,gg in test.groupby('parent_context_id'):
                xx=xs[model][gg.index];_,inv,counts=np.unique(xx,axis=0,return_inverse=True,return_counts=True);y=gg.measured_delta.to_numpy();means=np.bincount(inv,weights=y)/counts
                collision=float(np.mean(counts[inv]>1));bound=((y.max()-means.max())+(means.min()-y.min()))/(2*np.ptp(y))
                assert -.00000001<=bound<=.50000001
                collisions.append({'dataset':study,'parent_context_id':context,'biological_component':gg.biological_component.iloc[0],'model':model,'candidates':len(y),'unique_feature_vectors':len(counts),'collision_candidate_fraction':collision,'optimistic_feature_only_regret_bound':bound})
        print('Support diagnostics',study,flush=True)
    su=csv('feature_support_summary.csv',support);csv('unsupported_dimensions.csv',dims);co=csv('representation_collision_contexts.csv',collisions)
    cs=pd.concat([macro(g,['collision_candidate_fraction','optimistic_feature_only_regret_bound']).assign(model=m) for m,g in co.groupby('model')],ignore_index=True);csv('representation_collision_summary.csv',cs)
    availability_summary=av.groupby('dataset').agg(contexts=('parent_context_id','size'),contexts_with_replicates=('replicate_slots',lambda x:int((x>=2).sum())),candidate_rows=('candidates','sum'),rows_with_two_replicates=('rows_with_two_replicates','sum')).reset_index()
    report=f'''# Failure diagnosis on exposed data

The cross-assay development result remains **NO-GO**. No model was fitted, selected or retuned, and no independent resource was searched or opened. This diagnostic addresses repeatability, target-estimator agreement, edit-design support, and exact representation collisions. It does not establish which factor caused the failure.

## Replicate coverage

{table(availability_summary)}

Moffatt lacks paired replicate contrasts in the admitted table; its reliability is unknown here, not zero. Astrocyte slots correspond to original labels 1–9 and 11–15. Missing values stay missing. Mikl and astrocyte raw contrasts differ from author-processed estimators; their repeatability is not a certified ceiling on the processed target. SRLE replicates belong to the same single reporter experiment as the original aggregate.

## Does candidate ordering repeat?

{table(pm)}

Ordering agreement omits pairs tied in either measurement. 0.5 is chance-like agreement, not a formal statistical null test. Every replicate pair was used; shared replicates and overlapping candidates are not independent replications. Context-level counts and missingness remain in the CSVs. Aggregation is equal parent within frozen component, then equal component within study. No significance/effect filter was used.

## Select using other replicates, evaluate in the omitted replicate

{table(cm)}

This uses measured outcomes from other replicates and therefore is an outcome-informed repeatability benchmark, not a deployable sequence model. Candidate subsets require a finite held-out value and at least one finite remaining replicate, with two candidates and nonzero held-out range. The two requested directions are averaged. Selected raw effects can change sign because the WT contrast is uncertain. A poor result cannot prove that no sequence model can denoise the measurements.

## Processed outcome versus mean raw contrasts

{table(am)}

These estimates share measurement information and are not validation. Disagreement is an estimator/provenance diagnostic; it does not automatically make the author estimator wrong.

## Training support under the original whole-study purge

{table(su)}

Fractions are component-macro candidate fractions. A constant training feature has no estimable ranking coefficient in these standardized regularized linear fits. An out-of-range feature signals extrapolation, not inevitable failure; it may be irrelevant to within-parent ranking. Length and edit-size shifts confound study, intervention design and biological domain. Every unsupported feature is listed in `unsupported_dimensions.csv`.

## Exact representation collisions

{table(cs)}

Identical vectors cannot distinguish candidates without using extra information. The optimistic bound allows outcome-informed selection of the best feature-equivalence group separately for every parent and random selection within the group. A near-zero bound means exact collisions do not explain failure by themselves; it does not demonstrate that a fitted linear model can achieve the bound. Float32 equality matches the saved model inputs. More approximate similarity and related-sequence grouping remain unaudited.

## Interpretation boundary

These measurements can identify a specific deficiency to investigate, but cannot justify retroactively changing the failed gate, filtering noisy candidates into a favorable test, claiming universality, or consuming a new untouched resource. Separate biology, sampling noise, estimator choices and model misspecification remain possible explanations. A future proposal must state which deficiency it addresses and how that claim can fail.

All previous files are preserved. Only the new `failure_audit_20260928` namespaces are written. See `verification_receipt.json` for source hashes, preservation and analytic checks. No paid resources, new datasets, broad pytest, or protected outcomes were used.
'''
    save(REP/'results.md',report.encode())
    for p,h in inputs.items():assert sha256(ROOT/p)==h
    for p,e in delivery['manifest'].items():assert sha256(ROOT/p)==e['sha256']
    for p,h in before['unchanged_user_files'].items():assert sha256(ROOT/p)==h
    jsave(OUT/'verification_receipt.json',{'status':'PASS','analytic_checks':count,'prior_bundle_members_unchanged':len(delivery['manifest']),'prefit_hashes_unchanged':len(freeze['files']),'unrelated_modified_files_unchanged':len(before['unchanged_user_files']),'primary_rows':len(f),'replicate_pair_context_rows':len(pa),'replicate_choice_rows':len(ch),'representation_context_rows':len(co),'new_model_fits':0,'new_datasets':0,'gate_changed':False,'source_hashes':inputs})
    print('PASS; diagnostics complete. No gate change.',flush=True)

if __name__=='__main__':run()
