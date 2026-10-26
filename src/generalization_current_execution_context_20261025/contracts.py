"""Pure JSON, bits and reference contracts. None grants stage authority."""
import hashlib
import json
import math
import struct
from pathlib import PurePosixPath


def digest(raw):
    assert type(raw) is bytes
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)+'\n').encode('utf8')


def sha(value):
    assert type(value) is str and len(value)==64 and all(x in '0123456789abcdef' for x in value)
    return value


def decode(raw):
    assert type(raw) is bytes and len(raw)<=64*2**20
    def unique(items):
        result={}
        for key,value in items:
            assert key not in result,'Duplicate JSON key'
            result[key]=value
        return result
    value=json.loads(raw,object_pairs_hook=unique,
        parse_constant=lambda value:(_ for _ in ()).throw(AssertionError('Nonfinite JSON token')))
    assert type(value) is dict
    canonical(value)
    return value


def relative(value):
    assert type(value) is str and value and '\\' not in value and ':' not in value
    p=PurePosixPath(value)
    assert not p.is_absolute() and p.parts and all(x not in ('.','..') for x in p.parts)
    assert p.as_posix()==value
    return value


def pack_labels(ids,values):
    assert type(ids) is list and type(values) is list and len(ids)==len(values)==len(set(ids))
    assert all(type(x) is str and x for x in ids)
    assert all(type(x) is float and math.isfinite(x) for x in values)
    return b''.join(struct.pack('<d',value) for value in values)


def reference_contract(value):
    fields={'status','file_sha256','actual_prefit_relative_path','actual_prefit_commit',
        'projection_admission_relative_path','projection_admission_commit','historical_runtime_anchor_sha256',
        'historical_native_profile_origin_sha256','input_authority_granted_here'}
    assert type(value) is dict and set(value)==fields
    assert value['status']=='FROZEN_HISTORICAL_SCIENTIFIC_REFERENCE_NOT_CURRENT_RUNTIME_ADMISSION'
    assert set(value['file_sha256'])=={'metadata','array','labels','prefit','projection'}
    for expected in value['file_sha256'].values():sha(expected)
    for key in ('actual_prefit_relative_path','projection_admission_relative_path'):relative(value[key])
    for key in ('actual_prefit_commit','projection_admission_commit'):
        commit=value[key];assert type(commit) is str and len(commit)==40 and all(x in '0123456789abcdef' for x in commit)
    sha(value['historical_runtime_anchor_sha256']);sha(value['historical_native_profile_origin_sha256'])
    assert value['input_authority_granted_here'] is False
    return value


def check_supplied(raws,reference):
    reference_contract(reference)
    assert set(raws)==set(reference['file_sha256'])
    for name,raw in raws.items():assert digest(raw)==reference['file_sha256'][name],name
    return {name:decode(raw) for name,raw in raws.items()}
