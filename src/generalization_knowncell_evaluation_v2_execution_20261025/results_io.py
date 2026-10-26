"""Lossless deterministic storage for the unchanged complete evaluator result."""
import gzip
import os
from . import common as c
from src.generalization_knowncell_joint_campaign_20261023 import contracts as lc
HEAVY=('all_decisions','primary_decisions','unmatched_decisions')
MAX_RAW=128*2**20
MAX_GZIP=32*2**20


def summary(value):return {key:item for key,item in value.items() if key not in HEAVY}


def encode(value):
    raw=lc.canonical_bytes(value);assert len(raw)<=MAX_RAW
    compressed=gzip.compress(raw,compresslevel=9,mtime=0);assert len(compressed)<=MAX_GZIP
    return compressed,{'gzip_sha256':c.sha(compressed),'canonical_json_sha256':c.sha(raw),
        'gzip_bytes':len(compressed),'canonical_json_bytes':len(raw),'compression':'gzip_level9_mtime0',
        'complete_original_evaluator_result_preserved':True}


def decode(compressed,certificate):
    import io
    assert len(compressed)==certificate['gzip_bytes']<=MAX_GZIP and c.sha(compressed)==certificate['gzip_sha256']
    with gzip.GzipFile(fileobj=io.BytesIO(compressed),mode='rb') as stream:raw=stream.read(MAX_RAW+1)
    assert len(raw)==certificate['canonical_json_bytes']<=MAX_RAW and c.sha(raw)==certificate['canonical_json_sha256']
    value=lc.strict_json(raw);assert lc.canonical_bytes(value)==raw
    return value


def persist(value):
    compressed,certificate=encode(value)
    with c.EVALUATION_DATA.open('xb') as stream:stream.write(compressed);stream.flush();os.fsync(stream.fileno())
    return certificate
