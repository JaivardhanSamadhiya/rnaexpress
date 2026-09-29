from .common import *
from .report import table

def run():
    frozen();assert readj(OUT/'verification_receipt.json')['status']=='PASS'
    checked=[]
    for p in [ART/'replicate_candidate_measurements.csv',ART/'replicate_pairwise_evidence.csv',ART/'pairwise_probabilities.csv',ART/'candidate_rankings.csv',OUT/'candidate_index.csv',OUT/'decision_metrics.csv',OUT/'predictions.csv',OUT/'matched_raw_replicate_decisions.csv']:
        h=hashlib.sha256()
        with gzip.open(str(p)+'.gz','rb') as stream:
            while block:=stream.read(8*1024*1024):h.update(block)
        assert h.hexdigest()==sha256(p);checked.append(p.relative_to(ROOT).as_posix())
    c=pd.read_csv(ART/'calibration.csv');c=c[c.stage.eq('held_assay')&c.endpoint.eq('replicate')].copy();c['constant_half_brier']=.25;c['constant_half_logloss']=np.log(2);c['brier_gain_vs_constant_half']=.25-c.brier;c['logloss_gain_vs_constant_half']=np.log(2)-c.log_loss;csvsave(OUT/'calibration_constant_reference.csv',c)
    p=c[c.model.isin(PRIMARY)][['model','dataset','brier','log_loss','brier_gain_vs_constant_half','logloss_gain_vs_constant_half']]
    text='''# Interpreting improved probability scores

This is a postfit analytic reference, not a new fitted comparator, gate or selection rule. A constant pair probability of 0.5 has expected per-replicate Brier score 0.25 and log loss log(2)=0.693147, for every target fraction. With both orientations equally weighted it also has marginal ECE zero and sharpness zero. It supplies no candidate-ranking information.

'''+table(p)+'''

Every primary method remains worse than the constant-0.5 reference on both probability scores in all three replicate-covered whole-study evaluations. Thus P2's improvement over H0 in Brier/log loss should be understood as reduced probabilistic error; it does not demonstrate informative or calibrated transfer. Better calibration scores and useful discrimination are distinct. The frozen calibration-claim gate and decision gate both remain failed, and no abstention policy was activated.

The numerical reference is valid for the exact expected per-replicate scoring definitions used here. It is not the squared error against an empirical fraction, whose null score would differ. No hard-label, model, candidate, or evaluation endpoint changed for this calculation.
'''
    assert (p.brier_gain_vs_constant_half<0).all() and (p.logloss_gain_vs_constant_half<0).all()
    save(REP/'calibration_reference.md',text.encode())
    jsave(OUT/'quality_receipt.json',{'status':'PASS','gzip_roundtrips':checked,'figure_visual_review':'Seven figures and contact sheet inspected; reliability-plot labels adjusted and rechecked.','constant_probability_reference':'analytic postfit context only; no gate change','code_sha256':sha256(Path(__file__))})
    print('Delivery quality checks PASS; eight gzip round trips and analytic calibration reference.',flush=True)
if __name__=='__main__':run()
