"""Additional prefit integrity checks, preserving the production-frozen assembler."""
from .common import *

def verify_blocks():
    receipt=readj(OUT/'bert_features_receipt.json')
    assert receipt['status']=='PASS'
    for name,key in [('bert_features.npz','bert_features_sha256'),('lookup_features.npz','lookup_features_sha256')]:
        assert sha256(ART/name)==receipt[key], name
    for shard in receipt['compact_shards']:
        assert sha256(ROOT/shard['path'])==shard['sha256'], shard['path']

def run():
    production_check()
    verify_blocks()
    from .assemble import run as assemble
    assemble()
    jsave(OUT/'assembly_integrity_receipt.json', {'status':'PASS', 'feature_blocks_match_producer_receipts':True,
        'verified_compact_shards':len(readj(OUT/'bert_features_receipt.json')['compact_shards']),
        'code_sha256':sha256(Path(__file__))})

if __name__=='__main__': run()
