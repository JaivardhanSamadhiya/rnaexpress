"""Static scientific figures from saved frozen development outputs."""
from .common import *
import sys,io
sys.path.insert(0,str(ROOT/'data/interim/research_20260921/plot_runtime'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
LABEL={'astrocyte_gse330741':'Astrocyte','mikl_gse173098':'Mikl','moffatt_gse334718':'Moffatt','srle':'SRLE','sirloin':'SIRLOIN'}
COL={'astrocyte_gse330741':'#2980b9','mikl_gse173098':'#29775c','moffatt_gse334718':'#b36730','srle':'#8752a1'}
FOOT='Exposed development only | 4 studies | unequal biological breadth | equal-study/component macro metrics | no new independent test'
def output(fig,name,caption):
    fig.text(.01,.01,FOOT,fontsize=8,color='#555555')
    for ext in ('png','svg'):
        buf=io.BytesIO();fig.savefig(buf,format=ext,dpi=180,bbox_inches='tight',metadata={'Date':None} if ext=='svg' else {'Software':'RNA cross-assay development'});data=buf.getvalue()
        if ext=='svg':data=('\n'.join(line.rstrip() for line in data.decode().splitlines())+'\n').encode()
        save(ART/(name+'.'+ext),data)
    plt.close(fig);return {'figure':name,'caption':caption}
def run():
    frozen();plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.hashsalt':'cross-assay-20260927'})
    comp=pd.read_csv(ART/'model_comparison.csv');gate=readj(OUT/'gate_verdict.json');leader=gate['selected_model'] or gate['descriptive_leader_not_validated'];counts=pd.read_csv(OUT/'primary_counts.csv');studies=config()['core_studies'];caps=[]
    f=pd.read_csv(ART/'canonical_interventions.csv',low_memory=False);f=f[f.primary_eligible]
    fig,axes=plt.subplots(1,2,figsize=(13,5));fig.subplots_adjust(bottom=.18,wspace=.38)
    ax=axes[0];ax.axis('off');ax.set_title('A  Four exposed biological systems',loc='left',fontweight='bold')
    lines=[('SRLE','Nucleus / cytoplasm','1 HBB reporter'),('Astrocyte','SN input / cortex input','7 parents / 2 genes'),('Mikl','Neurite / soma','2,417 parents / 187 genes'),('Moffatt','Neurite / soma','6 parents / 2 reporters')]
    for i,(name,endpoint,breadth) in enumerate(lines):
        ax.text(0,.85-i*.23,name,fontweight='bold',fontsize=13);ax.text(.25,.85-i*.23,endpoint);ax.text(.25,.77-i*.23,breadth,color='#555555')
    ax=axes[1]
    for study in studies:
        hist=f[f.dataset.eq(study)].substitution_count.value_counts(normalize=True).reindex(range(1,7),fill_value=0);ax.plot(hist.index,hist.values,'o-',label=LABEL[study],color=COL[study])
    ax.set_title('B  Physical substitution counts',loc='left',fontweight='bold');ax.set_xlabel('Changed nucleotide positions');ax.set_ylabel('Fraction of candidate measurements');ax.set_xticks(range(1,7));ax.legend(fontsize=9)
    caps.append(output(fig,'figure01_systems_and_edits','Primary candidates have 1–6 changed bases; span may be larger. Repeated cell/reporter measurements are not independent experiments. All inputs are development-exposed.'))
    core=comp[comp.stage.eq('held_assay')];pivot=core.pivot(index='model',columns='dataset',values='regret').reindex(columns=studies)
    fig,axes=plt.subplots(1,2,figsize=(14,7));fig.subplots_adjust(left=.19,bottom=.18,wspace=.45)
    ax=axes[0];im=ax.imshow(pivot.to_numpy(),cmap='viridis_r',vmin=0,vmax=1,aspect='auto');ax.set_yticks(range(len(pivot)),pivot.index);ax.set_xticks(range(4),[LABEL[s] for s in studies]);ax.set_title('A  Every held-study model: regret',loc='left');fig.colorbar(im,ax=ax,shrink=.7)
    for i in range(len(pivot)):
        for j in range(4):ax.text(j,i,f'{pivot.iloc[i,j]:.3f}',ha='center',va='center',fontsize=8,color='white' if pivot.iloc[i,j]>.55 else 'black')
    gain=pd.read_csv(OUT/'per_assay_baseline_gains.csv');gp=gain.pivot(index='model',columns='dataset',values='regret_gain').reindex(columns=studies);ax=axes[1];lim=max(.05,abs(gp.to_numpy()).max());im=ax.imshow(gp.to_numpy(),cmap='RdBu',vmin=-lim,vmax=lim,aspect='auto');ax.set_yticks(range(len(gp)),gp.index);ax.set_xticks(range(4),[LABEL[s] for s in studies]);ax.set_title('B  Gain over strongest simple envelope',loc='left');fig.colorbar(im,ax=ax,shrink=.7)
    for i in range(len(gp)):
        for j in range(4):ax.text(j,i,f'{gp.iloc[i,j]:+.3f}',ha='center',va='center',fontsize=8)
    caps.append(output(fig,'figure02_held_assay_comparison','Regret is lower-is-better; gain is positive-is-better. Every held assay is visible. The conservative baseline envelope chooses the best simple comparator within each study solely for evaluation.'))
    fig,axes=plt.subplots(1,2,figsize=(13,5));fig.subplots_adjust(bottom=.22,wspace=.4)
    stages=['within_assay','held_parent','held_assay'];ax=axes[0]
    for study in studies:
        s=comp[comp.dataset.eq(study)&comp.model.eq(leader)].set_index('stage');values=[s.loc[t,'regret'] if t in s.index else np.nan for t in stages];ax.plot(range(3),values,'o-',color=COL[study],label=LABEL[study])
    ax.set_xticks(range(3),['Within assay\noptimistic','Held parent\ncomponent folds','Held study']);ax.set_ylabel('Macro normalized regret');ax.set_title('A  Evaluation difficulty: '+leader,loc='left');ax.legend(fontsize=9)
    transfer=pd.read_csv(ART/'feature_transfer_matrix.csv').groupby('model')[['within_assay_gain_optimistic','held_parent_gain','held_assay_gain']].mean();ax=axes[1];im=ax.imshow(transfer,cmap='RdBu',vmin=-.15,vmax=.15,aspect='auto');ax.set_yticks(range(len(transfer)),transfer.index,fontsize=9);ax.set_xticks(range(3),['Within assay','Held parent','Held study']);ax.set_title('B  Feature gain versus composition',loc='left');fig.colorbar(im,ax=ax,shrink=.7)
    caps.append(output(fig,'figure03_generalization_gap','The displayed model is the fixed-composite descriptive leader, not a validated substitute if the gate failed. SRLE lacks independent held-parent evaluation and is not imputed. Feature gains average only eligible stages.'))
    fail=pd.read_csv(OUT/'failure_decomposition.csv');s=fail[fail.stage.eq('held_assay')&fail.model.eq(leader)].set_index('dataset').loc[studies];curves=pd.read_csv(OUT/'coverage_risk.csv')
    fig,axes=plt.subplots(1,2,figsize=(13,5));fig.subplots_adjust(bottom=.2,wspace=.4);ax=axes[0];bottom=np.zeros(4)
    for col,label,color in [('unavoidable_wrong','All candidates wrong','#aaa'),('avoidable_wrong','Avoidable wrong','#b94c40'),('neutral_only_alternative_wrong','Only neutral alternatives','#d7ac58')]:
        ax.bar(range(4),s[col],bottom=bottom,label=label,color=color);bottom+=s[col].to_numpy()
    ax.set_xticks(range(4),[LABEL[x] for x in studies]);ax.set_ylim(0,1);ax.set_ylabel('Wrong-direction fraction');ax.set_title('A  Full-coverage failure decomposition',loc='left');ax.legend(fontsize=8)
    ax=axes[1]
    for study in studies:
        c=curves[curves.stage.eq('held_assay')&curves.model.eq(leader)&curves.dataset.eq(study)].sort_values('coverage');ax.plot(c.coverage,c.avoidable_wrong,'o-',color=COL[study],label=LABEL[study]);fixed=c[c.threshold.eq(.8)];ax.scatter(fixed.coverage,fixed.avoidable_wrong,s=100,facecolors='none',edgecolors=COL[study])
    ax.set_xlim(0,1.03);ax.set_ylim(0,1);ax.set_xlabel('Coverage');ax.set_ylabel('Conditional avoidable wrong-direction risk');ax.set_title('B  Fixed confidence thresholds',loc='left');ax.legend(fontsize=9)
    caps.append(output(fig,'figure04_failure_and_abstention','Overall wrong-direction risk is retained alongside avoidable/unavoidable/neutral-only categories. Curves use a fixed threshold grid; open circles mark the predeclared 0.8 policy. Zero-coverage risk is missing, not zero.'))
    het=pd.read_csv(OUT/'feature_heterogeneity.csv');h=het[het.model.eq('delta2')&het.feature.str.startswith('delta_')].set_index('feature');h=h.reindex(columns=studies)
    resid=pd.read_csv(OUT/'universal_residual_contribution.csv');s=resid[resid.stage.eq('held_parent')]
    fig,axes=plt.subplots(1,2,figsize=(13,7));fig.subplots_adjust(left=.12,bottom=.16,wspace=.5);ax=axes[0];lim=max(abs(h.to_numpy()).max(),.001);im=ax.imshow(h,cmap='RdBu_r',vmin=-lim,vmax=lim,aspect='auto');ax.set_yticks(range(len(h)),h.index,fontsize=9);ax.set_xticks(range(4),[LABEL[x] for x in studies]);ax.set_title('A  Separately fitted short-word effects',loc='left');fig.colorbar(im,ax=ax,shrink=.7,label='Training-scale-removed coefficient')
    ax=axes[1];ix=np.arange(len(s));ax.bar(ix-.18,s.universal_only_regret,.36,color='#888',label='Universal only');ax.bar(ix+.18,s.full_score_regret,.36,color='#297fa6',label='+ assay residual');ax.set_xticks(ix,[LABEL.get(v,v) for v in s.dataset]);ax.set_ylabel('Held-parent normalized regret');ax.set_title('B  Residual contribution in known studies',loc='left');ax.legend(fontsize=9)
    caps.append(output(fig,'figure05_feature_heterogeneity','Coefficient sign reversals limit universality; regularized correlated coefficients are not molecular mechanisms. Residual contributions are allowed only for known exposed training studies, never whole-study transfer.'))
    size=pd.read_csv(OUT/'size_locality_metrics.csv');family=comp[comp.stage.eq('family_transfer')&comp.model.eq('kmer123')];domain=comp[comp.stage.eq('held_domain')&comp.model.eq('kmer123')]
    fig,axes=plt.subplots(1,2,figsize=(13,5));fig.subplots_adjust(bottom=.23,wspace=.4);ax=axes[0]
    for study in studies:
        s=size[size.model.eq(leader)&size.dataset.eq(study)].set_index('stage');vals=[s.loc['sensitivity_'+b,'regret'] if 'sensitivity_'+b in s.index else np.nan for b in ['1','2-3','4-6']];ax.plot(range(3),vals,'o-',label=LABEL[study],color=COL[study])
    ax.set_xticks(range(3),['1 base','2–3 bases','4–6 bases']);ax.set_ylabel('Regret on fixed size-defined candidate sets');ax.set_title('A  Edit-size sensitivity',loc='left');ax.legend(fontsize=9)
    ax=axes[1];x=np.arange(4);lo=core[core.model.eq('kmer123')].set_index('dataset').reindex(studies);fa=family.set_index('dataset').reindex(studies);do=domain.set_index('dataset').reindex(studies);ax.plot(x,lo.regret,'o-',label='Held study: all other studies');ax.plot(x,fa.regret,'s--',label='Same destination family only');ax.plot(x,do.regret,'^:',label='Different destination domain only');ax.set_xticks(x,[LABEL[s] for s in studies]);ax.set_ylabel('Normalized regret');ax.set_title('B  Destination-class transfer: kmer123',loc='left');ax.legend(fontsize=8)
    caps.append(output(fig,'figure06_edit_size_and_domain','Sensitivity subsets cannot replace the main gate. Nuclear SRLE has no same-family core training study; missing family performance remains missing. Different-domain transfer and same-family transfer are distinct hypotheses.'))
    bert=comp[comp.stage.eq('pretrained_restricted')];summary=core.groupby('model').regret.mean();fig,axes=plt.subplots(1,2,figsize=(13,5));fig.subplots_adjust(bottom=.2,wspace=.45)
    ax=axes[0];p=bert.pivot(index='dataset',columns='model',values='regret');ix=np.arange(len(p))
    for offset,name,color in [(-.18,'matched_kmer123','#888'),(.18,'frozen_bert_plus_kmer','#297fa6')]:ax.bar(ix+offset,p[name],.36,label=name,color=color)
    ax.set_xticks(ix,[LABEL[s] for s in p.index]);ax.set_ylabel('Held-study regret on matched contexts');ax.set_title('A  Frozen pretrained comparison',loc='left');ax.legend(fontsize=8)
    ax=axes[1];choices=['uniform','metadata','composition',leader];ax.bar(range(len(choices)),summary.loc[choices],color=['#aaa','#888','#666','#297fa6']);ax.set_xticks(range(len(choices)),choices,rotation=15,ha='right');ax.set_ylabel('Equal-study macro regret');ax.set_title('B  Gate: '+gate['status'],loc='left');ax.text(.02,.96,'Descriptive leader; not selected' if not gate['selected_model'] else 'Selected development model',transform=ax.transAxes,va='top',fontsize=9)
    ax.set_ylim(0,.62)
    caps.append(output(fig,'figure07_pretrained_and_verdict','The pretrained test is restricted to two studies and does not fulfill full-grid evidence. Lowest average regret alone is not the selection criterion; consistency and harm checks remain required.'))
    jsave(OUT/'figure_captions.json',caps)
    fig,axes=plt.subplots(4,2,figsize=(16,18))
    for ax,item in zip(axes.ravel(),caps):ax.imshow(plt.imread(ART/(item['figure']+'.png')));ax.axis('off')
    axes.ravel()[-1].axis('off');fig.tight_layout();buf=io.BytesIO();fig.savefig(buf,format='png',dpi=120);save(ART/'figure_contact_sheet.png',buf.getvalue());plt.close(fig)
    print('Rendered',len(caps),'figures and contact sheet.')
if __name__=='__main__':run()
