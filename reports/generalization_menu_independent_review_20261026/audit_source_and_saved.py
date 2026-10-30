"""Stdlib invented probes and a fixed, already exposed report audit only."""
import ast
from collections import defaultdict
import csv
import hashlib
import io
import itertools
import json
import math
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'reports/generalization_menu_independent_review_20261026'
OBSERVED = {}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(name, maximum=16*2**20):
    path = ROOT/name
    assert path.resolve().is_relative_to(ROOT.resolve())
    assert not name.endswith(('.gz', '.npz', '.npy', '.dll', '.exe'))
    assert path.stat().st_size <= maximum
    with path.open('rb') as stream:
        raw = stream.read(maximum+1)
    assert len(raw) <= maximum
    OBSERVED[name] = sha(raw)
    return raw


def main():
    controls = (
        'results/generalization_menu_comparison_core_20261026/source_manifest.json',
        'results/generalization_menu_comparison_core_20261026/metadata_route_source_manifest.json',
        'results/generalization_menu_loss_20261026/prototype_manifest.json')
    control_counts = {}
    for name in controls:
        manifest = json.loads(read(name))
        control_counts[name] = len(manifest['files'])
        for path, want in manifest['files'].items():
            raw = read(path)
            assert sha(raw) == want, path
            if path.endswith('.py'):
                ast.parse(raw, filename=path)
    assert OBSERVED[controls[0]] == 'be83d0a8aaddda6959475a6c86241b99624aa300fe71940e10d5b60ed4c02fd9'
    extracts = json.loads(read('results/generalization_menu_independent_review_20261026/historical_source_extract.json'))
    for entry in extracts['files']:
        raw = read(entry['extracted_path'])
        assert sha(raw) == entry['sha256'] and len(raw) == entry['bytes']
        assert entry['source_commit'] == '3640240580717a9a6e40945ded851806b91fc71f'
        ast.parse(raw, filename=entry['historical_path'])
    for path in ('src/generalization_menu_bound_reference_20261026/reference.py',
                 'src/generalization_menu_bound_reference_20261026/tests.py',
                 'src/generalization_menu_bound_reference_20261026/__init__.py'):
        ast.parse(read(path), filename=path)
    assert not os.path.lexists(ROOT/'results/generalization_knowncell_runtime_provider_20261023/source_cache_must_remain_absent')
    from src.generalization_menu_comparison_core_20261026 import scalar, metadata_route as route
    from src.generalization_menu_loss_20261026.loss import menu_loss
    from src.generalization_menu_bound_reference_20261026.reference import evaluate

    catalog = ({'context':'m0','indices':(0,1),'weight':.5},
               {'context':'m1','indices':(2,3),'weight':.5})
    x = ((0.,),(1.,),(0.,),(100.,))
    effects = (0.,1.,0.,1.)
    sampled = {'m0':((0,1),),'m1':((2,3),)}
    pairs = scalar.pair_contract(effects,catalog,sampled)
    scale = scalar.scaling(x,pairs,catalog)
    missing = ((0,1,-1.,1.),)
    wrong_scale = scalar.scaling(x,missing,catalog)
    wrong_value = scalar.objective((.2,),x,effects,catalog,missing,wrong_scale,
                                   arm='pairwise',penalty=.05)
    reweighted = ((0,1,-1.,.99),(2,3,-1.,.01))
    scalar.objective((.2,),x,effects,catalog,reweighted,scalar.scaling(x,reweighted,catalog),
                     arm='pairwise',penalty=.05)
    cross = scalar.scaling(x,((0,3,-1.,1.),),catalog)
    witness = {'source_rows':4,'complete_menus':2,'declared_menu_weights':[.5,.5],
        'proper_pair_weights':[r[3] for r in pairs],
        'first_context_only_mass1_accepted_by_low_level_functions':True,
        'accepted_objective':wrong_value[0],'proper_rms':scale['pair_rms'][0],
        'missing_context_rms':wrong_scale['pair_rms'][0],
        'arbitrary_context_weights_accepted':[.99,.01],
        'cross_context_pair_accepted_by_scaling_only_rms':cross['pair_rms'][0]}
    metadata = []
    for si, study in enumerate(route.STUDIES):
        parent = 'A'*20+'ACGT'[si]
        for c in range(2):
            metadata.append({'intervention_id':study+':'+str(c),'dataset':study,
                'biological_component':'g'+str(si),'parent_context_id':'ctx'+str(si),
                'parent_sequence':parent,'mutant_sequence':('C' if c==0 else 'G')+parent[1:]})
    args = dict(beta=(.2,),features=x,effects=effects,source_metadata=metadata[:4],
        sampled_pairs={'ctx0':((0,1),),'ctx1':((2,3),)},arm='pairwise',penalty=.05)
    correct = evaluate(**args)
    for key in ('pair_rows','menu_catalog'):
        try:
            evaluate(**args, **{key:missing})
        except TypeError:
            pass
        else:
            raise AssertionError('new API permits injection')
    omitted = dict(args, sampled_pairs={'ctx0':((0,1),)})
    try:
        evaluate(**omitted)
    except ValueError:
        pass
    else:
        raise AssertionError('new API permits omitted context')
    repair = {'new_api_rejects_pair_and_catalog_injection_and_context_omission':True,
              'internally_recomputed_rms':correct['source_scaling']['pair_rms'][0],
              'actual_input_admission_certified':correct['input_admission_certified']}

    gradient_error = 0.
    for scores,y in (((.3,-.7,.4,.9),(-2.,.1,1.4,3.)),
                     ((.3,-.7,.4,.9),(1.,1.,0.,0.)),((.2,-.1,2.),(0.,.4,1.))):
        _, gradient = menu_loss(scores,y)
        for j,want in enumerate(gradient):
            a,b=list(scores),list(scores);a[j]+=1e-6;b[j]-=1e-6
            error=abs((menu_loss(a,y)[0]-menu_loss(b,y)[0])/2e-6-want)
            gradient_error=max(gradient_error,error)
    assert gradient_error<2e-9
    binary_error=binary_gradient_error=0.
    for a,b in itertools.product((-5.,-.3,0.,.4,5.),repeat=2):
        t=(1-(b-a))/.25
        expected=.25*(max(t,0)+math.log1p(math.exp(-abs(t))))
        p=1/(1+math.exp(-t)) if t>=0 else math.exp(t)/(1+math.exp(t))
        value,g=menu_loss((a,b),(-2.,5.))
        binary_error=max(binary_error,abs(value-expected))
        binary_gradient_error=max(binary_gradient_error,abs(g[0]-p),abs(g[1]+p))
    assert binary_error<1e-13 and binary_gradient_error<1e-13
    for scores in itertools.product((-2.,0.,2.),repeat=3):
        for y in ((0.,.2,1.),(0.,1.,1.)):
            regret=math.fsum((max(d*v for v in y)-d*y[max(range(3),key=lambda i:d*scores[i])])/(max(y)-min(y)) for d in (-1,1))/2
            assert menu_loss(scores,y)[0]+1e-14>=regret

    def streams(reserved=False):
        index,archive=io.StringIO(),io.StringIO()
        iw=csv.DictWriter(index,fieldnames=route.INDEX_FIELDS,lineterminator='\n');iw.writeheader()
        aw=csv.DictWriter(archive,fieldnames=route.ARCHIVE_FIELDS+('measured_localization_value','unused'),lineterminator='\n');aw.writeheader()
        for i,row in enumerate(metadata):
            iw.writerow({k:row[k] for k in route.INDEX_FIELDS})
            for slot,rep in enumerate(route.REPLICATE_IDS[row['dataset']]):
                if reserved and i==6 and slot==1:rep=3
                aw.writerow({'candidate_id':row['intervention_id'],**{k:row[k] for k in route.FIELDS if k!='intervention_id'},
                    'feature_row':i,'replicate_slot':slot,'replicate_id':rep,
                    'measured_localization_value':'NOT_NUMERIC','unused':'quoted, unused\nNaN 1e999999'})
        index.seek(0);archive.seek(0);return index,archive
    parsed=route.parse_streams(*streams(),expected_rows=8)
    assert parsed['rows']==tuple(metadata) and parsed['numeric_outcome_columns_parsed'] is False
    try:
        route.parse_streams(*streams(True),expected_rows=8)
    except ValueError as error:
        reserved_error=str(error)
    else:
        raise AssertionError('reserved replicate admitted')

    report_path='results/generalization_current_study_verification_20261026/evaluate/worker_report.json'
    raw=read(report_path,64*2**20)
    assert sha(raw)=='be53e8c02be6ae444ec67bd231532571bd97d00a4c92b4f52bc8ec15969f462a'
    original=json.loads(raw)['result']
    saved=json.loads(read('results/generalization_menu_feasibility_20261026/saved_decision_diagnostic.json'))
    summaries={};maximum_error=0.;rosters=[];distribution=None
    for arm,decisions in original['primary_decisions'].items():
        groups=defaultdict(dict)
        for row in decisions:
            key=(row['cell_type'],row['biological_component'],row['parent_context_id']);d=row['direction']
            assert d in (-1,1) and d not in groups[key];groups[key][d]=row
        assert len(groups)==4816 and all(set(v)=={-1,1} for v in groups.values());rosters.append(set(groups))
        hierarchy=defaultdict(lambda:defaultdict(list))
        for key,directions in groups.items():
            assert directions[-1]['candidates']==directions[1]['candidates']
            hierarchy[key[0]][key[1]].append((key,math.fsum(row['regret'] for row in directions.values())/2))
        macro=math.fsum(math.fsum(math.fsum(v for _,v in menus)/len(menus) for menus in genes.values())/len(genes) for genes in hierarchy.values())/len(hierarchy)
        binary_values=[];binary_mass=[];multi_values=[];constant=0;counts=defaultdict(int);masses=defaultdict(list)
        for cell,genes in hierarchy.items():
            assert len(genes)==187
            for gene,menus in genes.items():
                weight=1/len(hierarchy)/len(genes)/len(menus)
                for key,regret in menus:
                    ds=groups[key];n=ds[1]['candidates'];name=str(n) if n<=4 else ('5-9' if n<10 else '10+')
                    counts[name]+=1;masses[name].append(weight)
                    if n==2:binary_values.append(weight*regret);binary_mass.append(weight)
                    else:multi_values.append(weight*regret)
                    if ds[-1]['selected_score']==ds[1]['selected_score']:constant+=1
        binary=math.fsum(binary_values)/math.fsum(binary_mass)
        binary_contribution=math.fsum(binary_values);multi=math.fsum(multi_values)
        target=saved['arms'][arm]
        for a,b in ((macro,target['macro_regret_recomputed']),(binary,target['conditional_regret_by_menu_size']['2']),
                    (binary_contribution,target['restricted_best_possible_regret_if_only_multicandidate_choices_change']),
                    (multi,target['multicandidate_current_regret_contribution'])):
            maximum_error=max(maximum_error,abs(a-b))
        assert abs(macro-original['primary_summaries'][arm]['macro_regret'])<1e-12 and constant==target['exact_constant_score_menus']
        summaries[arm]={'macro_regret':macro,'binary_conditional_regret':binary,'binary_implied_accuracy':1-binary,
            'constant_menus':constant,'restricted_bound_direct_binary_contribution':binary_contribution,'multi_regret_contribution':multi}
        this_distribution={name:{'menus':counts[name],'primary_weight':math.fsum(values)} for name,values in masses.items()}
        if distribution is None:distribution=this_distribution
        else:assert this_distribution==distribution
    assert all(roster==rosters[0] for roster in rosters) and maximum_error<1e-12
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch') for name in sys.modules)
    OBSERVED[Path(__file__).resolve().relative_to(ROOT).as_posix()]=sha(Path(__file__).read_bytes())
    for name,want in OBSERVED.items():assert sha((ROOT/name).read_bytes())==want,name
    result={'status':'INDEPENDENT_SOURCE_AND_EXPOSED_REPORT_AUDIT_NOT_INPUT_OR_NATIVE_ADMISSION',
        'files_sha256':OBSERVED,'control_manifest_counts':control_counts,'invented_pair_binding_witness':witness,
        'additive_source_bound_repair_probe':repair,'maximum_gradient_probe_error':gradient_error,
        'maximum_binary_loss_probe_error':binary_error,'maximum_binary_gradient_probe_error':binary_gradient_error,
        'invented_parser_rows':8,'invented_parser_records':parsed['archive_records_tokenized'],'reserved_alias_rejection':reserved_error,
        'saved_decision_metrics_independently_reconstructed':summaries,'menu_distribution':distribution,
        'maximum_saved_metric_difference':maximum_error,'original_inputs_CORE_arrays_archives_or_protected_outcomes_opened':False,
        'actual_scientific_imports_models_jobs_or_fits':0,'new_biological_or_native_admission':False}
    raw=(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
    with (OUT/'review_evidence.json').open('xb') as stream:stream.write(raw)
    print(json.dumps({'status':result['status'],'evidence_sha256':sha(raw),'files_bound':len(OBSERVED),
        'witness':witness,'maximum_gradient_error':gradient_error,'maximum_saved_metric_difference':maximum_error,
        'metrics':summaries},sort_keys=True))


if __name__=='__main__':
    main()
