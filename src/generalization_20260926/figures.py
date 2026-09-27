"""Scientific figures from saved evidence only; no fitting or new tests."""
from .common import *
import io,sys
sys.path.insert(0,str(ROOT/'data/interim/research_20260921/plot_runtime'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

FOOT='Astrocytes: 3,984 SNPs | 7 parents | 5 nonoverlap components | 2 genes | partially exposed | descriptive intervals'
BLUE='#2474a6';GREEN='#287d61';RED='#af493c';GRAY='#727782'
def output(fig,name,caption):
    fig.text(.01,.015,FOOT,fontsize=8,color='#555555')
    for ext in ('png','svg'):
        buf=io.BytesIO();fig.savefig(buf,format=ext,dpi=180,bbox_inches='tight',metadata={'Date':None} if ext=='svg' else {'Software':'RNA generalization'})
        payload=buf.getvalue()
        if ext=='svg':payload=('\n'.join(line.rstrip() for line in payload.decode().splitlines())+'\n').encode()
        save(ART/(name+'.'+ext),payload)
    plt.close(fig);return {'figure':name,'caption':caption}
def short(p):return p.replace('slc1a2.1_','Slc1a2 ').replace('sparc_','Sparc ')
def run():
    assert_frozen();plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.hashsalt':'generalization-20260926'})
    ap=pd.read_csv(OUT/'test_a_parent_metrics.csv');bp=pd.read_csv(OUT/'test_b_parent_metrics.csv');captions=[]
    fig,axes=plt.subplots(1,3,figsize=(14,4.8));fig.subplots_adjust(bottom=.21,wspace=.5)
    ax=axes[0];ax.set_title('A  Preserved SRLE result',loc='left',fontweight='bold')
    ax.errorbar([10.1929],[0],xerr=[[9.1918],[9.8007]],fmt='o',color=GREEN,capsize=5);ax.axvline(0,color=GRAY,lw=1);ax.set_xlim(-5,24);ax.set_ylim(-1,1);ax.set_yticks([]);ax.set_xlabel('Edit-effect MSE gain over composition (%)')
    ax.text(.04,.1,'Strict composition holdout + two-edit purge\nTwo-position swaps in 6 nt\nOne HBB reporter; class-level interval',transform=ax.transAxes,fontsize=10)
    ax=axes[1];ax.axis('off');ax.set_title('B  External mutation design',loc='left',fontweight='bold')
    ax.text(.02,.84,'190-nt parent → one-base mutant',fontsize=13,color=BLUE)
    ax.text(.02,.69,'8 designed parents / 4,553 SNPs\n1 author poor-cloning exclusion\n7 admitted parents / 3,984 SNPs\n2 genes / 5 nonoverlap components\n14 matched replicate pool labels',linespacing=1.6,va='top')
    ax.text(.02,.09,'Target: SN/cortex log2 enrichment\nMutant minus exact WT',fontsize=11)
    ax=axes[2];ax.axis('off');ax.set_title('C  Generalization hierarchy',loc='left',fontweight='bold')
    for i,(label,status,color) in enumerate([('1  Strict SRLE prediction','SUPPORTED',GREEN),('2  Incremental method replication','INCOMPLETE',RED),('3  Zero-shot parameter transfer','NOT ESTABLISHED',RED),('4  Multi-system candidate validation','NOT ESTABLISHED',RED)]):
        ax.text(0,.85-i*.23,label,fontsize=11);ax.text(0,.76-i*.23,status,color=color,fontweight='bold')
    captions.append(output(fig,'figure01_design_and_claims','Historical SRLE interval is across composition classes in one reporter, not biological replicates. The new assay admits seven parent elements and does not pass either primary generalization criterion.'))
    frame=pd.read_csv(ART/'GSE330741_zero_shot_predictions.csv');frame=frame[frame.qc_status.eq('VERIFIED')]
    fig,axes=plt.subplots(2,4,figsize=(14,7));fig.subplots_adjust(hspace=.45,wspace=.35,bottom=.13)
    for ax,(parent,g) in zip(axes.ravel(),frame.groupby('parent_id')):
        rho=ap[ap.parent_id.eq(parent)&ap.model.eq('srle_2mer_full')].spearman.iloc[0]
        ax.scatter(g.srle_2mer_full,g.observed_delta,s=7,alpha=.32,color=BLUE,rasterized=True)
        ax.axhline(0,color=GRAY,lw=.7);ax.axvline(0,color=GRAY,lw=.7);ax.set_title(short(parent)+f'\nρ = {rho:.3f}');ax.set_xlabel('Frozen source prediction');ax.set_ylabel('Measured mutant − WT')
    ax=axes.ravel()[-1];ax.axis('off');ax.text(.02,.8,'ZERO-SHOT PRIMARY\n\nMean parent ρ = 0.051\n95% descriptive interval\n[−0.003, 0.139]\n\nComposition baseline: 0.067\n\nFrozen criterion failed',va='top',linespacing=1.5,color=RED)
    captions.append(output(fig,'figure02_zero_shot_scatter','Every admitted SNP is plotted, separated by parent. Prediction and measurement scales represent different endpoints and are not calibrated. No pooled-SNP significance claim is made.'))
    fig,axes=plt.subplots(1,3,figsize=(15,5.2));fig.subplots_adjust(left=.16,right=.98,bottom=.18,wspace=.48)
    parents=sorted(bp.parent_id.unique());yy=np.arange(len(parents))
    for ax,df,models,title in [(axes[0],ap,['srle_composition','srle_2mer_full'],'A  Zero-shot ranks'),(axes[1],bp,['simple_full','simple_full_delta2'],'B  Held-parent ranks')]:
        for model,color in zip(models,[GRAY,BLUE]):
            vals=df[df.model.eq(model)].set_index('parent_id').loc[parents,'spearman'];ax.plot(vals,yy,'o',label=model,color=color)
        ax.axvline(0,color='black',lw=.8);ax.set_title(title,loc='left');ax.set_xlabel('Within-parent Spearman');ax.set_yticks(yy, [short(p) for p in parents] if ax==axes[0] else []);ax.legend(fontsize=8,loc='lower right')
    ax=axes[2];simple=bp[bp.model.eq('simple_full')].set_index('parent_id').loc[parents,'spearman'];order=bp[bp.model.eq('simple_full_delta2')].set_index('parent_id').loc[parents,'spearman'];gain=order-simple
    ax.barh(yy,gain,color=[GREEN if x>0 else RED for x in gain]);ax.axvline(0,color='black',lw=.8);ax.set_yticks([]);ax.set_title('C  Increment from 2-mers',loc='left');ax.set_xlabel('Paired Spearman increment');ax.text(.02,.98,'Mean +0.013 [−0.022, 0.068]\nExact block p = 0.3125',transform=ax.transAxes,va='top',fontsize=9)
    captions.append(output(fig,'figure03_parent_rank_generalization','B removes the whole held parent and every overlapping parent from training. Four parents improve with 2-mer context, three worsen; the paired increment fails the frozen criterion.'))
    am=pd.read_csv(OUT/'test_a_decision_metrics.csv');bm=pd.read_csv(OUT/'test_b_decision_metrics.csv')
    fig,axes=plt.subplots(1,3,figsize=(15,5.4));fig.subplots_adjust(left=.17,bottom=.19,wspace=.65)
    for ax,df,models,title in [(axes[0],am,['uniform','srle_composition','srle_2mer_full','srle_2mer_order_only','srle_kmer123_full'],'A  Zero-shot candidate regret'),(axes[1],bm,['uniform','simple_full','position','delta2','simple_full_delta2','simple_full_delta2_delta3'],'B  Held-parent candidate regret')]:
        s=df.set_index('model').loc[models];yy=np.arange(len(s));ax.errorbar(s.regret,yy,xerr=np.array([s.regret-s.regret_ci_low,s.regret_ci_high-s.regret]),fmt='o',color=BLUE,capsize=4);ax.set_yticks(yy,models,fontsize=9);ax.axvline(.5,color=GRAY,ls='--');ax.set_xlabel('Normalized regret (lower is better)');ax.set_title(title,loc='left',fontsize=11);ax.set_xlim(.25,.65)
    ax=axes[2];s=bm.set_index('model').loc[['uniform','simple_full','simple_full_delta2']];ax.bar([0,1,2],s.wrong_direction,color=[GRAY,RED,BLUE]);ax.set_xticks([0,1,2],['Uniform','Simple','Simple\n+ 2-mer']);ax.set_ylim(0,.8);ax.set_ylabel('Wrong-direction fraction');ax.set_title('C  14 directional decisions',loc='left',fontsize=11)
    for i,v in enumerate(s.wrong_direction):ax.text(i,v+.025,f'{v:.1%}',ha='center')
    captions.append(output(fig,'figure04_candidate_choice','Both directions are averaged within parent. B primary regret improves in all seven parents versus uniform; 5/14 selections still have the wrong measured sign. Bootstrap bars use five overlap components; the simple-baseline exact regret p is 0.0625.'))
    fig,axes=plt.subplots(1,3,figsize=(14,4.6));fig.subplots_adjust(bottom=.22,wspace=.55)
    co=pd.read_csv(OUT/'cross_assay_coefficients.csv');x=co.srle_raw.to_numpy();y=co.astrocyte_mean_raw.to_numpy();v=max(abs(x).max(),abs(y).max())
    for ax,vals,title in [(axes[0],x,'A  Frozen SRLE 2-mer'),(axes[1],y,'B  Mean astrocyte 2-mer fit')]:
        im=ax.imshow((vals-vals.mean()).reshape(4,4),cmap='RdBu_r',vmin=-v,vmax=v);ax.set_xticks(range(4),list('ACGT'));ax.set_yticks(range(4),list('ACGT'));ax.set_xlabel('Second base');ax.set_ylabel('First base');ax.set_title(title,loc='left');fig.colorbar(im,ax=ax,shrink=.75,label='Count coefficient')
    ax=axes[2];g=pd.read_csv(OUT/'leave_gene_out_parent_metrics.csv').groupby(['held_gene','model']).spearman.mean().unstack();ix=np.arange(len(g));ax.bar(ix-.18,g.simple_full,.36,color=GRAY,label='Simple');ax.bar(ix+.18,g.simple_full_delta2,.36,color=BLUE,label='+ 2-mer');ax.set_xticks(ix,g.index);ax.set_ylabel('Mean parent Spearman');ax.set_title('C  Held-gene sensitivity',loc='left');ax.legend(fontsize=9);ax.text(.02,-.17,'Fixed α=10; two gene folds only',transform=ax.transAxes,va='top',fontsize=9);ax.set_ylim(0,.21)
    captions.append(output(fig,'figure05_cross_assay_features','Grand-mean centered coefficient correlation is −0.471. Removing row/column additive terms gives interaction r=0.457 (descriptive feature-label p=0.0913). The plots do not establish a shared mechanism. Gene holdout is secondary and only two folds exist.'))
    selected=pd.read_csv(OUT/'primary_selected_candidates.csv');fig,axes=plt.subplots(1,2,figsize=(13,6));fig.subplots_adjust(left=.2,bottom=.17,wspace=.6)
    for ax,stage,title in [(axes[0],'test_a','A  Every zero-shot choice'),(axes[1],'test_b','B  Every held-parent choice')]:
        g=selected[selected.stage.eq(stage)].sort_values(['parent_id','direction']);signed=g.direction*g.observed_delta;ax.barh(np.arange(len(g)),signed,color=[GREEN if v>0 else RED for v in signed]);ax.axvline(0,color='black',lw=.8);ax.set_yticks(np.arange(len(g)),[short(p)+(' ↓' if d==-1 else ' ↑') for p,d in zip(g.parent_id,g.direction)],fontsize=8);ax.set_title(title,loc='left');ax.set_xlabel('Measured effect oriented to requested direction')
    captions.append(output(fig,'figure06_successes_and_failures','Every deterministic primary selection is shown, without selecting favorable examples. Positive bars satisfy the requested measured direction; negative bars fail. Seven A and five B choices fail.'))
    jsave(OUT/'figure_captions.json',captions)
    fig,axes=plt.subplots(3,2,figsize=(16,14))
    for ax,item in zip(axes.ravel(),captions):ax.imshow(plt.imread(ART/(item['figure']+'.png')));ax.axis('off')
    fig.tight_layout();buf=io.BytesIO();fig.savefig(buf,format='png',dpi=130);save(ART/'figure_contact_sheet.png',buf.getvalue());plt.close(fig)
    print('Rendered',len(captions),'figures in PNG/SVG and contact sheet.')

if __name__=='__main__':run()
