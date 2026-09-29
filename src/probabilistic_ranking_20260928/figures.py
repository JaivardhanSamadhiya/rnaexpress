from .common import *
import sys
sys.path.insert(0,str(ROOT/'data/interim/research_20260921/plot_runtime'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
COL={'H0':'#555555','P1':'#297fa6','P2':'#2c8261','P3':'#a66630'}
FOOT='Exposed development only | balanced biological units | no independent confirmation | prior NO-GO preserved'
def output(fig,name,caption):
    fig.text(.015,.015,FOOT,fontsize=8,color='#555')
    for ext in ('png','svg'):
        b=io.BytesIO();fig.savefig(b,format=ext,dpi=180,bbox_inches='tight',metadata={'Date':None} if ext=='svg' else {'Software':'RNA probabilistic ranking'});value=b.getvalue()
        if ext=='svg':value=('\n'.join(v.rstrip() for v in value.decode().splitlines())+'\n').encode()
        save(ART/(name+'.'+ext),value)
    plt.close(fig);return {'figure':name,'caption':caption}
def run():
    frozen();plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.hashsalt':'probabilistic-ranking-20260928'});caps=[]
    frame,_,_,pairs=load();comp=pd.read_csv(ART/'model_comparison.csv');core=comp[comp.stage.eq('held_assay')];reliability=pd.read_csv(ROOT/'results/failure_audit_20260928/replicate_pair_summary.csv');available=[s for s in STUDIES if s in set(reliability.dataset)];p=pairs[pairs.n.gt(0)&pairs.historical_train_eligible].reset_index(drop=True)
    fig,axes=plt.subplots(1,2,figsize=(13,5));fig.subplots_adjust(bottom=.18,wspace=.38)
    rr=reliability.set_index('dataset').loc[available];axes[0].bar(range(3),rr.ordering_agreement,color=['#297fa6','#2c8261','#8752a1']);axes[0].axhline(.5,color='#888',linestyle='--');axes[0].set_xticks(range(3),[label(s) for s in available]);axes[0].set_ylim(0,1);axes[0].set_ylabel('Replicate pair-order agreement');axes[0].set_title('A  Previously audited repeatability',loc='left')
    for study in available:
        pp=p[p.dataset.eq(study)];w=pair_weights(frame[frame.dataset.eq(study)],pp);axes[1].hist(pp.q_P1,bins=np.linspace(0,1,11),weights=w,histtype='step',linewidth=2,label=label(study))
    axes[1].set_xlabel('Empirical replicate support P1');axes[1].set_ylabel('Balanced pair fraction');axes[1].set_title('B  Replicate support is often uncertain',loc='left');axes[1].legend()
    caps.append(output(fig,'figure01_replicates_and_support','Moffatt lacks admitted paired replicate contrasts. Repeatability comes from the frozen failure audit; support histograms use the current matched historical training-pair roster.'))
    fig,axes=plt.subplots(1,2,figsize=(12,5));fig.subplots_adjust(bottom=.2,wspace=.4);w=pair_weights(frame,p)
    for ax,col,title in zip(axes,['q_P1','q_P2'],['A  Hard aggregate versus empirical votes','B  Hard aggregate versus smoothed votes']):
        h=ax.hist2d(p.q_H0,p[col],bins=[[-.1,.1,.9,1.1],np.linspace(0,1,11)],weights=w,cmap='Blues');ax.set_xticks([0,1]);ax.set_xlabel('H0 hard preference');ax.set_ylabel(col.replace('q_','')+' support');ax.set_title(title,loc='left');fig.colorbar(h[3],ax=ax,label='Balanced pair mass')
    caps.append(output(fig,'figure02_hard_and_soft_targets','H0/P1/P2 share candidates and sequence features; targets can differ due to replicate uncertainty and raw-versus-author processing. The Hraw control separates those explanations.'))
    bins=pd.read_csv(OUT/'reliability_bins.csv');fig,axes=plt.subplots(2,2,figsize=(11,9));fig.subplots_adjust(bottom=.1,hspace=.35,wspace=.3)
    for ax,study in zip(axes.ravel(),STUDIES):
        endpoint='aggregate' if study==STUDIES[2] else 'replicate';b=bins[bins.stage.eq('held_assay')&bins.dataset.eq(study)&bins.endpoint.eq(endpoint)];ax.plot([0,1],[0,1],'--',color='#aaa')
        for name in PRIMARY:
            s=b[b.model.eq(name)&b.weight.gt(0)];ax.plot(s.predicted,s.observed_support,'o-',label=name,color=COL[name])
        ax.set(xlim=(0,1),ylim=(0,1),xlabel='Predicted pair probability',ylabel='Observed preference support',title=label(study)+' — '+endpoint);ax.legend(fontsize=8)
    caps.append(output(fig,'figure03_calibration','Fixed ten-bin reliability curves. Moffatt uses aggregate labels only and cannot establish replicated probability calibration. Pair probabilities do not imply absolute benefit over WT.'))
    fig,axes=plt.subplots(1,2,figsize=(14,5));fig.subplots_adjust(bottom=.18,wspace=.35);base=pd.read_csv(OLD/'strongest_simple_envelope.csv').set_index('dataset');ix=np.arange(4);width=.18
    for j,name in enumerate(PRIMARY):
        s=core[core.model.eq(name)].set_index('dataset').loc[STUDIES];axes[0].bar(ix+(j-1.5)*width,s.regret,width,color=COL[name],label=name)
    axes[0].scatter(ix,base.loc[STUDIES,'regret'],marker='D',color='black',s=24,label='Strongest simple');axes[0].set_xticks(ix,[label(s) for s in STUDIES]);axes[0].set_ylim(0,.65);axes[0].set_ylabel('Normalized candidate regret');axes[0].set_title('A  Whole-study decision performance',loc='left');axes[0].legend(fontsize=8,ncol=2)
    gains=pd.read_csv(OUT/'per_assay_gains.csv')
    for j,name in enumerate(PRIMARY[1:]):
        s=gains[gains.model.eq(name)].set_index('dataset').loc[STUDIES];axes[1].bar(ix+(j-1)*.24,s.gain_vs_H0,.24,label=name,color=COL[name])
    axes[1].axhline(0,color='black',linewidth=.7);axes[1].set_xticks(ix,[label(s) for s in STUDIES]);axes[1].set_ylabel('H0 regret − soft-model regret');axes[1].set_title('B  Every gain and harm remains visible',loc='left');axes[1].legend(fontsize=8)
    caps.append(output(fig,'figure04_transfer_and_gains','Lower regret and positive gain are better. Primary supervision methods share the fixed interaction_3 representation and original study/component balance. A pooled gain alone cannot pass.'))
    fig,ax=plt.subplots(figsize=(14,5));fig.subplots_adjust(bottom=.27);ordered=pd.concat([core[core.dataset.eq(s)].set_index('model').loc[PRIMARY].reset_index() for s in STUDIES],ignore_index=True);bottom=np.zeros(len(ordered))
    for col,color,name in [('unavoidable_wrong','#aaa','All candidates wrong'),('avoidable_wrong','#b84b40','Avoidable wrong'),('neutral_only_alternative_wrong','#d5ab57','Only neutral alternatives')]:ax.bar(np.arange(len(ordered)),ordered[col],bottom=bottom,color=color,label=name);bottom+=ordered[col]
    ax.set_xticks(np.arange(len(ordered)),[label(s)+'\n'+m for s,m in zip(ordered.dataset,ordered.model)],fontsize=8);ax.set_ylim(0,1);ax.set_ylabel('Wrong-direction fraction');ax.set_title('Wrong recommendations are retained under uncertainty');ax.legend(fontsize=9)
    caps.append(output(fig,'figure05_wrong_direction','Stacked categories sum to overall wrong direction. Replicate ambiguity overlaps these categories and is reported separately, never used to erase errors.'))
    fig,axes=plt.subplots(1,2,figsize=(13,6));fig.subplots_adjust(bottom=.2,wspace=.4)
    for name in PRIMARY[1:]:
        s=gains[gains.model.eq(name)].set_index('dataset').loc[available];axes[0].plot(rr.ordering_agreement,s.gain_vs_H0,'o-',label=name,color=COL[name])
    axes[0].axhline(0,color='#888',linewidth=.7);axes[0].set_xlabel('Replicate ordering agreement');axes[0].set_ylabel('Held-assay gain over H0');axes[0].set_title('A  Reliability versus benefit: three assays',loc='left');axes[0].legend()
    p3g=gains[gains.model.eq('P3')].set_index('dataset')
    for study,xpos in zip(available,rr.ordering_agreement):axes[0].annotate(label(study),(xpos,p3g.loc[study,'gain_vs_H0']),xytext=(5,7),textcoords='offset points',fontsize=8)
    sm=core.groupby('model').regret.mean().reindex(PRIMARY+SECONDARY);axes[1].barh(sm.index,sm.values,color=[COL.get(n,'#999') for n in sm.index]);axes[1].invert_yaxis();axes[1].axvline(.468,color='#b84b40',linestyle='--',label='Gate macro threshold');axes[1].set_xlim(0,.65);axes[1].set_xlabel('Equal-study macro regret');axes[1].set_title('B  Prespecified secondary models',loc='left');axes[1].legend(fontsize=8)
    caps.append(output(fig,'figure06_reliability_and_secondary','The reliability association has n=3 and is not mechanistic proof. Secondary variants cannot rescue a failed primary supervision gate.'))
    raw=pd.read_csv(OUT/'matched_reproducibility_summary.csv');fig,ax=plt.subplots(figsize=(12,5));fig.subplots_adjust(bottom=.18);ix=np.arange(3)
    for j,name in enumerate(PRIMARY):
        s=raw[raw.model.eq(name)].set_index('dataset').loc[available];ax.bar(ix+(j-2)*.15,s.model_regret,.15,label=name,color=COL[name])
    reference=raw[raw.model.eq('H0')].set_index('dataset').loc[available];ax.bar(ix+2*.15,reference.replicate_regret,.15,label='Other measured replicates',color='#8752a1');ax.axhline(.5,color='black',linestyle='--',label='Uniform');ax.set_xticks(ix,[label(s) for s in available]);ax.set_ylim(0,.7);ax.set_ylabel('Regret on identical omitted-replicate targets');ax.set_title('Empirical decision reproducibility and sequence-model performance');ax.legend(fontsize=8,ncol=3)
    caps.append(output(fig,'figure07_matched_reproducibility','All bars use matched candidate subsets and raw held-replicate targets. The measured-replicate reference is neither deployable nor a theoretical maximum.'))
    jsave(OUT/'figure_captions.json',caps);fig,axes=plt.subplots(4,2,figsize=(16,19))
    for ax,item in zip(axes.ravel(),caps):ax.imshow(plt.imread(ART/(item['figure']+'.png')));ax.axis('off')
    axes.ravel()[-1].axis('off');fig.tight_layout();b=io.BytesIO();fig.savefig(b,format='png',dpi=120);save(ART/'figure_contact_sheet.png',b.getvalue());plt.close(fig);print('Rendered seven figures covering all nine requested topics.',flush=True)
if __name__=='__main__':run()
