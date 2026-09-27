"""Static figures exclusively from saved predictions and saved summaries."""
from .common import *
import io,sys
sys.path.insert(0,str(ROOT/'data/interim/research_20260921/plot_runtime'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

LABEL={'composition':'Composition / zero','1mer':'1-mer','2mer':'2-mer','3mer':'3-mer','kmer123':'1–3-mer','position_pair':'Position pair','position_additive':'Position additive','uniform':'Uniform'}
COLOR={'2mer':'#287c61','kmer123':'#2766a4','position_pair':'#b45237','composition':'#777777','uniform':'#aaaaaa'}
FOOT='SRLE • one HBB reporter context • exposed exploratory analysis • composition-class uncertainty is not biological replication'

def output(fig,name,caption):
    fig.text(.01,.01,FOOT,fontsize=8,color='#555555')
    for ext in ('png','svg'):
        buf=io.BytesIO();fig.savefig(buf,format=ext,dpi=210,bbox_inches='tight',metadata={'Date':None} if ext=='svg' else {'Software':'SRLE synthesis'})
        save(ART/(name+'.'+ext),buf.getvalue())
    plt.close(fig)
    return {'figure':name,'caption':caption,'png':str((ART/(name+'.png')).relative_to(ROOT)),'svg':str((ART/(name+'.svg')).relative_to(ROOT))}

def run():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.hashsalt':'srle-synthesis-20260926'})
    captions=[]
    feat=pd.read_csv(ART/'edit_features.csv',dtype={'group':str});models=pd.read_csv(OUT/'model_comparison.csv').set_index('model')
    decisions=pd.read_csv(ART/'recommendation_decisions.csv',dtype={'group':str});summary=pd.read_csv(OUT/'recommendation_summary.csv').set_index('model')
    fig,axes=plt.subplots(1,3,figsize=(13,4.5),gridspec_kw={'width_ratios':[1.15,1.1,1.3]});fig.subplots_adjust(bottom=.2,wspace=.4)
    example=feat[~feat.delta2_zero].sort_values(['parent','candidate']).iloc[0]
    ax=axes[0];ax.axis('off');ax.set_title('A  Precisely defined intervention',loc='left',fontweight='bold')
    ax.text(.04,.76,example.parent+'  →  '+example.candidate,fontsize=19,fontfamily='monospace')
    ax.text(.04,.47,'Two unequal bases exchanged\nChanged positions: '+str(example.changed_positions_1based)+'\nWindow: 6 nucleotides\nΔ base counts = (0, 0, 0, 0)',linespacing=1.8)
    ax.text(.04,.10,f'Measured Δ NRS: {example.published_delta:+.3f}\nFrozen 2-mer prediction: {example.pred_2mer:+.3f}')
    ax=axes[1];cols=[c for c in feat if c.startswith('delta_2mer_') and abs(example[c])>0]
    ax.bar([c.split('_')[-1] for c in cols],[example[c] for c in cols],color='#287c61');ax.axhline(0,color='#777777',lw=.8)
    ax.set_title('B  Changes in adjacency counts',loc='left',fontweight='bold');ax.set_ylabel('Edited − parent count')
    ax=axes[2];ax.axis('off');ax.set_title('C  Candidate recommendation',loc='left',fontweight='bold')
    ax.text(.04,.86,'Parent + complete candidate set\n↓\nFrozen sequence scores\n↓\nRank for increase or decrease\n↓\nReveal measured effects',fontsize=12,linespacing=1.3,va='top')
    ax.text(.04,.08,'1,744 links • 592 local anchors\n60 composition classes • 1 context\n87 links leave 2-mer counts unchanged',fontsize=10)
    captions.append(output(fig,'figure01_task','Lexical first nonzero Δ2-mer example, not selected for outcome. DNA T encoding denotes the local RNA sequence. Only two positions change. Outcomes are revealed after frozen scoring; the original roster itself was historically coverage/outcome-conditioned.'))
    effects=pd.read_csv(ART/'edit_prediction_diagnostics.csv');fig,axes=plt.subplots(1,3,figsize=(13,4.9),sharex=True,sharey=True);fig.subplots_adjust(bottom=.19,wspace=.22)
    limit=max(abs(effects.published_delta).max(),abs(effects[effects.model.isin(['composition','2mer','position_pair'])].predicted_delta).max())*1.03
    for ax,model in zip(axes,('composition','2mer','position_pair')):
        g=effects[effects.model.eq(model)];ax.scatter(g.published_delta,g.predicted_delta,s=7,alpha=.22,color=COLOR[model],rasterized=True)
        ax.plot([-limit,limit],[-limit,limit],color='#888888',ls='--',lw=1);ax.set_xlim(-limit,limit);ax.set_ylim(-limit,limit)
        m=models.loc[model];ax.set_title(LABEL[model],fontweight='bold');ax.set_xlabel('Measured Δ NRS (log2 score units)')
        ax.text(.04,.96,f'RMSE {m.rmse:.3f}\nMSE reduction {m.mse_reduction:+.1%}',transform=ax.transAxes,va='top',bbox={'facecolor':'white','alpha':.85,'edgecolor':'none'})
    axes[0].set_ylabel('Predicted Δ NRS');fig.suptitle('Figure 2 • Strict purge: simple prediction survives; pair magnitudes fail',fontsize=13)
    captions.append(output(fig,'figure02_quantitative','All 1,744 directed links. Same axes expose pair-model overdispersion. Composition predicts zero effect. Fixed original held-out scores; no recalibration.'))
    fig,axes=plt.subplots(1,2,figsize=(13,5.6));fig.subplots_adjust(bottom=.2,wspace=.32)
    order=['composition','1mer','2mer','3mer','kmer123','position_additive','position_pair'];m=models.loc[order];ax=axes[0]
    ax.barh(np.arange(len(m)),m.mse_reduction*100,color=[COLOR.get(k,'#99a9b4') for k in order])
    ax.errorbar(m.mse_reduction*100,np.arange(len(m)),xerr=np.array([m.mse_reduction-m.mse_reduction_ci_low,m.mse_reduction_ci_high-m.mse_reduction])*100,fmt='none',color='#333333',capsize=3)
    ax.set_yticks(np.arange(len(m)),[LABEL[k] for k in order]);ax.invert_yaxis();ax.axvline(0,color='#555555',lw=.8);ax.set_xlabel('Edit-effect MSE reduction vs zero (%)');ax.set_title('A  Frozen feature complexity',loc='left',fontweight='bold')
    c=pd.read_csv(OUT/'control_metrics.csv');c=c[c.target.eq('published')];null=c[c.control.str.contains('label_null')];ax=axes[1]
    ax.scatter(null.mse_improvement*100,np.linspace(-.18,.18,len(null)),s=23,color='#a4a4a4',label='All 32 label nulls')
    for y,name,label in [(1,'random16','Random 16 features'),(2,'position_shuffled_2mer','Shuffled-position 2-mers')]:
        r=c[c.control.eq(name)].iloc[0];ax.errorbar(r.mse_improvement*100,y,xerr=[[100*(r.mse_improvement-r.ci_low)],[100*(r.ci_high-r.mse_improvement)]],fmt='o',color='#777777',capsize=3)
    r=models.loc['2mer'];ax.errorbar(r.mse_reduction*100,3,xerr=[[100*(r.mse_reduction-r.mse_reduction_ci_low)],[100*(r.mse_reduction_ci_high-r.mse_reduction)]],fmt='o',color=COLOR['2mer'],capsize=3)
    ax.set_yticks([0,1,2,3],['32 label nulls','Random 16 features','Shuffled positions','Original 2-mers']);ax.axvline(0,color='#555555',lw=.8);ax.set_xlabel('Edit-effect MSE reduction vs zero (%)');ax.set_title('B  Fixed controls; no seed search',loc='left',fontweight='bold')
    captions.append(output(fig,'figure03_features_controls','Original 95% descriptive composition-class intervals. Every fixed label null displayed; jitter is deterministic display spacing, not data. Shuffled positions retain other order information and are a representation control.'))
    stable=pd.read_csv(OUT/'coefficient_stability.csv');stable=stable[stable.scheme.eq('purged_composition_holdout')].set_index('feature')
    contrib=pd.read_csv(OUT/'contribution_summary.csv').set_index('feature');order=contrib.index.tolist();fig,axes=plt.subplots(1,2,figsize=(13,6.3));fig.subplots_adjust(bottom=.15,wspace=.35)
    s=stable.loc[order];ax=axes[0];ax.errorbar(s.median_centered_coefficient,np.arange(16),xerr=np.array([s.median_centered_coefficient-s.q25,s.q75-s.median_centered_coefficient]),fmt='o',color='#287c61',capsize=3)
    ax.set_yticks(np.arange(16),order);ax.invert_yaxis();ax.axvline(0,color='#999999',lw=.8);ax.set_xlabel('Centered count coefficient: median and IQR');ax.set_title('A  Across 70 overlapping purged fits',loc='left',fontweight='bold')
    ax=axes[1];ax.barh(np.arange(16),contrib.absolute_contribution_share*100,color=['#287c61']*4+['#9fbbb0']*12);ax.set_yticks(np.arange(16),order);ax.invert_yaxis();ax.set_xlabel('Share of absolute centered contributions (%)');ax.set_title('B  CA, AC, TC, CT contribute 63%',loc='left',fontweight='bold')
    captions.append(output(fig,'figure04_order_structure','Coefficient IQRs describe overlapping fits, not confidence intervals. Centering all 16 weights preserves predictions because Δ2-mer counts sum to zero. Contributions depend on representation and covariance; they are not mechanisms. Boundary/interaction decomposition is saved separately.'))
    distribution=pd.read_csv(OUT/'regret_distribution.csv');fig,axes=plt.subplots(1,2,figsize=(12,4.9));fig.subplots_adjust(bottom=.2,wspace=.33)
    order=['uniform','composition','2mer','kmer123']
    for model in order:
        g=distribution[distribution.model.eq(model)].sort_values('regret');axes[0].step(g.regret,g.weight.cumsum()/g.weight.sum(),where='post',label=LABEL[model],color=COLOR.get(model),ls='--' if model=='composition' else '-')
    axes[0].set_xlabel('Normalized regret (0 best, 1 worst)');axes[0].set_ylabel('Cumulative decision probability');axes[0].legend(frameon=False);axes[0].set_title('A  Complete regret distributions',loc='left',fontweight='bold')
    m=summary.loc[order];axes[1].bar(np.arange(4),m.published_regret,color=[COLOR[k] for k in order]);axes[1].errorbar(np.arange(4),m.published_regret,yerr=np.array([m.published_regret-m.published_regret_ci_low,m.published_regret_ci_high-m.published_regret]),fmt='none',color='#333333',capsize=3)
    axes[1].set_xticks(np.arange(4),[LABEL[k] for k in order],rotation=15);axes[1].set_ylabel('Class-balanced mean regret');axes[1].set_ylim(0,.65);axes[1].set_title('B  Ranking improves over uniform',loc='left',fontweight='bold')
    captions.append(output(fig,'figure05_recommendation','ECDFs weight decisions equally; uniform is the exact within-set candidate mixture. Mean/interval panel weights composition classes equally. These are different explicit weighting conventions; the pooled median is zero for both sequence selectors, but worst-choice mass remains.'))
    fig,axes=plt.subplots(1,2,figsize=(13,5));fig.subplots_adjust(bottom=.2,wspace=.32);order=['uniform','2mer','kmer123','position_pair'];m=summary.loc[order]
    for j,(field,label,color) in enumerate([('published_correct_direction','Correct: published','#287c61'),('published_wrong_direction','Wrong: published','#bb7055'),('wrong_both','Wrong in both reps','#6c4c81')]):
        axes[0].bar(np.arange(4)+(j-1)*.23,m[field],width=.23,label=label,color=color)
    axes[0].set_xticks(np.arange(4),[LABEL[k] for k in order],rotation=15);axes[0].set_ylabel('Class-balanced fraction');axes[0].set_ylim(0,.75);axes[0].legend(fontsize=8,frameon=False);axes[0].set_title('A  Directional risk remains substantial',loc='left',fontweight='bold')
    bottom=np.zeros(4)
    for field,label,color in [('wrong_both_unavoidable','Every candidate wrong in both','#8a8a8a'),('wrong_both_ambiguous_alternative','Alternative avoids wrong-both','#ce9d61'),('wrong_both_correct_alternative','Both-correct alternative existed','#b45237')]:
        axes[1].bar(np.arange(4),m[field],bottom=bottom,label=label,color=color);bottom+=m[field].to_numpy()
    axes[1].set_xticks(np.arange(4),[LABEL[k] for k in order],rotation=15);axes[1].set_ylabel('Fraction of all decisions');axes[1].set_ylim(0,.55);axes[1].legend(fontsize=8,frameon=False);axes[1].set_title('B  Wrong-both decomposition',loc='left',fontweight='bold')
    captions.append(output(fig,'figure06_failures','Both directions, 1,184 decisions per selector. Correct/wrong published rates use the author target; wrong-both uses constituent raw replicates. The 16.6% forced-choice floor depends on the measured roster and does not establish a biological ceiling.'))
    sim=pd.read_csv(OUT/'similarity_performance.csv');fig,axes=plt.subplots(1,2,figsize=(12,4.9));fig.subplots_adjust(bottom=.2,wspace=.35)
    for ax,factor,title in zip(axes,['minimum_nearest_2mer_l1','minimum_nearest_3mer_l1'],['Nearest 2-mer count distance','Nearest 3-mer count distance']):
        for model,shift in [('2mer',-.05),('kmer123',0),('position_pair',.05)]:
            g=sim[sim.model.eq(model)&sim.distance_metric.eq(factor)].sort_values('distance')
            ax.errorbar(g.distance+shift,100*g.mse_improvement_vs_no_change,yerr=100*np.array([g.mse_improvement_vs_no_change-g.ci_low,g.ci_high-g.mse_improvement_vs_no_change]),fmt='o-',label=LABEL[model],color=COLOR[model],capsize=3)
        ax.set_xticks([4,6]);ax.axhline(0,color='#777777',ls='--',lw=1);ax.set_xlabel(title+' (minimum of endpoints)');ax.set_ylabel('MSE reduction vs zero (%)');ax.legend(fontsize=8,frameon=False)
    fig.suptitle('Figure 7 • All nearest Hamming and Levenshtein distances equal 3',fontsize=13)
    captions.append(output(fig,'figure07_similarity','Exact feature-distance levels, no selected cutoff. The 2-mer gain is 6.5% at distance 4 and 16.2% at distance 6. These correlated descriptive strata do not establish monotonic generalization, and sequence distances >3 are untested.'))
    examples=pd.read_csv(OUT/'representative_examples.csv');candidate=pd.read_csv(ART/'all_candidate_recommendations.csv');fig,axes=plt.subplots(2,2,figsize=(13,9));fig.subplots_adjust(bottom=.14,hspace=.6,wspace=.25)
    for ax,example in zip(axes.flat,examples.itertuples()):
        g=candidate[candidate.evaluation_split.eq('purged_composition_holdout')&candidate.model_name.eq('kmer123')&candidate.parent.eq(example.parent)&candidate.direction.eq(example.direction)].sort_values('candidate');xx=np.arange(len(g))
        for j,(field,label,color) in enumerate([('predicted_delta','Prediction','#2766a4'),('measured_delta','Published','#666666'),('rep1_delta','Replicate 1','#63917c'),('rep2_delta','Replicate 2','#c99558')]):ax.bar(xx+(j-1.5)*.19,g[field],width=.19,label=label,color=color)
        labels=[s+(' ★' if s==example.selected else '') for s in g.candidate];ax.set_xticks(xx,labels,rotation=12,fontfamily='DejaVu Sans Mono');ax.axhline(0,color='#777777',lw=.7);ax.set_ylabel('Candidate − parent Δ NRS')
        direction='Increase' if example.direction==1 else 'Decrease';ax.set_title(f'{direction} | {example.parent} | replicate {example.example_type}\nPublished regret {example.published_regret:.2f}; ★ chosen',fontsize=11,loc='left');ax.legend(fontsize=8,frameon=False,ncol=2)
    captions.append(output(fig,'figure08_examples','Predetermined median average replicate-regret examples within each correct-both/wrong-both direction subgroup. Selection was not optimized for the author aggregate, which can disagree with constituents. All candidates shown; a requested direction is not guaranteed by a forced ranking.'))
    cov=pd.read_csv(OUT/'confidence_coverage.csv');fig,axes=plt.subplots(2,2,figsize=(12,8));fig.subplots_adjust(bottom=.17,hspace=.35,wspace=.3)
    signals=['signal_margin','signal_directional_effect','signal_model_agreement','signal_feature_distance','signal_extrapolation']
    for i,model in enumerate(['2mer','kmer123']):
        for j,metric in enumerate(['published_regret','wrong_both']):
            ax=axes[i,j]
            for signal in signals:
                g=cov[cov.model.eq(model)&cov.signal.eq(signal)].sort_values('actual_coverage');ax.plot(g.actual_coverage*100,g[metric],marker='o',ms=4,label=signal.removeprefix('signal_').replace('_',' '))
            ax.set_title(LABEL[model]);ax.set_xlabel('Decision coverage (%)');ax.set_ylabel('Regret' if j==0 else 'Wrong in both replicates');ax.set_xticks([20,40,60,80,100])
    axes[0,0].legend(fontsize=8,frameon=False);fig.suptitle('Supplement • Fixed coverage curves are exploratory, not calibrated abstention')
    captions.append(output(fig,'figure09_confidence','All five prediction/design-only signals, both selectors, all five fixed coverages. Lexical ties can dominate coarse distance signals. Class composition changes with coverage; selected thresholds are not independently validated or deployed. Intervals and denominators are in confidence_coverage.csv.'))
    jsave(OUT/'figure_captions.json',captions)
    jsave(OUT/'figure_receipt.json',{'status':'PASS','required_figures':8,'supplemental_figures':1,'saved_data_only':True,'files':{p.relative_to(ROOT).as_posix():sha256(p) for p in ART.glob('figure*') if p.suffix in ('.png','.svg')}})
    print('Saved 8 required figures and 1 confidence supplement as PNG/SVG')

if __name__=='__main__':run()
