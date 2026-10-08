"""Independent stdlib RBP aggregate arithmetic; no fits/feature/model readers."""
from collections import defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
NS='generalization_rbp_20261007'
OUT=ROOT/'results'/NS
STUDIES=['astrocyte_gse330741','mikl_gse173098','moffatt_gse334718','srle']
TRACKS=['base','raw','access']
COLS=['regret','wrong_direction','avoidable_wrong','no_feasible_candidate','unavoidable_wrong',
      'neutral_only_alternative_wrong','best_recovery','top5_best_recovery','pairwise_accuracy']
TARGET=ROOT/'results/generalization_campaign_20261007/rbp_numerical_audit_03.json'
REPORT=ROOT/'reports/generalization_campaign_20261007/reviewed_rbp_results_03.md'

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def readj(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def csvrows(path):
 with Path(path).open(encoding='utf-8',newline='') as f:
  yield from csv.DictReader(f)
def mean(values):return math.fsum(values)/len(values)
def group_summary(rows):
 components=defaultdict(lambda:defaultdict(list))
 for r in rows:
  for metric in COLS:components[(r['dataset'],r['biological_component'])][metric].append(float(r[metric]))
 studies={study:{metric:mean([mean(values[metric]) for (s,_),values in components.items() if s==study]) for metric in COLS} for study in STUDIES}
 return studies,components
def independent_checks(regret,g,gh,wrong,wrong_h,lower):
 positive=[max(v,0.) for v in g];share=max(positive)/math.fsum(positive) if math.fsum(positive)>0 else 1.
 best=max(range(4),key=lambda i:g[i]);remaining=mean([g[i] for i in range(4) if i!=best])
 checks={'macro_regret_at_most_0_468':mean(regret)<=.468,
  'macro_gain_vs_simple_at_least_0_02':mean(g)>=.02,
  'three_assays_gain_vs_simple_at_least_0_02':sum(v>=.02 for v in g)>=3,
  'three_assays_gain_vs_H0_at_least_0_01':sum(v>=.01 for v in gh)>=3,
  'Mikl_SRLE_harm_at_most_0_01_vs_both':all(max(-g[i],-gh[i])<=.01 for i in (1,3)),
  'any_assay_harm_vs_simple_at_most_0_05':all(v>=-.05 for v in g),
  'macro_avoidable_harm_at_most_0_02_vs_both':max(mean(wrong),mean(wrong_h))<=.02,
  'each_avoidable_harm_at_most_0_05_vs_both':max(*wrong,*wrong_h)<=.05,
  'leave_best_assay_out_positive':remaining>0.,'max_positive_gain_share_at_most_0_60':share<=.6,
  'descriptive_bootstrap_lower_at_least_minus_0_01':lower>=-.01}
 return checks,share,remaining,STUDIES[best]

class Tests(unittest.TestCase):
 def test_component_means_not_candidate_size(self):
  rows=[]
  for study in STUDIES:
   for component,n,value in [('a',2,0.),('b',8,1.)]:
    rows.extend(dict(dataset=study,biological_component=component,**{key:value for key in COLS}) for _ in range(n))
  s,_=group_summary(rows);self.assertEqual(s[STUDIES[0]]['regret'],.5)
 def test_breadth_concentration_and_removed_best(self):
  c,share,remaining,best=independent_checks([.4]*4,[.08,-.01,.01,-.01],[.01]*4,[0.]*4,[0.]*4,0.)
  self.assertFalse(c['three_assays_gain_vs_simple_at_least_0_02']);self.assertGreater(share,.6);self.assertLess(remaining,0.)
  self.assertEqual(best,STUDIES[0])
 def test_worst_harm_against_both_controls(self):
  c,_,_,_=independent_checks([.4]*4,[.03]*4,[.03,-.02,.03,.03],[0.]*4,[0.]*4,0.)
  self.assertFalse(c['Mikl_SRLE_harm_at_most_0_01_vs_both'])

def run():
 assert not TARGET.exists() and not REPORT.exists()
 assert not any(n.split('.')[0] in ('numpy','pandas','scipy','torch','sklearn') for n in sys.modules)
 paths=[OUT/'gate_verdict.json',OUT/'verification_receipt.json',OUT/'canonical_source_only_replay.json',
        OUT/'prefit_manifest.json',OUT/'feature_production_manifest.json',
        ROOT/'artifacts/cross_assay_20260927/model_comparison.csv',ROOT/'results/cross_assay_20260927/decision_metrics.csv',
        ROOT/'src/generalization_rbp_20261007/gate.py',ROOT/'src/generalization_rbp_20261007/common.py',
        ROOT/'src/generalization_20261007/common.py',ROOT/'src/generalization_next_20261007/bootstrap.py',
        ROOT/'reports/generalization_rbp_20261007/protocol.md',Path(__file__)]
 paths.extend(OUT/track/name for track in TRACKS for name in ('comparison.csv','decisions.csv','run_complete.json'))
 before={p.relative_to(ROOT).as_posix():sha(p) for p in paths}
 gate=readj(OUT/'gate_verdict.json');assert gate['status']=='NO-GO'
 verified=readj(OUT/'verification_receipt.json');canonical=readj(OUT/'canonical_source_only_replay.json')
 assert verified['status']=='PASS' and verified['models']==120
 assert canonical['status'].startswith('PASS')
 original=[r for r in csvrows(ROOT/'artifacts/cross_assay_20260927/model_comparison.csv') if r['stage']=='held_assay' and r['dataset'] in STUDIES and r['model'] in ('uniform','metadata','composition','interaction_3')]
 old={(r['model'],r['dataset']):r for r in original};assert len(old)==16
 prior=[r for r in csvrows(ROOT/'results/cross_assay_20260927/decision_metrics.csv') if r['stage']=='held_assay' and r['dataset'] in STUDIES and r['model'] in ('uniform','metadata','composition','interaction_3')]
 simple={s:min(('uniform','metadata','composition'),key=lambda m:(float(old[m,s]['regret']),float(old[m,s]['avoidable_wrong']),m)) for s in STUDIES}
 baseline_reconstructed={};maximum=0.;numeric=0;boolean=0;metric_rows={};rosters={};audited=[]
 def check(a,b):
  nonlocal maximum,numeric
  error=abs(float(a)-float(b));maximum=max(maximum,error);numeric+=1;assert error<=1e-12,(a,b,error)
 for model in ('uniform','metadata','composition','interaction_3'):
  summaries,_=group_summary([r for r in prior if r['model']==model]);baseline_reconstructed[model]=summaries
  for study in STUDIES:
   assert set(COLS)-set(old[model,study])=={'neutral_only_alternative_wrong'},'Unexpected historical comparison schema'
   for metric in COLS:
    if metric in old[model,study]:check(summaries[study][metric],old[model,study][metric])
 for track,declared in zip(TRACKS,gate['tracks']):
  assert declared['track']==track and readj(OUT/track/'run_complete.json')['status']=='PASS'
  rows=list(csvrows(OUT/track/'decisions.csv'));assert len(rows)==10872
  roster=[(r['dataset'],r['biological_component'],r['parent_context_id'],int(r['direction'])) for r in rows]
  assert len(set(roster))==len(roster) and {r['model'] for r in rows}=={track} and {r['stage'] for r in rows}=={'held_assay'}
  assert all(math.isfinite(float(r[key])) for r in rows for key in COLS)
  for r in rows:
   assert int(r['direction']) in (-1,1) and int(r['candidates'])>=2
   assert -1e-12<=float(r['regret'])<=1.+1e-12
   check(float(r['wrong_direction']),sum(float(r[k]) for k in ('avoidable_wrong','unavoidable_wrong','neutral_only_alternative_wrong')))
  rosters[track]=set(roster);sums,components=group_summary(rows);metric_rows[track]=sums
  comp={r['dataset']:r for r in csvrows(OUT/track/'comparison.csv')};assert set(comp)==set(STUDIES)
  for study in STUDIES:
   for metric in COLS:check(sums[study][metric],comp[study][metric])
  regret=[sums[s]['regret'] for s in STUDIES]
  g=[baseline_reconstructed[simple[s]][s]['regret']-sums[s]['regret'] for s in STUDIES]
  gh=[baseline_reconstructed['interaction_3'][s]['regret']-sums[s]['regret'] for s in STUDIES]
  wrong=[sums[s]['avoidable_wrong']-baseline_reconstructed[simple[s]][s]['avoidable_wrong'] for s in STUDIES]
  wrong_h=[sums[s]['avoidable_wrong']-baseline_reconstructed['interaction_3'][s]['avoidable_wrong'] for s in STUDIES]
  checks,share,remaining,best=independent_checks(regret,g,gh,wrong,wrong_h,declared['gain_ci'][0])
  assert checks==declared['checks'];boolean+=len(checks)
  check(mean(regret),declared['macro_regret']);check(mean(g),declared['macro_gain_vs_simple']);check(mean(gh),declared['macro_gain_vs_H0']);check(-min(gh),declared['worst_harm_vs_H0'])
  assert declared['assays_helped_vs_H0']==sum(v>0 for v in gh) and declared['assays_harmed_vs_H0']==sum(v<0 for v in gh)
  for i,study in enumerate(STUDIES):
   given=declared['per_assay'][i];assert given['dataset']==study
   for key,value in [('regret',regret[i]),('gain_vs_simple',g[i]),('gain_vs_H0',gh[i]),('avoidable_wrong',sums[study]['avoidable_wrong'])]:check(value,given[key])
  audit={'track':track,'macro_regret':mean(regret),'gain_vs_simple':mean(g),'gain_vs_H0':mean(gh),'per_assay':sums,
         'components_per_assay':{study:sum(ss==study for ss,_ in components) for study in STUDIES},'decision_rows':len(rows),
         'checks':checks,'failed_checks':[name for name,ok in checks.items() if not ok],
         'positive_gain_share_vs_simple':share,'leave_best_assay_out_gain_vs_simple':remaining,'best_assay_vs_simple':best,
         'gain_ci_reported_not_resimulated':declared['gain_ci'],'historical_gate_passes':all(checks.values())}
  audited.append(audit)
 assert rosters['base']==rosters['raw']==rosters['access']
 for model in ('uniform','metadata','composition','interaction_3'):
  historical_roster={(r['dataset'],r['biological_component'],r['parent_context_id'],int(r['direction'])) for r in prior if r['model']==model}
  assert historical_roster==rosters['base'],'Historical control full-menu roster differs: '+model
 for audit,declared in zip(audited,gate['tracks']):
  track=audit['track'];comparators={'raw':['base'],'access':['raw']}.get(track,[])
  increment=[]
  for comparator,given in zip(comparators,declared['incremental_comparisons']):
   gains=[metric_rows[comparator][ss]['regret']-metric_rows[track][ss]['regret'] for ss in STUDIES]
   remaining=mean([v for i,v in enumerate(gains) if i!=max(range(4),key=lambda j:gains[j])])
   checks={'macro_incremental_gain_at_least_0_01':mean(gains)>=.01,'incremental_leave_best_assay_out_positive':remaining>0}
   assert given['comparator']==comparator and given['checks']==checks and given['passes']==all(checks.values());boolean+=3
   check(mean(gains),given['mean_gain'])
   for i,study in enumerate(STUDIES):check(gains[i],given['per_assay_gain'][study])
   increment.append({'comparator':comparator,'mean_gain':mean(gains),'per_assay_gain':dict(zip(STUDIES,gains)),'leave_best_gain':remaining,'passes':all(checks.values())})
  audit['incremental_comparisons']=increment
  assert declared['historical_gate_passes']==audit['historical_gate_passes']
  assert declared['passes']==bool(audit['historical_gate_passes'] and track in ('raw','access') and all(r['passes'] for r in increment));boolean+=2
 access_base=[metric_rows['base'][ss]['regret']-metric_rows['access'][ss]['regret'] for ss in STUDIES]
 comparisons={'access_vs_base_descriptive':{'mean_gain':mean(access_base),'per_assay_gain':dict(zip(STUDIES,access_base)),
     'leave_best_assay_gain':mean([v for i,v in enumerate(access_base) if i!=max(range(4),key=lambda j:access_base[j])])}}
 assert before=={p.relative_to(ROOT).as_posix():sha(p) for p in paths},'Inputs changed during audit'
 result={'status':'PASS_INDEPENDENT_RBP_POINT_METRICS_AND_GATE_ARITHMETIC','tracks':audited,'descriptive_comparisons':comparisons,
         'numeric_values_checked':numeric,'boolean_checks_checked':boolean,'maximum_absolute_numeric_error':maximum,
         'selected_historical_simple_controls':simple,'all_three_complete_decision_rosters_equal':True,
         'observed_input_sha256_postfit_not_creation_binding':before,'canonical_checkpoint_replay_receipt_bound':True,
         'bootstrap_source_inspected':True,'bootstrap_draws_independently_resimulated':False,
         'bootstrap_limit':'Reported percentiles are hash-bound outputs; their gate inequality was independently checked. No fresh NumPy draw simulation performed by this stdlib audit.',
         'historical_comparison_missing_field':'neutral_only_alternative_wrong is reconstructed from original decision CSV but is absent from the historical comparison schema; no fabricated old-column parity claim',
         'new_models_fitted':0,'features_or_model_parameters_read':False,'protected_outcomes_read':False,'criteria_or_old_files_changed':False}
 TARGET.parent.mkdir(parents=True,exist_ok=True)
 with TARGET.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')
 table='\n'.join('| '+a['track']+' | '+f"{a['macro_regret']:.6f}"+' | '+f"{a['gain_vs_simple']:+.6f}"+' | '+f"{a['gain_vs_H0']:+.6f}"+' | NO-GO |' for a in audited)
 text='''# Independently reviewed RBP transfer results

All three declared RBP tracks remain NO-GO. Accessibility improves over the raw-motif route on all four exposed assays, but does not satisfy the unchanged generalization gate or establish a biological binding mechanism.

| Track | Macro regret (lower better) | Gain vs best simple | Gain vs historical H0 | Verdict |
|---|---:|---:|---:|---|
'''+table+'''

The accessibility-vs-raw mean improvement is0.039289, with assay gains Astro0.004098, Mikl0.002051, Moffatt0.054657 and SRLE0.096349. Its fixed incremental check passes, including positive gain after the best assay is removed. However, raw was a poor comparator: its mean regret0.526923 is worse than base0.512255, and its gain versus the historical simple controls has a wholly negative reported95% descriptive interval[-0.044981,-0.014785]. Accessibility mostly repairs this deterioration; the improvement does not make the whole-assay task pass.

Accessibility macro regret0.487635 exceeds the required0.468, and mean simple-control gain0.009233 is below0.02. Its reported descriptive interval[-0.015770,0.034185] includes zero and its lower bound fails even the declared permissive-0.01 threshold. Only Astro and Moffatt improve versus the strongest simple controls; Mikl is worse by0.033720 and SRLE by0.032315. Only Astro improves versus historical H0. Positive gain concentration is above60%, and removing Astro leaves negative mean gain versus simple. Thus breadth, concentration, distributed gain and protected Mikl/SRLE harm criteria fail. This interval is conditional on repeatedly exposed assays and fixed controls; it is not independent confirmation or a probability of future success.

Accessibility improves over its freshly fit base by0.024620 macro, but that descriptive gain is concentrated in Astro. The other three assays all worsen relative to base, and removing Astro makes that contrast negative. Four-positive gains versus raw therefore cannot support a four-source improvement over the stronger available comparators. The declared matched accessibility comparator remains raw; this additional contrast explains the practical limits without changing any selector or verdict.

Equal-assay macro summaries first average each decision direction/context within biological component, then average components. The full10,872 decision rows per track share exactly the same dataset/component/context/direction roster. This audit independently reconstructs every point comparison column, historical simple/H0 summaries, categorical wrong-direction partition, all eleven historical gate booleans, incremental checks and final eligibility. It hash-binds the completed120-model canonical replay and original verification receipts; it does not rerun models, parse coefficients, or treat aggregate arithmetic as author-level label proof. The reported shared-component exponential bootstrap source was inspected: one weight per global component is reused across studies, normalized within each assay, then four assays have equal weight. Bootstrap draws/percentiles were not independently resimulated in this stdlib audit; the existing CI bytes and their gate inequalities are explicitly bound.

Raw PFMs are direct human in-vitro specificity priors applied to mouse and engineered reporters. Marginal nucleotide unpairing is an isolated RNA ensemble proxy, not joint site opening or cell-specific RBP occupancy. Random projection compresses motifs and prevents individual-protein causal attribution. No new biological study, wet-lab evidence, localization probability, evolutionary-homology guarantee or cell-state measurement is added. The postfit cell-axis follow-up remains a separate repeatedly exposed development evaluation; it cannot rescue these frozen whole-assay results.

All input/source/decision/gate hashes are observed postfit audit bindings, not retroactive creation-time certifications. No old source, protocol, output, model or threshold was modified; no fit, protected outcome or feature/model-parameter read occurred. The numerical JSON receipt records exact reconstructed values, failed criteria, coverage, provenance and confidence limits.
'''
 with REPORT.open('x',encoding='utf-8') as f:f.write(text)
 print('RBP point/gate independent audit PASS',numeric,boolean,maximum,sha(TARGET),sha(REPORT),flush=True)

if __name__=='__main__':
 if '--test' in sys.argv:unittest.main(argv=[sys.argv[0]],verbosity=2)
 else:run()
