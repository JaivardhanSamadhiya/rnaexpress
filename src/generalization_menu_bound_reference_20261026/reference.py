"""Derive source pair weights/scaling internally before scalar evaluation.

The frozen lower-level arithmetic remains unchanged. Callers cannot inject
pair_rows, weights, a menu catalog or operative scaling at this entry point.
This is a reference calculation, not actual data/runtime/execution admission.
"""
import hashlib
import json
import math
from src.generalization_menu_comparison_core_20261026 import layout, scalar


def _digest(value):
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def evaluate(*, beta, features, effects, source_metadata, sampled_pairs,
             arm, penalty, recorded_scaling=None):
    """Independently reconstruct the source-only roster, masses and scaler.

    Original seeded sampler equivalence and correct outer/inner source IDs
    remain external obligations of the future admitted producer. This function
    certifies neither. Small supplied fixtures have no biological authority.
    """
    rows=layout.metadata(source_metadata)
    x=scalar.matrix(features); y=tuple(float(value) for value in effects)
    layout.require(len(rows)==len(x)==len(y), 'source metadata/features/effects row counts differ')
    catalog=layout.menus(rows,range(len(rows)))
    pairs=scalar.pair_contract(y,catalog,sampled_pairs)
    source_scale=scalar.scaling(x,pairs,catalog)
    if recorded_scaling is not None:
        for key in ('active','scale','mean','pair_rms'):
            layout.require(key in recorded_scaling and len(recorded_scaling[key])==len(x[0]),
                           'recorded scaling shape differs: '+key)
            if key=='active':
                layout.require(all(type(value) is bool for value in recorded_scaling[key]) and
                               tuple(recorded_scaling[key])==source_scale[key],
                               'recorded source support differs')
            else:
                layout.require(all(math.isfinite(value) and abs(value-want)<1e-9
                                   for value,want in zip(recorded_scaling[key],source_scale[key])),
                               'recorded source scaling differs: '+key)
    loss,gradient=scalar.objective(beta,x,y,catalog,pairs,source_scale,arm=arm,penalty=penalty)
    return {'status':'SOURCE_BOUND_SCALAR_REFERENCE_NOT_DATA_OR_NATIVE_ADMISSION',
            'objective':loss,'gradient':gradient,'source_scaling':source_scale,
            'source_rows':len(rows),'source_contexts':len(catalog),'valid_source_pairs':len(pairs),
            'source_metadata_sha256':_digest(rows),'supplied_sampled_roster_sha256':_digest(sampled_pairs),
            'caller_pair_rows_or_weights_accepted':False,'recorded_scaling_used_for_computation':False,
            'original_numpy_sampler_equivalence_certified':False,'input_admission_certified':False,
            'fits_or_refits':0}
