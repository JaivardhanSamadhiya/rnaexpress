from .common import *
from .models import transformed,probabilities,candidate_scores
from src.cross_assay_20260927.models import row_weights
from src.cross_assay_20260927.metrics import pair_accuracy
from scipy.stats import spearmanr

def ambiguity(frame,r):
    result={}
    def tails(a,b):
        d=a-b;n=np.isfinite(d).sum(-1);wins=(d>TOL).sum(-1);loss=(d<-TOL).sum(-1);ties=n-wins-loss
        return 1-betainc(wins+.5*ties+.5,loss+.5*ties+.5,.5),n
    for context,g in frame.groupby('parent_context_id'):
        v=r[g.index];n=len(v)
        for direction in (-1,1):
            if not (np.isfinite(v).sum(1)>=2).any():result[context,direction]='UNAVAILABLE';continue
            vv=direction*v;champion=0
            for j in range(1,n):
                tail,count=tails(vv[j],vv[champion])
                if count>=2 and tail>=.9:champion=j
            tail,count=tails(vv[champion],vv);other=np.arange(n)!=champion
            result[context,direction]='UNIQUE_REPLICATE_SUPPORTED_OPTIMUM' if ((count[other]>=2)&(tail[other]>=.9)).all() else 'AMBIGUOUS'
    return result

def calibration(frame,x,r,pairs,model,stage,held,rep_slots=None,save_pairs=False):
    ids=frame.index.to_numpy();mask=pairs.left.isin(ids)&pairs.right.isin(ids);p=pairs[mask].copy().reset_index(drop=True);z=transformed(model,x);a=p.left.to_numpy();b=p.right.to_numpy();pred=probabilities(model,z[a],z[b]);rr=r if rep_slots is None else r[:,rep_slots];s=pair_stats(rr[a]-rr[b]);lookup=frame.measured_delta
    delta=lookup.loc[a].to_numpy()-lookup.loc[b].to_numpy();aggregate=np.where(delta>TOL,1,np.where(delta<-TOL,0,.5));summaries=[];bins=[];records=[]
    for endpoint,q,valid in [('aggregate',aggregate,np.ones(len(p),bool)),('replicate',s['q1'],s['n']>0)]:
        if not valid.any():continue
        pp=p[valid].reset_index(drop=True);prob=pred[valid];truth=q[valid];w=pair_weights(frame,pp);pc=np.clip(prob,1e-12,1-1e-12)
        brier=truth*(1-prob)**2+(1-truth)*prob**2;logloss=-(truth*np.log(pc)+(1-truth)*np.log1p(-pc));bid=np.minimum((np.r_[prob,1-prob]*10).astype(int),9);pv=np.r_[prob,1-prob];yv=np.r_[truth,1-truth];ww=np.r_[w,w]/2;ece=0
        for k in range(10):
            take=bid==k;mass=ww[take].sum()
            if mass:mp=float(ww[take]@pv[take]/mass);mq=float(ww[take]@yv[take]/mass);ece+=mass*abs(mp-mq)
            else:mp=mq=np.nan
            bins.append({'stage':stage,'held':held,'model':model['name'],'dataset':frame.dataset.iloc[0],'endpoint':endpoint,'bin':k,'left':k/10,'right':(k+1)/10,'weight':mass,'predicted':mp,'observed_support':mq,'oriented_pairs':int(take.sum())})
        summaries.append({'stage':stage,'held':held,'model':model['name'],'dataset':frame.dataset.iloc[0],'endpoint':endpoint,'pairs':len(pp),'contexts':pp.parent_context_id.nunique(),'brier':float(w@brier),'log_loss':float(w@logloss),'ece':float(ece),'sharpness':float(w@abs(2*prob-1))})
    if save_pairs:
        for j,row in enumerate(p.itertuples()):records.append({'stage':stage,'held':held,'model':model['name'],'dataset':row.dataset,'parent_context_id':row.parent_context_id,'biological_component':row.biological_component,'pair_id':row.pair_id,'left_id':row.left_id,'right_id':row.right_id,'probability_left_beats_right':float(pred[j]),'reverse_probability':float(1-pred[j]),'aggregate_target':float(aggregate[j]),'replicate_win_fraction':float(s['q1'][j]),'valid_replicates':int(s['n'][j]),'information_scope':'held-out evaluation only; unavailable during fit'})
    return summaries,bins,records

def decisions(frame,x,r,model,stage,held,ambiguous,replicate_diagnostic=False,conditional_policy=False):
    out=[];rankings=[];raw=[];policy=[];predictions=[];allscore={}
    for context,g in frame.groupby('parent_context_id',sort=True):
        ix=g.index.to_numpy();ids=g.intervention_id.to_numpy();y=g.measured_delta.to_numpy();n=len(g)
        if n<2 or np.ptp(y)<=TOL:continue
        score,latent,matrix,expected=candidate_scores(model,x[ix]);allscore.update(zip(ix,score));z=transformed(model,x[ix]);direction_prob=expit(np.column_stack([np.ones(n),z])@model['direction_beta'])
        pair=pair_accuracy(y,score);rho=0 if np.ptp(score)<=TOL else float(spearmanr(y,score).statistic)
        clipped=np.clip(matrix,1e-12,1-1e-12);entropy=(-(clipped*np.log2(clipped)+(1-clipped)*np.log2(1-clipped)).sum(1)-1)/(n-1)
        for direction in (-1,1):
            truth=direction*y;utility=direction*score;order=np.lexsort((ids,-utility));j=order[0];pm=matrix if direction==1 else 1-matrix;diag=pm.copy();np.fill_diagonal(diag,1);minwin=diag.min(1);best=truth==truth.max();wrong=truth<-TOL;valid=truth>TOL;regret=(truth.max()-truth)/np.ptp(truth);amb=ambiguous.get((context,direction),'UNAVAILABLE')
            base={'stage':stage,'held':held,'model':model['name'],'dataset':g.dataset.iloc[0],'biological_component':g.biological_component.iloc[0],'parent_context_id':context,'direction':direction,'candidates':n}
            row={**base,'selected_id':ids[j],'regret':float(regret[j]),'raw_regret':float(truth.max()-truth[j]),'correct_direction':float(valid[j]),'wrong_direction':float(wrong[j]),'avoidable_wrong':float(wrong[j] and valid.any()),'unavoidable_wrong':float(wrong[j] and wrong.all()),'neutral_only_alternative_wrong':float(wrong[j] and not valid.any() and not wrong.all()),'no_feasible_candidate':float(not valid.any()),'best_recovery':float(best[j]),'top5_best_recovery':float(best[order[:min(n,5)]].any()),'pairwise_accuracy':pair,'spearman':rho,'direction_head_brier':float(np.mean((direction_prob-(y>TOL))**2)),'minimum_win_probability':float(minwin[j]),'expected_win_fraction':float(expected[j] if direction==1 else 1-expected[j]),'mean_pairwise_entropy_bits':float(entropy[j]),'measurement_ambiguity':amb}
            out.append(row)
            if stage=='held_assay':
                ranks=np.empty(n,int);ranks[order]=np.arange(1,n+1)
                rankings.extend({**base,'candidate_id':ids[k],'rank':int(ranks[k]),'selected':bool(k==j),'candidate_score':float(direction*score[k]),'latent_utility':float(direction*latent[k]),'expected_win_fraction':float(expected[k] if direction==1 else 1-expected[k]),'minimum_win_probability':float(minwin[k]),'mean_pairwise_entropy_bits':float(entropy[k]),'observed_delta':float(y[k])} for k in range(n))
            if conditional_policy:
                chosen=np.lexsort((ids,-minwin))[0];accept=minwin[chosen]>=.8;policy.append({**base,'selected_id':ids[chosen],'accepted':bool(accept),'minimum_win_probability':float(minwin[chosen]),'regret':float(regret[chosen]),'correct_direction':float(valid[chosen]),'wrong_direction':float(wrong[chosen]),'avoidable_wrong':float(wrong[chosen] and valid.any())})
        if stage=='held_assay':predictions.extend({'model':model['name'],'dataset':g.dataset.iloc[0],'parent_context_id':context,'intervention_id':ids[k],'score':float(score[k]),'latent_utility':float(latent[k]),'direction_probability':float(direction_prob[k])} for k in range(n))
        if replicate_diagnostic:
            rr=r[ix]
            for slot in range(rr.shape[1]):
                other=np.delete(rr,slot,axis=1);count=np.isfinite(other).sum(1);othermean=np.divide(np.nansum(other,axis=1),count,out=np.full(n,np.nan),where=count>0);keep=np.isfinite(rr[:,slot])&np.isfinite(othermean);yy=rr[keep,slot];ss=score[keep];oo=othermean[keep];cid=ids[keep]
                if len(yy)<2 or np.ptp(yy)<=TOL:continue
                for direction in (-1,1):
                    yy_dir=direction*yy;j=np.lexsort((cid,-direction*ss))[0];oracle=np.lexsort((cid,-direction*oo))[0];loss=(yy_dir.max()-yy_dir)/np.ptp(yy_dir)
                    raw.append({'stage':stage,'model':model['name'],'dataset':g.dataset.iloc[0],'biological_component':g.biological_component.iloc[0],'parent_context_id':context,'replicate_slot':slot,'direction':direction,'candidates':len(yy),'model_regret':float(loss[j]),'uniform_regret':float(loss.mean()),'replicate_regret':float(loss[oracle]),'wrong_direction':float(yy_dir[j]<-TOL),'selected_id':cid[j]})
    return out,rankings,raw,policy,predictions,allscore

FIELDS=['regret','raw_regret','correct_direction','wrong_direction','avoidable_wrong','unavoidable_wrong','neutral_only_alternative_wrong','no_feasible_candidate','best_recovery','top5_best_recovery','pairwise_accuracy','spearman','direction_head_brier']
def summarize(dec):
    result=macro(dec,FIELDS)
    extra=[]
    for key,g in dec.groupby(['stage','model','dataset']):extra.append(dict(zip(['stage','model','dataset'],key))|{'decision_sets':g.parent_context_id.nunique(),'components':g.biological_component.nunique(),'variant_weighted_regret':float(np.average(g.regret,weights=g.candidates)),'measurement_ambiguous_fraction':float(g.assign(v=g.measurement_ambiguity.eq('AMBIGUOUS')).groupby('biological_component').v.mean().mean()),'measurement_unavailable_fraction':float(g.assign(v=g.measurement_ambiguity.eq('UNAVAILABLE')).groupby('biological_component').v.mean().mean())})
    return result.merge(pd.DataFrame(extra),on=['stage','model','dataset'],validate='one_to_one')

def conditional_eligibility(cal):
    eligible=[];details=[]
    # Pool held-parent fold metrics weighted by held component counts supplied by runner.
    s=cal[cal.stage.eq('held_parent')&cal.endpoint.eq('replicate')]
    for name in PRIMARY[1:]:
        ok=[]
        for study in [STUDIES[0],STUDIES[1]]:
            a=s[s.model.eq(name)&s.dataset.eq(study)];b=s[s.model.eq('H0')&s.dataset.eq(study)]
            if not len(a) or not len(b):ok.append(False);continue
            av={k:np.average(a[k],weights=a.components) for k in ['brier','log_loss','ece']};bv={k:np.average(b[k],weights=b.components) for k in ['brier','log_loss','ece']};passed=bv['brier']-av['brier']>=.005 and bv['log_loss']-av['log_loss']>=.01 and av['ece']<=.05;ok.append(passed);details.append({'model':name,'dataset':study,'brier_gain':bv['brier']-av['brier'],'logloss_gain':bv['log_loss']-av['log_loss'],'ece':av['ece'],'passes':passed})
        if len(ok)==2 and all(ok):eligible.append(name)
    return {'eligible_models':eligible,'checks':details,'absolute_benefit_abstention':'NOT_IDENTIFIED_BY_PAIRWISE_PROBABILITIES','status':'ELIGIBLE_FOR_FIXED_RELATIVE_POLICY' if eligible else 'NOT_RUN_CALIBRATION_REQUIREMENTS_NOT_MET'}
