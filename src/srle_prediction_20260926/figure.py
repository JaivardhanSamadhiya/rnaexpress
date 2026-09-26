from .core import *
import io
import sys
sys.path.insert(0,str(ROOT/'data/interim/research_20260921/plot_runtime'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec


def run():
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.hashsalt':'srle-prediction-20260926'})
    effect=pd.read_csv(OUT/'edit_effect_predictions.csv')
    metrics=pd.read_csv(OUT/'prediction_metrics.csv')
    decisions=pd.read_csv(OUT/'decision_metrics.csv')
    examples=pd.read_csv(OUT/'example_choices.csv')
    labels={'composition':'Composition','1mer':'1-mer (same)','2mer':'2-mer','3mer':'3-mer','kmer123':'1–3-mer','position_additive':'Position additive','position_pair':'Position pair'}
    colors={'position_pair':'#af563b','kmer123':'#397493','2mer':'#518466','uniform':'#888888'}
    fig=plt.figure(figsize=(16,13));grid=GridSpec(3,2,figure=fig,height_ratios=[1.12,1,.76],hspace=.48,wspace=.29)
    ag=grid[0,0].subgridspec(1,2,wspace=.32)
    for index,model in enumerate(('position_pair','2mer')):
        ax=fig.add_subplot(ag[0,index]);g=effect[(effect.scheme=='purged_composition_holdout')&(effect.model==model)]
        ax.hexbin(g.published_delta,g.predicted_delta,gridsize=32,mincnt=1,cmap='Blues',linewidths=0)
        lim=max(np.abs(g.published_delta).max(),np.abs(g.predicted_delta).max())*1.03
        ax.plot([-lim,lim],[-lim,lim],color='#999999',ls='--',lw=1);ax.set_xlim(-lim,lim);ax.set_ylim(-lim,lim)
        ax.set_xlabel('Measured Δ NRS (log2 units)');ax.set_ylabel('Predicted Δ NRS' if index==0 else '')
        m=metrics[(metrics.kind=='edit_delta')&(metrics.scheme=='purged_composition_holdout')&(metrics.target=='published')&(metrics.model==model)].iloc[0]
        ax.set_title(('A  Purged held-out edits\n' if index==0 else 'Prespecified simple control\n')+labels[model],loc='left',fontsize=11,fontweight='bold')
        ax.text(.04,.96,f'r = {m.pearson:.3f}\nRMSE = {m.rmse:.3f}\nR² = {m.r2:.3f}',transform=ax.transAxes,va='top',fontsize=9,
            bbox={'facecolor':'white','alpha':.85,'edgecolor':'none'})
    ax=fig.add_subplot(grid[0,1]);b=metrics[(metrics.kind=='edit_delta')&(metrics.scheme=='purged_composition_holdout')&(metrics.target=='published')].set_index('model').loc[list(MODELS)]
    xpos=np.arange(len(b));ax.bar(xpos,b.rmse,color=[colors.get(m,'#9cabb3') for m in b.index],width=.65)
    ax.errorbar(xpos,b.rmse,yerr=np.array([b.rmse-b.rmse_ci_low,b.rmse_ci_high-b.rmse]),fmt='none',ecolor='#333333',capsize=3,lw=1)
    ax.axhline(b.loc['composition','rmse'],color='#555555',ls='--',lw=1)
    ax.set_xticks(xpos,[labels[m] for m in b.index],rotation=30,ha='right');ax.set_ylabel('Edit-effect RMSE (lower is better)')
    ax.set_title('B  All controls under the strictest holdout',loc='left',fontsize=12,fontweight='bold')
    ax=fig.add_subplot(grid[1,0])
    for model in ('position_pair','kmer123','2mer'):
        d=decisions[(decisions.model==model)&(decisions.direction==0)].set_index('scheme').loc[list(SCHEMES)]
        ax.errorbar(np.arange(3),d.published_regret,yerr=[d.published_regret-d.published_regret_ci_low,d.published_regret_ci_high-d.published_regret],
                    color=colors[model],marker='o',capsize=3,label=labels[model])
    ax.axhline(.5,color='#888888',ls='--',label='Uniform choice');ax.axvspan(2.65,3.35,color='#eeeeee')
    ax.text(3,.31,'Unavailable:\none biological\nreporter context',ha='center',va='center',fontsize=9)
    ax.set_xlim(-.22,3.38);ax.set_ylim(.15,.6);ax.set_xticks(range(4),['Sequence\nholdout','Composition\nholdout','Purged\ncomposition','New biological\ncontext'])
    ax.set_ylabel('Candidate-choice regret (lower is better)');ax.legend(loc='lower left',ncol=2,fontsize=8)
    ax.set_title('C  Harder holdout, same candidate roster',loc='left',fontsize=12,fontweight='bold')
    dg=grid[1,1].subgridspec(1,2,width_ratios=[1,1],wspace=.34)
    models=['position_pair','kmer123','2mer','uniform'];d=decisions[(decisions.scheme=='purged_composition_holdout')&(decisions.direction==0)].set_index('model').loc[models]
    ax=fig.add_subplot(dg[0,0]);ypos=np.arange(4)
    ax.barh(ypos,d.rep1_correct_direction,color='#629b82',label='Correct')
    ax.barh(ypos,d.rep1_wrong_direction,left=d.rep1_correct_direction,color='#c17561',label='Wrong')
    ax.set_yticks(ypos,[labels.get(m,'Uniform') for m in models]);ax.invert_yaxis();ax.set_xlim(0,1);ax.set_xlabel('Fraction of choices');ax.legend(fontsize=8,loc='lower center',bbox_to_anchor=(.5,-.27),ncol=2)
    ax.set_title('D  Direction risk, purged test\nConstituent replicate 1',loc='left',fontsize=11,fontweight='bold')
    ax=fig.add_subplot(dg[0,1]);ax.errorbar(d.wrong_both,ypos,xerr=[d.wrong_both-d.wrong_both_ci_low,d.wrong_both_ci_high-d.wrong_both],fmt='o',color='#444444',capsize=3)
    ax.set_yticks(ypos,['']*4);ax.invert_yaxis();ax.set_xlim(.15,.46);ax.set_xlabel('Wrong in both: fraction')
    ax.set_title('Same choice, both\nconstituent replicates',fontsize=10)
    ax=fig.add_subplot(grid[2,:]);ax.axis('off');ax.set_title('E  Fixed-rule examples — primary pair model, purged holdout',loc='left',fontsize=12,fontweight='bold',pad=14)
    rows=[]
    for r in examples.itertuples():
        rows.append(['Median' if r.selection_rule=='median' else 'Median wrong-both', 'Increase' if r.direction==1 else 'Decrease',
            r.parent+' → '+r.selected,f'{r.predicted_delta:+.3f}',f'{r.published_measured_delta:+.3f}',f'{r.rep1_measured_delta:+.3f}',f'{r.rep2_measured_delta:+.3f}', 'Yes' if r.wrong_both else 'No'])
    table=ax.table(cellText=rows,colLabels=['Selection rule','Desired','Measured sequence pair','Predicted Δ','Published Δ','Replicate 1 Δ','Replicate 2 Δ','Wrong both?'],loc='upper center',cellLoc='center',colWidths=[.145,.085,.22,.10,.10,.11,.11,.095])
    table.auto_set_font_size(False);table.set_fontsize(9);table.scale(1,1.75)
    for (r,c),cell in table.get_celld().items():
        cell.set_edgecolor('#d5dadd')
        if r==0:cell.set_facecolor('#e5edf0');cell.set_text_props(weight='bold')
        elif rows[r-1][-1]=='Yes':cell.set_facecolor('#f7e7e1')
    ax.text(0,-.01,'Examples use prespecified median-regret rules, including failures; positive Δ means increased NRS, regardless of desired direction.',transform=ax.transAxes,fontsize=9)
    fig.suptitle('Predicting localization-related consequences of measured six-mer swaps',fontsize=17,y=.985)
    fig.text(.06,.944,'Two changed positions within a six-nucleotide window • 1,744 overlapping candidate links • 592 anchors • one SRLE HBB reporter context',fontsize=10)
    fig.subplots_adjust(top=.90,bottom=.09,left=.07,right=.98)
    fig.text(.06,.025,'95% intervals resample composition classes (60 for edits), conditional on this experiment and fitted models.\nAll sources were previously exposed. Constituent-replicate agreement is not independent biological validation; full measurement provenance remains partial.',fontsize=9)
    hashes={}
    for extension in ('png','svg'):
        buffer=io.BytesIO();fig.savefig(buffer,format=extension,dpi=170,bbox_inches='tight',metadata={'Date':None} if extension=='svg' else {})
        path=ART/('srle_small_edit_prediction_figure.'+extension);save(path,buffer.getvalue());hashes[path.name]=sha256(path)
    plt.close(fig);jsave(OUT/'figure_receipt.json',{'files':hashes,'examples_rule':'frozen median and median wrong-both; primary pair model retained'})


if __name__=='__main__':run()
