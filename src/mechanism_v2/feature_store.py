"""Hash-verified, explicitly named feature blocks for development only."""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
from .io import ROOT,load_development,sha256
from .forensics import archived_functions
from .groups import assert_partition_disjoint

BLOCK_MANIFESTS={
    'rbp_delta':'rbp_signed_delta_manifest.json',
    'bert_pooled_delta':'bert_pooled_allele_delta_manifest.json',
    'structure_delta':'structure_delta_full_manifest.json',
    'processing_delta':'processing_nuisance_delta_manifest.json',
    'motif_delta':'motif_accessibility_delta_full_manifest.json',
    'trans_aligned':'trans_aligned_interactions_manifest.json',
}
DIMENSIONS={'geometry':28,'rbp_delta':412,'bert_pooled_delta':128,
    'structure_delta':18,'processing_delta':8,'motif_delta':8,'trans_aligned':4}


def checked_array(record):
    path=(ROOT/record['path']).resolve()
    if not path.is_relative_to((ROOT/'data/interim/mechanism_v2').resolve()):
        raise PermissionError('Feature array outside new namespace')
    if sha256(path)!=record['sha256']:raise ValueError('Feature hash mismatch')
    value=np.load(path,mmap_mode='r',allow_pickle=False)
    if list(value.shape)!=record['shape'] or value.dtype.name!=record['dtype']:
        raise ValueError('Feature shape/dtype mismatch')
    if not np.isfinite(value).all():raise ValueError('Non-finite feature')
    return value


def validate_split_alignment(rows,inventory):
    keys=['dataset','biological_unit','decision_set_id','candidate_id','feature_row']
    if not rows[keys].reset_index(drop=True).equals(inventory[keys].reset_index(drop=True)):
        raise ValueError('Split inventory differs from the certified row order')
    if inventory[['component','outer_fold']].isna().any().any():raise ValueError('Missing split assignment')
    assert_partition_disjoint(rows,inventory.outer_fold,inventory.component)


class FeatureStore:
    def __init__(self):
        self.rows=load_development()
        design=json.loads((ROOT/'configs/mechanism_v2/localization_design.json').read_text())
        self.design=design
        self.split=json.loads((ROOT/design['split_manifest']).read_text())
        if sha256(ROOT/self.split['outer'])!=self.split['outer_sha256']:
            raise ValueError('Split file hash mismatch')
        inventory=pd.read_csv(ROOT/self.split['outer'])
        validate_split_alignment(self.rows,inventory)
        self.rows['component']=inventory.component
        self.rows['outer_fold']=inventory.outer_fold
        self.rows['row_id']=np.arange(len(self.rows))
        self.feature_rows=self.rows.feature_row.to_numpy(int)
        if self.feature_rows.min()!=0 or self.feature_rows.max()!=62664:
            raise ValueError('Unexpected intervention row axis')
        self.blocks={};self.records={}
        for name,filename in BLOCK_MANIFESTS.items():
            path=ROOT/'results/mechanism_v2/features'/filename
            record=json.loads(path.read_text());value=checked_array(record)
            expected_rows=len(self.rows) if name=='trans_aligned' else 62665
            if value.shape!=(expected_rows,DIMENSIONS[name]):raise ValueError(f'Unexpected block dimensions: {name}')
            self.blocks[name]=value;self.records[name]=record
        self.blocks['geometry']=archived_functions()['geometry_features'](self.rows)
        if self.blocks['geometry'].shape!=(len(self.rows),DIMENSIONS['geometry']):
            raise ValueError('Geometry definition changed')

    def matrix(self,family):
        names=self.design['families'][family]
        blocks=[self.blocks[name] if name in {'geometry','trans_aligned'}
                else self.blocks[name][self.feature_rows] for name in names]
        x=np.column_stack(blocks).astype(np.float32,copy=False)
        columns=[f'{name}:{j:03d}' for name in names for j in range(DIMENSIONS[name])]
        return x,columns

    def train_frame(self,indices):
        frame=self.rows.iloc[indices].copy().reset_index(drop=True)
        # Cross-source gene copies remain ONE independent unit for weighting.
        frame['biological_unit']=frame.component
        return frame
