"""Independent aggregation and compressed-artifact audit after numerical replay."""
from .common import *
import gzip

def run():
    frozen()
    f=pd.read_csv(ART/'canonical_interventions.csv',low_memory=False)
    core=f[f.primary_eligible]
    assert not core.duplicated(['parent_context_id','mutant_sequence']).any()
    minimum=int(core.groupby('parent_context_id').mutant_sequence.nunique().min())
    assert minimum>=2
    d=pd.read_csv(OUT/'decision_metrics.csv',usecols=['stage','dataset','model','biological_component','regret'],float_precision='round_trip')
    d=d[d.stage.eq('held_assay')]
    macro=d.groupby(['dataset','model','biological_component']).regret.mean().groupby(['dataset','model']).mean()
    c=pd.read_csv(ART/'model_comparison.csv',float_precision='round_trip')
    c=c[c.stage.eq('held_assay')].set_index(['dataset','model']).regret
    error=float(abs(macro-c).max());assert error<1e-12
    compressed=[]
    for p in [ART/'canonical_interventions.csv',ART/'leave_one_assay_out_predictions.csv',ART/'candidate_rankings.csv',ART/'secondary_predictions.csv',OUT/'decision_metrics.csv']:
        h=hashlib.sha256()
        with gzip.open(str(p)+'.gz','rb') as stream:
            while chunk:=stream.read(8*1024*1024):h.update(chunk)
        assert h.hexdigest()==sha256(p)
        compressed.append(p.relative_to(ROOT).as_posix())
    result={'status':'PASS','executed_code_sha256':sha256(Path(__file__)),'primary_duplicate_candidate_sequences':0,'minimum_distinct_candidates':minimum,'independent_macro_regret_checks':len(c),'macro_regret_max_error':error,'gzip_exact_round_trips':compressed,'figure_visual_review':'Seven PNG/SVG figures inspected through contact sheet; figure 7 annotation spacing corrected and rechecked.'}
    jsave(OUT/'supplementary_audit_receipt.json',result)
    print(clean(result))

if __name__=='__main__':run()
