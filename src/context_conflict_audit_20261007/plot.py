"""Publication figure from committed descriptive outputs only; no fits."""
from pathlib import Path
from collections import Counter
import hashlib, io, json, os, sys, tempfile, subprocess
import numpy as np
import pandas as pd

ROOT=Path('D:/rnaexpress')
NS='context_conflict_audit_20261007'
OUT=ROOT/'artifacts'/NS
RESULTS=ROOT/'results'/NS
LIB=ROOT/'data/interim/research_20260921/plot_runtime'
os.environ['MPLCONFIGDIR']=str(Path(tempfile.gettempdir())/'rnaexpress_context_conflict_mpl')
sys.path.append(str(LIB))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter,MaxNLocator
from .audit import check_plan,sha


def persist(path,payload):
    assert path.resolve().is_relative_to(OUT.resolve())
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and path.read_bytes()!=payload:
        assert '--replace-unfrozen-render' in sys.argv, 'Preserve '+str(path)
        assert path.name in {'observed_context_conflict.png','observed_context_conflict.svg','plot_manifest.json'}
        tracked=subprocess.run(['git','ls-files','--error-unmatch',path.relative_to(ROOT).as_posix()],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        assert tracked.returncode==1, 'Never replace tracked rendering'
        path.write_bytes(payload)
    elif not path.exists(): path.write_bytes(payload)


def main():
    check_plan()
    summary=json.loads((RESULTS/'summary.json').read_text(encoding='utf8'))
    replay=json.loads((RESULTS/'replay.json').read_text(encoding='utf8'))
    assert replay['status']=='PASS independent scalar brute-force replay'
    assert sha(RESULTS/'summary.json')==replay['summary_sha256']
    assert sha(RESULTS/'menus.csv')==replay['saved_menu_sha256']
    data=pd.read_csv(RESULTS/'menus.csv',float_precision='round_trip')
    assert len(data)==2408 and data.biological_component.nunique()==187
    assert set(data.dataset)=={'mikl_gse173098'}
    assert len(data)==summary['studies']['mikl_gse173098']['menus']
    assert summary['coverage']['moffatt_gse334718']['exact_shared_menus']==0
    component_sizes=Counter(data.biological_component)
    weight=np.asarray([1/(187*component_sizes[c]) for c in data.biological_component])
    assert abs(weight.sum()-1)<1e-12
    regret=data.minimum_pooled_regret.to_numpy(float)
    order=np.argsort(regret,kind='stable')
    sorted_values,sorted_weights=regret[order],weight[order]
    unique,inverse=np.unique(sorted_values,return_inverse=True)
    steps=np.cumsum(np.bincount(inverse,weights=sorted_weights))
    assert abs(steps[-1]-1)<1e-12
    mean=float(np.dot(weight,regret))
    assert abs(mean-summary['studies']['mikl_gse173098']['component_weighted_minimum_pooled_regret'])<1e-12
    exact_zero=int(data.exact_zero_feasible.sum());conflict=int(data.numerical_conflict.sum())
    assert (exact_zero,conflict)==(881,1527) and exact_zero+conflict==len(data)
    weighted_conflict=float(np.dot(weight,data.numerical_conflict.astype(float)))
    assert abs(weighted_conflict-summary['studies']['mikl_gse173098']['component_weighted_numerical_conflict_fraction'])<1e-12
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.titlesize':13,'axes.labelsize':11,
                         'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.8,
                         'svg.fonttype':'none','svg.hashsalt':NS,'savefig.facecolor':'white'})
    fig=plt.figure(figsize=(13.5,6.4),facecolor='white')
    grid=fig.add_gridspec(1,2,left=.075,right=.965,bottom=.275,top=.72,width_ratios=[1.45,1],wspace=.3)
    ax=fig.add_subplot(grid[0,0]);bars=fig.add_subplot(grid[0,1])
    blue='#245B78';green='#3C8268';amber='#B57529';dark='#23333D';grey='#697880'
    fig.text(.075,.935,'Observed cross-cell choice conflicts',fontsize=22,fontweight='bold',color=dark)
    fig.text(.075,.886,'Outcome-informed menu oracle · descriptive only · not a predictor or noise floor',fontsize=12,color=grey)
    fig.text(.075,.825,'Mikl CAD / Neuro-2a: 2,408 identical parent + candidate menus across all 187 biological components',fontsize=12,color=dark)
    ax.step(np.r_[0.,unique],np.r_[0.,steps],where='post',color=blue,linewidth=2.3)
    ax.scatter([0],[steps[0]],s=26,color=blue,zorder=5)
    ax.set_xlim(-.008,.508);ax.set_ylim(0,1.015)
    ax.set_xticks(np.arange(0,.501,.1));ax.set_yticks(np.arange(0,1.001,.2));ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_xlabel('Relaxed observed minimum pooled regret')
    ax.set_ylabel('Cumulative biological-component weight')
    ax.set_title('A   Component-weighted distribution',loc='left',fontweight='bold',pad=14)
    ax.grid(axis='y',color='#E2E8EB',linewidth=.7);ax.set_axisbelow(True)
    ax.text(.265,.15,f'Weighted mean: {mean:.3f}\nEqual weight per component;\nequal menu weight within component',fontsize=10.5,color=dark,
            bbox={'boxstyle':'round,pad=.55','facecolor':'#F3F6F7','edgecolor':'none'})
    ax.text(.02,.80,f'{(1-weighted_conflict):.1%} of component weight\nhas simultaneous zero regret',fontsize=10,color=blue)
    ax.text(.498,.035,'Constant scores: 0.5',ha='right',fontsize=9.5,color=grey)
    x=np.arange(2);counts=[exact_zero,conflict]
    bars.bar(x,counts,width=.55,color=[green,amber])
    bars.set_xticks(x,['Simultaneous\nexact zero','Observed\nconflict'])
    bars.set_ylim(0,1850);bars.set_yticks([0,500,1000,1500]);bars.yaxis.set_major_locator(MaxNLocator(integer=True,nbins=4))
    bars.set_ylabel('Raw menu count (unweighted)')
    bars.set_title('B   Raw menu counts',loc='left',fontweight='bold',pad=14)
    bars.grid(axis='y',color='#E2E8EB',linewidth=.7);bars.set_axisbelow(True)
    for position,count in zip(x,counts):
        bars.text(position,count+55,f'{count:,}\n({count/len(data):.1%} of menus)',ha='center',fontsize=11,color=dark)
    fig.text(.075,.177,'Coverage: 13,760 / 13,781 Mikl measurements; 187 / 187 components. Nine unmatched contexts excluded.',fontsize=11,color=dark)
    fig.text(.075,.135,'Observed conflicts occur in 171 / 187 components. Numerical conflict threshold: minimum regret > 10⁻¹².',fontsize=11,color=dark)
    fig.text(.075,.093,'Moffatt: 0 exact shared GFP / firefly menus; all six parent pairs excluded. No Moffatt outcome calculation.',fontsize=11,color=grey)
    fig.text(.075,.047,'Menu-wise independent optimization is a relaxed empirical bound; sampling noise and assay context remain unresolved.',fontsize=10.5,color=grey)
    files={}
    for extension in ['png','svg']:
        target=OUT/('observed_context_conflict.'+extension)
        stream=io.BytesIO()
        metadata={'Software':'matplotlib'} if extension=='png' else {'Date':'2026-10-07','Creator':'RNAexpress descriptive audit'}
        fig.savefig(stream,format=extension,dpi=300,metadata=metadata)
        payload=stream.getvalue();persist(target,payload);files[str(target.relative_to(ROOT))]=hashlib.sha256(payload).hexdigest()
    plt.close(fig)
    receipt={'status':'RENDERED; visual inspection pending','figure_kind':'component-weighted ECDF plus unweighted raw counts',
             'complete_mature_RNA_claim':False,'prediction_claim':False,'noise_floor_claim':False,'model_fits':False,
             'protected_outcomes_read':False,'weighted_mean_regret':mean,'weighted_conflict_fraction':weighted_conflict,
             'raw_exact_zero_menus':exact_zero,'raw_conflict_menus':conflict,'components':187,'Moffatt_exact_menus':0,
             'matplotlib_version':matplotlib.__version__,'python':sys.executable,'files_sha256':files,
             'inputs_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [RESULTS/'menus.csv',RESULTS/'summary.json',RESULTS/'replay.json',Path(__file__)]}}
    persist(OUT/'plot_manifest.json',(json.dumps(receipt,indent=2,sort_keys=True)+'\n').encode())
    print(json.dumps({'status':receipt['status'],'files':list(files),'weighted_mean':mean},indent=2))


if __name__=='__main__': main()
