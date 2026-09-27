"""Summarize every already-fixed control's choice behavior without refitting."""
from .common import *

def run():
    frame=pd.read_csv(ART/'control_predictions.csv',dtype={'group':str},float_precision='round_trip')
    controls=list(frame.columns[6:]);rows=[]
    for parent,g in frame.groupby('parent'):
        g=g.sort_values('candidate');group=g.group.iloc[0]
        for direction in (-1,1):
            for name in controls:
                p=direction*g[name].to_numpy();ix=int(np.argmax(p))
                a=direction*g.rep1_delta.to_numpy();b=direction*g.rep2_delta.to_numpy()
                row={'parent':parent,'direction':direction,'group':group,'control':name,'selected':g.candidate.iloc[ix],'wrong_both':float(a[ix]<-TOL and b[ix]<-TOL)}
                for target in ('published','rep1','rep2'):
                    y=direction*g[target+'_delta'].to_numpy();row[target+'_regret']=(y.max()-y[ix])/np.ptp(y);row[target+'_correct_direction']=float(y[ix]>TOL)
                rows.append(row)
    frame=pd.DataFrame(rows);csvsave(ART/'control_decisions.csv',frame)
    csvsave(OUT/'control_decision_summary.csv',group_summary(frame,['published_regret','rep1_regret','rep2_regret','published_correct_direction','rep1_correct_direction','rep2_correct_direction','wrong_both'],['control']))
    metrics=pd.read_csv(OUT/'control_metrics.csv');null=metrics[metrics.control.str.contains('label_null')&metrics.target.eq('published')]
    jsave(OUT/'control_summary_receipt.json',{'status':'PASS','all_control_decisions':len(frame),'label_null_runs':len(null),'label_null_mse_gain_min':null.mse_improvement.min(),'label_null_mse_gain_max':null.mse_improvement.max(),'label_null_mse_gain_mean':null.mse_improvement.mean(),'nulls_exceeding_frozen_2mer':int((null.mse_improvement>=.10192902960964512).sum()),'interpretation':'32 retained descriptive nulls, not independent confirmation or calibrated permutation p-value'})
    print(readj(OUT/'control_summary_receipt.json'))

if __name__=='__main__':run()
