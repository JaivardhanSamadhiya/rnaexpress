import numpy as np
import pandas as pd
import pytest
from src.mechanism_v2.evaluation import decision_metrics,pair_comparison,context_values,paired_component_bootstrap,holm_adjust


def test_metric_direction_and_lexical_ties():
    rows=pd.DataFrame({'dataset':['a']*3,'component':['u']*3,'decision_set_id':['d']*3,
        'candidate_id':['c','b','a'],'localization_effect':[0.,1.,2.]})
    metrics,_=decision_metrics(rows,np.zeros(3))
    assert metrics.selected_candidate.tolist()==['a','a']
    assert metrics.regret.tolist()==[0.,1.]
    assert metrics['rank'].tolist()==[1.,0.]


def test_bootstrap_keeps_cross_source_components_together():
    records=[]
    for source in ['a','b']:
        for g in range(8):
            for direction in ['increase','decrease']:
                records.append({'dataset':source,'component':f'g{g}','decision_set_id':f'{source}_{g}',
                    'direction':direction,'rank_gain':g/100,'regret_gain':2*g/100})
    paired=pd.DataFrame(records)
    audit,samples=paired_component_bootstrap(paired,100,2)
    assert audit['components']==8 and audit['eligible']
    np.testing.assert_allclose(samples['regret_gain'],2*samples['rank_gain'])
    other=paired_component_bootstrap(paired,100,2)[1]
    np.testing.assert_array_equal(samples['rank_gain'],other['rank_gain'])


def test_holm_is_monotone_and_bounded():
    np.testing.assert_allclose(holm_adjust([.04,.01,.03]),[.06,.03,.06])
    with pytest.raises(ValueError):holm_adjust([np.nan])


def test_comparison_rejects_unmatched_test_sets():
    rows=pd.DataFrame({'dataset':['a']*3,'component':['u']*3,'decision_set_id':['d']*3,
        'candidate_id':['c','b','a'],'localization_effect':[0.,1.,2.]})
    metrics,_=decision_metrics(rows,np.zeros(3))
    with pytest.raises(ValueError):pair_comparison(metrics,metrics.iloc[:1])
    altered=rows.copy();altered.loc[0,'candidate_id']='different'
    with pytest.raises(ValueError,match='identities'):pair_comparison(metrics,decision_metrics(altered,np.zeros(3))[0])
    altered=rows.copy();altered.loc[0,'localization_effect']=-1
    with pytest.raises(ValueError,match='outcomes'):pair_comparison(metrics,decision_metrics(altered,np.zeros(3))[0])
