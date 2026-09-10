"""Compact external availability-aligned cis-delta interaction summaries."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from .io import ROOT,load_development,sha256,write_json
from .features import array_file
from .preservation import preserve

DESIGN_PATH=ROOT/'configs/mechanism_v2/trans_context_design.json'


def aligned_interactions(deltas,protein_names,expression,cell_names):
    deltas=np.asarray(deltas,float)
    if deltas.ndim!=3 or deltas.shape[1:]!=(len(protein_names),4) or len(cell_names)!=len(deltas):
        raise ValueError('Cis/trans input shape mismatch')
    if not np.isfinite(deltas).all():raise ValueError('Non-finite cis deltas')
    if len(set(protein_names))!=len(protein_names):raise ValueError('Repeated protein channel')
    if expression[['human_rbp','cell_line']].duplicated().any():raise ValueError('Ambiguous external expression channel')
    eligible=[];excluded=[];values={}
    for protein in protein_names:
        table=expression[expression.human_rbp.eq(protein)].set_index('cell_line')
        if not {'CAD','N2A'}<=set(table.index):
            excluded.append({'protein':protein,'reason':'missing_external_cell'});continue
        rows=table.loc[['CAD','N2A']]
        numbers=rows.compartment_balanced_expression_proxy.to_numpy(float)
        if not rows.context_eligible.eq(True).all() or not np.isfinite(numbers).all() or (numbers<0).any():
            excluded.append({'protein':protein,'reason':'not_eligible_or_invalid_proxy'});continue
        eligible.append(protein);values[protein]=numbers
    if not eligible:raise ValueError('No validated external availability channels')
    idx=[protein_names.index(p) for p in eligible]
    proxy=np.array([values[p] for p in eligible])
    if (proxy.sum(axis=0)<=0).any():raise ValueError('No positive external availability')
    weights=proxy/proxy.sum(axis=0,keepdims=True)
    if not set(cell_names)<=set(['CAD','N2A']):raise PermissionError('Unsupported cell context; no zero-fill fallback')
    out=np.empty((len(deltas),4),np.float32)
    for j,cell in enumerate(['CAD','N2A']):
        mask=np.array(cell_names)==cell
        out[mask]=np.einsum('nrf,r->nf',deltas[mask][:,idx],weights[:,j])
    return out,{'eligible_proteins':eligible,'excluded':excluded,'weights':weights.tolist(),
        'weight_cell_order':['CAD','N2A']}


def build_trans_context():
    preserve();design=json.loads(DESIGN_PATH.read_text())
    rows=load_development();record=json.loads((ROOT/'results/mechanism_v2/features/rbp_signed_delta_manifest.json').read_text())
    if sha256(ROOT/record['path'])!=record['sha256']:raise ValueError('RBP delta input changed')
    values=np.load(ROOT/record['path'],mmap_mode='r')
    dictionary_path=ROOT/'results/finalshot/rbp_feature_dictionary.csv'
    dictionary=pd.read_csv(dictionary_path).groupby('group_index',sort=True).first()
    proteins=dictionary.human_rbp.tolist()
    expression_path=ROOT/'results/finalshot/rbp_expression_proxy.csv'
    expression=pd.read_csv(expression_path)
    aliases=design['cell_aliases'];cells=rows.cell_type.map(aliases)
    if cells.isna().any():raise PermissionError('Unregistered source cell; cannot infer trans availability')
    result,audit=aligned_interactions(values[rows.feature_row.to_numpy(int)].reshape(-1,103,4),proteins,expression,cells.to_numpy())
    metadata=array_file('data/interim/mechanism_v2/trans_aligned_interactions.npy',result)
    metadata.update({'axis':'certified candidate rows, not unique interventions','configuration':design,
        'configuration_sha256':sha256(DESIGN_PATH),'code_sha256':sha256(Path(__file__)),
        'expression_sha256':sha256(expression_path),'dictionary_sha256':sha256(dictionary_path),
        'rbp_delta_sha256':record['sha256'],'candidate_rows_sha256':sha256(ROOT/'results/v4_phaseB/model_candidate_rows.csv.gz'),
        'audit':audit,'localization_outcomes_used':False})
    write_json('results/mechanism_v2/features/trans_aligned_interactions_manifest.json',metadata)
    print(f'External aligned interactions: {result.shape}, {len(audit["eligible_proteins"])} eligible protein channels',flush=True)
    return metadata
