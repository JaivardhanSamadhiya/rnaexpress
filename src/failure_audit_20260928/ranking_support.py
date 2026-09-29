"""Post-diagnostic refinement: exclude parent-constant additive features from OOD flags."""
from .run import *
from src.cross_assay_20260927.models import row_weights

def run():
    assert readj(OUT/'verification_receipt.json')['status']=='PASS';frozen()
    idx=pd.read_csv(OLD/'model_row_index.csv');f=pd.read_csv(ART/'canonical_interventions.csv',low_memory=False).set_index('intervention_id').loc[idx.intervention_id].reset_index();core=f.primary_eligible.to_numpy();schema=readj(OLD/'feature_schema.json')['columns'];rows=[];details=[]
    with np.load(ART/'features.npz') as archive:xs={name:archive[name] for name in MODELS}
    for study in sorted(f[core].dataset.unique()):
        te=core&f.dataset.eq(study).to_numpy();tr=purge(f,core&f.dataset.ne(study).to_numpy(),te);test=f[te].reset_index(drop=True);w=row_weights(test)
        for model in MODELS:
            a,b=xs[model][tr],xs[model][te];low=a.min(axis=0);high=a.max(axis=0);outside=(b<low-1e-12)|(b>high+1e-12)
            block=pd.DataFrame(b);groups=block.groupby(test.parent_context_id)
            active=(groups.transform('max')-groups.transform('min')).to_numpy()>1e-12
            assert active.shape==outside.shape
            # These features are exactly parent-constant in every admitted assay.
            assert not active[:,schema[model].index('log_parent_length')].any()
            flags=outside&active
            rows.append({'dataset':study,'model':model,'any_feature_outside_training_range':float(w@outside.any(axis=1)),'ranking_active_feature_outside_training_range':float(w@flags.any(axis=1))})
            freq=w@flags
            for j in np.flatnonzero(freq>0):details.append({'dataset':study,'model':model,'feature':schema[model][j],'macro_fraction_with_active_outside_feature':float(freq[j])})
    summary=csv('ranking_active_support_summary.csv',rows);detail=csv('ranking_active_support_features.csv',details)
    save(REP/'ranking_support_refinement.md',('''# Ranking-relevant support refinement

This additional descriptive check was motivated by the first diagnostic: several assays had 100% candidate-level range flags. It is explicitly post-diagnostic, not a newly preregistered result or a gate.

In a linear utility score, a feature constant across all candidates of one parent adds the same number to every candidate and cannot change their ordering. Therefore each original range flag is intersected with a within-parent nonzero-range mask for that saved feature. Parent-context interactions remain separate feature columns: they can vary even when their parent factor is constant. This is a necessary relevance check, not a proof that all retained shifts cause a model error. Aggregate with the original component/context/candidate weights.

'''+table(summary)+'''

The large unqualified range flags must not be presented as proof of severe ranking-domain mismatch. Neither qualified nor unqualified flags measure how far a candidate lies outside the training joint distribution, and coordinate-wise range coverage cannot establish adequate joint support. Detailed affected dimensions remain in `ranking_active_support_features.csv`. No model or threshold changed, and no new outcome source was opened.
''').encode())
    jsave(OUT/'ranking_support_receipt.json',{'status':'PASS','executed_code_sha256':sha256(Path(__file__)),'comparisons':len(rows),'parent_constant_length_excluded_in_all_comparisons':True,'post_diagnostic_refinement':True,'new_model_fits':0})
    print(summary.to_string(index=False))

if __name__=='__main__':run()
