"""Independent arithmetic/lineage check of the exposed four-assay core.

No fitting, eligibility changes or protected outcomes. Explicit source usecols
exclude stability and unadmitted assay outcomes. This checks local preserved
tables, not complete reconstruction of the author's raw experimental pipeline.
"""
from src.generalization_20261007.common import ROOT, np, pd, sha256
from pathlib import Path
import json

OUT = ROOT / 'results/generalization_next_20261007'
CORE = ROOT / 'results/probabilistic_ranking_20260928/candidate_index.csv'


def comparison(name, frame, source, keys, mapping):
    source = source[keys + list(mapping)].copy()
    assert not source.duplicated(keys).any(), (name, 'ambiguous local source')
    source = source.rename(columns={k: 'direct_' + k for k in mapping})
    joined = frame.merge(source, on=keys, how='left', validate='many_to_one', indicator=True)
    assert joined['_merge'].eq('both').all(), (name, 'source lineage missing')
    report = {'rows': len(joined), 'columns': {}}
    for original, canonical in mapping.items():
        a, b = joined['direct_' + original], joined[canonical]
        if canonical in ('parent_sequence', 'mutant_sequence'):
            equal = a.astype(str).eq(b.astype(str))
            assert equal.all(), (name, canonical)
            report['columns'][canonical] = {'exact_matches': int(equal.sum())}
        else:
            av, bv = a.to_numpy(float), b.to_numpy(float)
            assert np.isfinite(av).all() and np.isfinite(bv).all()
            error = float(np.max(np.abs(av-bv)))
            assert error <= 5e-10, (name, canonical, error)
            report['columns'][canonical] = {'maximum_absolute_error': error}
    return report


def run():
    target = OUT / 'admitted_lineage_audit_receipt.json'
    assert not target.exists(), 'Preserve previous audit receipt'
    assert sha256(CORE) == '773d6145bbe4b17ff50597e47eba13f0b2977a3ddf541a1b238adcb7ff433e3d'
    f = pd.read_csv(CORE, low_memory=False, float_precision='round_trip')
    assert len(f) == 26258 and f.intervention_id.is_unique
    reports, inputs = {}, [CORE]
    for r in f.itertuples():
        changed = [i+1 for i, (a,b) in enumerate(zip(r.parent_sequence,r.mutant_sequence)) if a != b]
        assert len(r.parent_sequence) == len(r.mutant_sequence)
        assert len(changed) == r.substitution_count and 1 <= len(changed) <= 6
        assert (min(changed),max(changed),max(changed)-min(changed)+1) == (r.edit_start,r.edit_end,r.physical_edit_span)
        assert not set(r.parent_sequence+r.mutant_sequence)-set('ACGT')

    path = ROOT / 'results/v4_phaseA/mikl_interventions.csv.gz'; inputs.append(path)
    keys = ['parent_id','mutant_id']
    columns = keys+['parent_sequence','mutant_sequence','localization_effect_cad','localization_effect_n2a']
    direct = pd.read_csv(path,usecols=columns,float_precision='round_trip')
    for cell, effect in [('CAD','localization_effect_cad'),('Neuro-2a','localization_effect_n2a')]:
        rows = f[f.dataset.eq('mikl_gse173098') & f.cell_type.eq(cell)]
        reports['mikl_'+cell] = comparison(cell,rows,direct,keys,
            {'parent_sequence':'parent_sequence','mutant_sequence':'mutant_sequence',effect:'measured_delta'})

    path = ROOT / 'results/v4_phaseA/moffatt_interventions.csv.gz'; inputs.append(path)
    columns = keys+['parent_sequence','mutant_sequence','intervention_class','localization_effect_gfp','localization_effect_firefly']
    direct = pd.read_csv(path,usecols=columns,float_precision='round_trip')
    direct = direct[direct.intervention_class.eq('random_substitution')]
    for reporter,effect in [('GFP','localization_effect_gfp'),('Firefly','localization_effect_firefly')]:
        rows = f[f.dataset.eq('moffatt_gse334718') & f.reporter.eq(reporter)]
        reports['moffatt_'+reporter] = comparison(reporter,rows,direct,keys,
            {'parent_sequence':'parent_sequence','mutant_sequence':'mutant_sequence',effect:'measured_delta'})

    path = ROOT / 'artifacts/generalization_20260926/GSE330741_mapped_outcomes.csv'; inputs.append(path)
    cols = ['element','parent_id','parent_sequence','mutant_sequence','observed_delta',
            'author_wt_normalized_localization','author_mutant_normalized_localization','qc_status']
    direct = pd.read_csv(path,usecols=cols,float_precision='round_trip')
    direct = direct[direct.qc_status.eq('VERIFIED')].rename(columns={'element':'mutant_id'})
    reports['astrocyte'] = comparison('astrocyte',f[f.dataset.eq('astrocyte_gse330741')],direct,keys,
        {'parent_sequence':'parent_sequence','mutant_sequence':'mutant_sequence','observed_delta':'measured_delta',
         'author_wt_normalized_localization':'measured_parent_localization',
         'author_mutant_normalized_localization':'measured_mutant_localization'})

    path = ROOT / 'results/research_20260921/raw_replication_scores.csv'; inputs.append(path)
    direct = pd.read_csv(path,usecols=['kmer','NRS1','NRS2'],float_precision='round_trip').set_index('kmer')
    assert direct.index.is_unique
    rows = f[f.dataset.eq('srle')]
    parent = direct.loc[rows.parent_sequence,['NRS1','NRS2']].to_numpy(float)
    mutant = direct.loc[rows.mutant_sequence,['NRS1','NRS2']].to_numpy(float)
    assert np.isfinite(parent).all() and np.isfinite(mutant).all()
    errors = {}
    for name,expected in [('measured_delta',(mutant-parent).mean(1)),
                          ('measured_parent_localization',parent.mean(1)),
                          ('measured_mutant_localization',mutant.mean(1))]:
        error = float(np.max(abs(expected-rows[name].to_numpy(float))))
        assert error <= 5e-10, (name,error); errors[name] = error
    reports['srle'] = {'rows':len(rows),'maximum_absolute_errors':errors}
    assert sum(v['rows'] for v in reports.values()) == len(f)
    result = {'status':'PASS','rows_checked':len(f),'source_checks':reports,
        'local_source_hashes':{p.relative_to(ROOT).as_posix():sha256(p) for p in inputs},
        'scope':'Independent preserved-table lineage and numeric arithmetic; not author raw pipeline reproduction',
        'limitations':['SRLE raw-to-author-table chain remains partial','Moffatt paired mutant-minus-WT replicates remain absent',
                       'Author aggregate effects need not equal mean pseudocounted raw contrasts',
                       'Local table agreement does not certify physical clone identity or complete reporter processing'],
        'protected_outcomes_opened':False,'models_fit':0,'source_sha256':sha256(Path(__file__))}
    OUT.mkdir(parents=True,exist_ok=True)
    with target.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(result,stream,indent=2,sort_keys=True);stream.write('\n')
    print(json.dumps(result,indent=2),flush=True)


if __name__ == '__main__': run()
