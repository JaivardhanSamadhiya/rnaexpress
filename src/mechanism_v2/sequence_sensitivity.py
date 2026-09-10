"""Harder all-allele 90% sequence sensitivity; never replaces primary folds."""
import json
import numpy as np
import pandas as pd
from .io import ROOT,load_development,sha256,write_json
from .forensics import csv
from .sequence_leakage import exact_near_components
from .feature_store import validate_split_alignment
from .splits import balanced_group_folds


def build_all_allele90():
    rows=load_development()
    source=ROOT/'results/mechanism_v2/manifests/splits_all_alleles95.json'
    manifest=json.loads(source.read_text())
    if sha256(ROOT/manifest['outer'])!=manifest['outer_sha256']:raise ValueError('Primary split changed')
    inventory=pd.read_csv(ROOT/manifest['outer']);validate_split_alignment(rows,inventory)
    groups=inventory.component.to_numpy()
    alleles=pd.concat([pd.DataFrame({'sequence':rows.parent_sequence,'component':groups}),
        pd.DataFrame({'sequence':rows.mutant_sequence,'component':groups})]).drop_duplicates()
    _,audit=exact_near_components(alleles.sequence.tolist(),alleles.component.tolist(),threshold=.90,progress=True)
    final=np.array([audit['component_mapping'][str(g)] for g in groups])
    folds=balanced_group_folds(rows,final,5,20260914)
    result=inventory.copy();result['sequence90_component']=final;result['sequence90_outer_fold']=folds
    inner={}
    for outer in range(5):
        mask=folds!=outer
        assignment=balanced_group_folds(rows.loc[mask],final[mask],3,20260915+outer)
        inner[str(outer)]=dict(zip(final[mask],map(int,assignment)))
    path='results/mechanism_v2/splits/all_alleles90.csv';csv(path,result)
    write_json('results/mechanism_v2/manifests/splits_all_alleles90.json',{
        'primary_manifest_sha256':sha256(source),'audit':audit,'inner_component_folds':inner,
        'outer':path,'outer_sha256':sha256(ROOT/path),'outcomes_used':False,'primary_folds_modified':False,
        'code_sha256':sha256(ROOT/'src/mechanism_v2/sequence_sensitivity.py'),
        'auditor_code_sha256':sha256(ROOT/'src/mechanism_v2/sequence_leakage.py')})
    print(f'All-allele 90% sensitivity complete: {audit["final_components"]} connected components',flush=True)
