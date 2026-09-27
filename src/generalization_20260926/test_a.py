from .common import *
from .evaluation import evaluate

def run():
    assert_frozen();assert not (OUT/'test_a_verdict.json').exists(),'Test A already evaluated; preserve it'
    receipt=readj(OUT/'outcome_access_receipt.json');assert sha256(ART/'GSE330741_mapped_outcomes.csv')==receipt['mapped_outcome_sha256']
    frame=pd.read_csv(ART/'GSE330741_mapped_outcomes.csv',float_precision='round_trip');prefit=pd.read_csv(ART/'GSE330741_prefit_predictions_without_outcomes.csv',float_precision='round_trip')
    assert frame.element.tolist()==prefit.element.tolist();models=config()['test_a_models']
    predictions=prefit[models].copy();export=frame.copy()
    for col in models+['delta_'+w for w in WORDS]:export[col]=prefit[col]
    export['model_prediction']=predictions[config()['test_a_primary_model']]
    export['predicted_direction']=sign(export.model_prediction);export['observed_direction']=sign(export.observed_delta)
    export['candidate_rank_increase']=np.nan;export['candidate_rank_decrease']=np.nan
    for parent,g in export[export.qc_status.eq('VERIFIED')].groupby('parent_id'):
        for direction,label in [(1,'increase'),(-1,'decrease')]:
            ordered=g.assign(score=direction*g.model_prediction).sort_values(['score','element'],ascending=[False,True]);export.loc[ordered.index,'candidate_rank_'+label]=np.arange(1,len(g)+1)
    csvsave(ART/'GSE330741_zero_shot_predictions.csv',export)
    eligible=frame[frame.qc_status.eq('VERIFIED')]
    evaluate(eligible,predictions.loc[eligible.index],'test_a',config()['test_a_primary_model'],config()['test_a_required_baselines'])

if __name__=='__main__':run()
