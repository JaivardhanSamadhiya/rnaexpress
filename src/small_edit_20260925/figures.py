"""Seven scientific figures from saved predictions and metrics; no fitting."""
from .common import *
import io
import sys
sys.path.insert(0,str(ROOT/'data/interim/research_20260921/plot_runtime'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

CELLS=('CAD','Neuro-2a'); BANDS=('1','2','3','4-6')
COLORS={'primary':'#246a88','delta_AU':'#bc633e','train_mean':'#777777','no_change':'#b7b7b7'}


def finish(fig,name,title,caption):
    fig.suptitle(title,fontsize=15,y=.99)
    fig.text(.015,.012,caption,fontsize=9,va='bottom')
    fig.tight_layout(rect=[0,.08,1,.95])
    for ext in ('png','svg'):
        stream=io.BytesIO(); fig.savefig(stream,format=ext,dpi=160,bbox_inches='tight')
        save(OUT/'figures'/(name+'.'+ext),stream.getvalue())
    plt.close(fig)


def run():
    plt.rcParams.update({'axes.spines.top':False,'axes.spines.right':False,'font.size':10})
    pred=pd.read_csv(OUT/'small_edit_predictions.csv')
    metrics=pd.read_csv(OUT/'effect_direction_metrics.csv',dtype={'edit_size_band':str})
    globalm=pd.read_csv(OUT/'global_prediction_metrics.csv',dtype={'edit_size_band':str})
    decisions=pd.read_csv(OUT/'small_edit_decisions.csv.gz',dtype={'edit_size_band':str})
    gm=pd.read_csv(OUT/'decision_gene_metrics.csv',dtype={'edit_size_band':str})
    dm=pd.read_csv(OUT/'decision_metrics.csv',dtype={'edit_size_band':str})
    secondary=pd.read_csv(OUT/'small_edit_secondary_predictions.csv')
    fig,axes=plt.subplots(2,2,figsize=(11,9))
    for ax,cell in zip(axes[0],CELLS):
        g=pred[pred.cell_type.eq(cell)&pred.edit_size_band.eq('4-6')]
        ax.hexbin(g.pred_primary,g.localization_change,gridsize=40,bins='log',mincnt=1,cmap='Blues')
        ax.set(title=f'Mikl {cell}: 4–6 substitutions',xlabel='Predicted Δ log2 neurite/soma',ylabel='Measured Δ log2 neurite/soma')
    for ax,rep in zip(axes[1],(1,2)):
        g=secondary[secondary.dataset.eq('srle')&secondary.model.eq('kmer123')&secondary.replicate.eq(rep)]
        ax.hexbin(g.predicted_score_difference,g.measured_effect,gridsize=35,bins='log',mincnt=1,cmap='Greens')
        ax.set(title=f'SRLE replicate {rep}: two-position swaps',xlabel='Fixed short-mer predicted Δ NRS',ylabel='Measured Δ NRS')
        limits=[min(ax.get_xlim()[0],ax.get_ylim()[0]),max(ax.get_xlim()[1],ax.get_ylim()[1])]
        ax.plot(limits,limits,'k--',lw=.8,alpha=.5)
    finish(fig,'01_predicted_vs_measured','Predicting changes: unseen genes and one shared reporter are different tasks',
        'Top: gene-held-out estimates on reused Mikl data. Bottom: original SRLE test-neighbor edges; related sequences and experiment shared.\nHexagons show log row counts, not independent biological units. SRLE is not a single-base or unseen-parent result.')
    fig,axes=plt.subplots(1,2,figsize=(11,5))
    for ax,cell in zip(axes,CELLS):
        for j,model in enumerate(('no_change','train_mean','delta_AU','primary')):
            g=metrics[metrics.context.eq(cell)&metrics.model.eq(model)].set_index('edit_size_band').loc[list(BANDS)]
            ax.errorbar(np.arange(4)+(j-1.5)*.13,g.rmse,yerr=[g.rmse-g.rmse_ci_low,g.rmse_ci_high-g.rmse],fmt='o',ms=4,capsize=2,label=model,color=COLORS[model])
        ax.set(xticks=range(4),xticklabels=BANDS,xlabel='Changed bases (substitutions)',ylabel='Gene-balanced RMSE',title=cell)
    axes[1].legend(fontsize=8)
    finish(fig,'02_performance_by_size','Small-edit effect error, without pooling edit sizes',
        '2,000 gene-bootstrap descriptive 95% intervals; fixed fitted models. Tier1 has only 13 variants/11 genes per cell.\nAll models train on <=6 substitutions; estimates are grouped development performance, not independent confirmation.')
    fig,axes=plt.subplots(1,2,figsize=(11,5))
    for ax,cell in zip(axes,CELLS):
        for j,model in enumerate(('delta_AU','primary')):
            g=metrics[metrics.context.eq(cell)&metrics.model.eq(model)].set_index('edit_size_band').loc[list(BANDS)]
            ax.errorbar(np.arange(4)+(j-.5)*.15,g.auroc,yerr=[g.auroc-g.auroc_ci_low,g.auroc_ci_high-g.auroc],fmt='o',capsize=3,label=model,color=COLORS[model])
        eligible=metrics[metrics.context.eq(cell)&metrics.model.eq('primary')].set_index('edit_size_band').loc[list(BANDS)].auroc_eligible_genes
        ax.set(xticks=range(4),xticklabels=[b+'\n'+str(n)+' genes' for b,n in zip(BANDS,eligible)],ylim=(-.05,1.08),ylabel='Gene-macro direction auROC',title=cell)
        ax.axhline(.5,color='gray',ls='--'); ax.legend()
    finish(fig,'03_direction_prediction','Direction discrimination is weak on measured small edits',
        'Only genes containing both positive and negative measured effects contribute to gene-macro auROC.\nThe single-base endpoint has ONE eligible gene: extreme points there cannot support a population claim. Global auROC is separately tabulated.')
    fig,axes=plt.subplots(2,3,figsize=(12,7))
    for row,cell in enumerate(CELLS):
        for col,b in enumerate(('2','3','4-6')):
            ax=axes[row,col]; samples=[]
            for model in ('delta_AU','primary'):
                samples.append(gm[gm.context.eq(cell)&gm.edit_size_band.eq(b)&gm.model.eq(model)].regret.to_numpy())
            ax.boxplot(samples,tick_labels=['ΔAU','Primary'],showfliers=True)
            ax.axhline(.5,color='gray',ls='--'); ax.set(title=f'{cell}, {b} bases; {len(samples[0])} genes',ylim=(-.03,1.03),ylabel='Gene-mean selection regret')
    finish(fig,'04_selection_regret','Held-out-gene candidate selection does not show a consistent advantage',
        'Each candidate set uses the same parent, cell and edit band; >=2 candidates and nonzero measured range.\nDirections and parents are averaged within genes. Dashed line: exact uniform mean for symmetric directions. Two-base sets have only four genes.')
    fig,axes=plt.subplots(1,2,figsize=(12,6))
    names=list(metrics.model.unique())
    for ax,cell in zip(axes,CELLS):
        g=metrics[metrics.context.eq(cell)&metrics.edit_size_band.eq('4-6')].set_index('model').reindex(names)
        ax.barh(range(len(names)),g.rmse,color=[COLORS.get(n,'#a9b9bd') for n in names])
        ax.set(yticks=range(len(names)),yticklabels=names,xlabel='Gene-balanced RMSE (lower is better)',title=cell)
        ax.invert_yaxis()
    finish(fig,'05_all_baselines','All fixed model families and controls: four-to-six-base effects',
        'Every nonconstant model uses the same inner alpha search. Primary selection uses training folds only.\nThe primary selected delta123 in all ten outer fits; no post-test winner replaces it. All other size bands are in the metric tables.')
    fig,axes=plt.subplots(2,2,figsize=(12,8))
    for col,cell in enumerate(CELLS):
        g=decisions[decisions.context.eq(cell)&decisions.edit_size_band.eq('4-6')&decisions.model.eq('primary')]
        parents=g.groupby('parent')[['regret','wrong_direction']].mean()
        axes[0,col].hist(parents.regret,bins=np.linspace(0,1,21),color=COLORS['primary'])
        axes[0,col].set(title=f'{cell}: all {len(parents)} eligible parents',xlabel='Parent-mean regret',ylabel='Parent count')
        genes=gm[gm.context.eq(cell)&gm.edit_size_band.eq('4-6')].pivot(index='gene',columns='model',values='regret').sort_index()
        gain=genes.delta_AU-genes.primary
        axes[1,col].bar(range(len(gain)),gain,color=np.where(gain>=0,'#2b7b67','#bd625a'))
        axes[1,col].axhline(0,color='black',lw=.7)
        axes[1,col].set(xlabel='All genes in lexical order',ylabel='Regret improvement over ΔAU',title='Benefit and failure across genes')
    finish(fig,'06_per_parent_performance','Performance varies across parents; all eligible units retained',
        'Parents are not independent when they share a gene. Inferential intervals use genes; histograms expose parent-level variation.\nNo favorable parent subset is selected. Every candidate rank and selected edit is supplied in small_edit_candidate_selection.csv.')
    fig,axes=plt.subplots(1,2,figsize=(11,5))
    for ax,cell in zip(axes,CELLS):
        g=dm[dm.context.eq(cell)&dm.model.eq('primary')].set_index('edit_size_band').loc[['2','3','4-6']]
        x=np.arange(3)
        ax.bar(x,g.correct_direction,label='Desired direction',color='#2a7e72')
        ax.bar(x,g.wrong_direction,bottom=g.correct_direction,label='Wrong direction',color='#b85f56')
        ax.bar(x,g.zero_change,bottom=g.correct_direction+g.wrong_direction,label='Zero measured change',color='#bcbcbc')
        ax.set(xticks=x,xticklabels=['2','3','4-6'],xlabel='Changed bases',ylabel='Gene-balanced choice fraction',ylim=(0,1),title=cell)
        for j,wrong in enumerate(g.wrong_direction): ax.text(j,.98,f'{wrong:.1%} wrong',ha='center',va='top',color='white',fontsize=9)
    axes[1].legend(loc='upper center',bbox_to_anchor=(.5,-.17),ncol=1,fontsize=8)
    finish(fig,'07_failure_analysis','Wrong-direction choices remain frequent in held-out genes',
        'Both requested directions retained; fixed primary procedure; measured change relative to parent.\nWrong direction is an assay decision failure, not a claim about toxicity or biological safety. Single-base candidate sets are unavailable.')
    jsave('figure_receipt.json',{'figures':7,'source':'saved fixed predictions/metrics only; no fitting',
        'files':{p.relative_to(ROOT).as_posix():sha256(p) for p in sorted((OUT/'figures').glob('*'))}})
    print('Generated seven PNG/SVG figures')


if __name__=='__main__': run()
