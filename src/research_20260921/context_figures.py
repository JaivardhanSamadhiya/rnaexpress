"""Render measured context-calibration results; no data/model refitting."""
from .common import ROOT,write_new,write_json,sha256
import sys,io,json
sys.path.insert(1,str(ROOT/'data/interim/research_20260921/plot_runtime'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def run():
    out=ROOT/'results/research_20260921'
    discovery=json.loads((out/'context_calibration_development.json').read_text())
    curve=json.loads((out/'context_learning_curve.json').read_text())['budgets']
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.hashsalt':'rnaddress-20260922'})
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    names=['target_kmer','composition','random3']; labels=['Target-only kmer','Composition','Random 3 features']
    for i,name in enumerate(names):
        v=discovery['comparisons'][name];lower,upper=v['paired_component_ci95']
        axes[0].errorbar(v['gain'],i,xerr=[[v['gain']-lower],[upper-v['gain']]],fmt='o',capsize=4,
                         color='#176c8b' if v['passes'] else '#bd653b')
    axes[0].axvline(0,color='gray',linewidth=1)
    axes[0].set(yticks=range(3),yticklabels=labels,xlabel='Regret improvement from transfer (95% CI)',
                title='Frozen development test: gate FAILED')
    axes[0].invert_yaxis();axes[0].grid(axis='x',alpha=.2)
    budgets=[16,64,256]
    for name,label,color in [('stack','Three-source calibration','#176c8b'),('target_kmer','Target-only kmer','#bd653b'),
                             ('sibling_uncalibrated','Similar-context source; no calibration','#538e55')]:
        values=[np.mean(list(curve[str(b)]['regret'][name].values())) for b in budgets]
        axes[1].plot(range(3),values,'o-',label=label,color=color)
    axes[1].axhline(.5,color='gray',linestyle=':',label='Uniform-choice expectation')
    axes[1].set(xticks=range(3),xticklabels=budgets,xlabel='Attempted target-label budget',
                ylabel='Normalized regret (lower is better)',title='Source-only exploratory learning curve')
    axes[1].legend(fontsize=8,loc='upper left');axes[1].grid(alpha=.2)
    fig.suptitle('RNA context matching is promising; calibration superiority remains unconfirmed',fontsize=13)
    fig.text(.02,.025,'Left: 20 development groups; 22 confirmation groups remain closed. Right: 58 evaluable source groups; reused-data diagnostic.\nFragment selection in one MCF7 reporter study. Not minimal-edit validation. Missing outcomes reduce usable calibration labels.',fontsize=8)
    fig.tight_layout(rect=[0,.1,1,.94])
    hashes={}
    for suffix in ['png','svg']:
        buf=io.BytesIO();fig.savefig(buf,format=suffix,dpi=180,metadata={'Date':None} if suffix=='svg' else {})
        p=out/('context_calibration_summary_v2.'+suffix);write_new(p,buf.getvalue());hashes[p.name]=sha256(p)
    plt.close(fig)
    write_json(out/'context_figure_receipt_v2.json',{'matplotlib':matplotlib.__version__,'numpy':np.__version__,
                                               'files':hashes,'fits_performed':False})

if __name__=='__main__':run()
