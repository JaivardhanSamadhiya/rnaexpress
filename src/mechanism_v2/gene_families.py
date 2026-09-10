"""External orthology-linked gene-group leakage sensitivity, with coverage audit."""
from __future__ import annotations
import json
from collections import defaultdict
import numpy as np
import pandas as pd
from .io import ROOT,load_development,sha256,write_json
from .forensics import csv
from .splits import balanced_group_folds
from .feature_store import validate_split_alignment

MISSING={'','-','missing','unknown','none','nan','na','n/a','not_available','null','.'}


def memberships(hgnc,hcop,minimum_sources=3):
    """Return exact mouse identifier -> conservative union of supported groups.

    Repeated database names within HCOP support strings count ONCE. Evidence
    for a pair is combined across duplicate records, never across different genes.
    """
    groups={}
    for row in hgnc.itertuples(index=False):
        if row.hgnc_id in groups:raise ValueError('Duplicate HGNC identifier')
        groups[row.hgnc_id]={x for x in str(row.gene_group_id).split('|') if x.isdigit()}
    evidence=defaultdict(set)
    for row in hcop.itertuples(index=False):
        if row.hgnc_id not in groups:continue
        key=(row.hgnc_id,str(row.mouse_ensembl_gene),str(row.mouse_symbol).lower())
        evidence[key].update(x.strip() for x in str(row.support).split(',') if x.strip())
    lookup=defaultdict(set);orthologs=defaultdict(set)
    for (human,ensembl,symbol),support in evidence.items():
        if len(support)<minimum_sources:continue
        for namespace,value in [('id',ensembl),('symbol',symbol)]:
            if value.lower() in MISSING:continue
            lookup[(namespace,value)].update(groups[human])
            orthologs[(namespace,value)].add(human)
    return lookup,orthologs


def map_units(metadata,lookup,orthologs):
    columns=['biological_unit','gene_id','gene_name']
    # Outcome fields are deliberately outside the mapping interface.
    genes=metadata[columns].drop_duplicates();result=[]
    for unit,part in genes.groupby('biological_unit',sort=True):
        groups=set();human=set();keys=set()
        for row in part.itertuples(index=False):
            if str(row.gene_id).lower() not in MISSING:
                keys.add(('id',str(row.gene_id).split('.')[0]))
            if str(row.gene_name).lower() not in MISSING:
                keys.add(('symbol',str(row.gene_name).strip().lower()))
        for key in keys:
            groups.update(lookup.get(key,()));human.update(orthologs.get(key,()))
        result.append({'biological_unit':unit,'group_ids':'|'.join(sorted(groups)),
            'human_ortholog_ids':'|'.join(sorted(human)),
            'mapped':bool(groups),'status':'annotated_group' if groups else
                ('supported_ortholog_without_group' if human else 'no_supported_ortholog'),
            'matched_mouse_keys':'|'.join(':'.join(k) for k in sorted(keys) if k in orthologs)})
    return pd.DataFrame(result)


def merge_family_components(inventory,mapping):
    units=inventory[['biological_unit','component']].drop_duplicates()
    if units.biological_unit.duplicated().any():raise ValueError('Unit has multiple primary components')
    units=units.merge(mapping,on='biological_unit',validate='one_to_one')
    if len(units)!=inventory.biological_unit.nunique():raise ValueError('Missing unit annotation')
    parents={c:c for c in units.component.unique()}
    def find(c):
        while parents[c]!=c:parents[c]=parents[parents[c]];c=parents[c]
        return c
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b:parents[max(a,b)]=min(a,b)
    first={};edges=[]
    for row in units.sort_values('biological_unit').itertuples(index=False):
        for group in filter(None,row.group_ids.split('|')):
            if group in first:
                if find(row.component)!=find(first[group]):
                    edges.append({'group_id':group,'left':find(row.component),'right':find(first[group])})
                union(row.component,first[group])
            else:first[group]=row.component
    final={c:find(c) for c in parents}
    # A linked family component is eligible only when every constituent unit is annotated.
    units['family_component']=units.component.map(final)
    complete=units.groupby('family_component').mapped.all().to_dict()
    result=inventory.copy();result['family_component']=result.component.map(final)
    result['family_eligible']=result.family_component.map(complete)
    return result,edges


def build_gene_family_sensitivity():
    config_path=ROOT/'configs/mechanism_v2/gene_family_design.json'
    config=json.loads(config_path.read_text())
    for name in ['hgnc','hcop']:
        if sha256(ROOT/config[name]['path'])!=config[name]['sha256']:raise ValueError('External ontology hash mismatch')
    hgnc=pd.read_csv(ROOT/config['hgnc']['path'],sep='\t',dtype=str,keep_default_na=False)
    hcop=pd.read_csv(ROOT/config['hcop']['path'],sep='\t',compression='gzip',dtype=str,keep_default_na=False)
    lookup,orthologs=memberships(hgnc,hcop,config['minimum_distinct_orthology_sources'])
    rows=load_development()
    split_path=ROOT/'results/mechanism_v2/manifests/splits_all_alleles95.json'
    split=json.loads(split_path.read_text())
    if sha256(ROOT/split['outer'])!=split['outer_sha256']:raise ValueError('Primary split changed')
    inventory=pd.read_csv(ROOT/split['outer']);validate_split_alignment(rows,inventory)
    mapping=map_units(rows[['biological_unit','gene_id','gene_name']],lookup,orthologs)
    result,edges=merge_family_components(inventory,mapping)
    selected=result.family_eligible.to_numpy(bool);groups=result.family_component.to_numpy()
    result['family_outer_fold']=-1
    folds=balanced_group_folds(rows.loc[selected],groups[selected],config['outer_folds'],config['seed'])
    result.loc[selected,'family_outer_fold']=folds
    inner={}
    for outer in range(config['outer_folds']):
        mask=selected & result.family_outer_fold.ne(outer).to_numpy()
        assignments=balanced_group_folds(rows.loc[mask],groups[mask],config['inner_folds'],config['seed']+outer+1)
        inner[str(outer)]=dict(zip(groups[mask],map(int,assignments)))
    mapping_path='results/mechanism_v2/splits/gene_group_annotations.csv'
    result_path='results/mechanism_v2/splits/gene_group_sensitivity.csv'
    csv(mapping_path,mapping);csv(result_path,result)
    summary={'configuration_sha256':sha256(config_path),'code_sha256':sha256(ROOT/'src/mechanism_v2/gene_families.py'),
        'primary_split_manifest_sha256':sha256(split_path),'outer':result_path,'outer_sha256':sha256(ROOT/result_path),
        'annotation':mapping_path,'annotation_sha256':sha256(ROOT/mapping_path),
        'original_units':len(mapping),'annotated_units':int(mapping.mapped.sum()),
        'primary_components':int(result.component.nunique()),
        'eligible_family_components':int(result.loc[selected,'family_component'].nunique()),
        'eligible_rows':int(selected.sum()),'excluded_rows':int((~selected).sum()),
        'source_eligible_units':result.loc[selected].groupby('dataset').biological_unit.nunique().to_dict(),
        'source_excluded_units':result.loc[~selected].groupby('dataset').biological_unit.nunique().to_dict(),
        'annotation_status':mapping.status.value_counts().to_dict(),'family_merge_edges':edges,
        'inner_component_folds':inner,'outcomes_used':False,'primary_folds_modified':False,
        'limitation':config['interpretation']}
    write_json('results/mechanism_v2/manifests/splits_gene_group_sensitivity.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k not in ['inner_component_folds','family_merge_edges']},indent=2),flush=True)


if __name__=='__main__':build_gene_family_sensitivity()
