"""Separate outcome-free extraction and comparative-fit freezes."""
from .common import *
import sys

def run(stage):
    assert stage in ('production','prefit')
    assert not any((OUT/t/'fits').exists() for t in TRACKS)
    from src.generalization_20261007.verify import preservation
    preservation()
    paths = sorted(p for directory in (SRC,REP) for p in directory.glob('*') if p.is_file())
    paths += [ROOT/'artifacts/generalization_20261007/reporter_context_metadata.json',
              ROOT/'results/generalization_20261007/prefit_manifest.json',
              ROOT/'artifacts/generalization_20261007/delivery_receipt.json',
              ROOT/'results/probabilistic_ranking_20260928/candidate_index.csv',
              ROOT/'results/v4_phaseB/openvino_backend_equivalence.json']
    paths += sorted(p for p in OUT.glob('*') if p.is_file() and p.name not in ('feature_production_manifest.json','prefit_manifest.json'))
    paths += sorted(p for p in ART.glob('*') if p.is_file() and p.suffix in ('.npz','.npy','.gz','.json'))
    assert readj(OUT/'tests_receipt.json')['status'] == 'PASS'
    assert readj(OUT/'short_feature_receipt.json')['status'] == 'PASS'
    from . import route_structure as structure
    paths += [Path(structure.RNA.__file__),Path(structure.RNA._RNA.__file__)]
    from .bert_backend_probe import MODEL,IR
    paths += [MODEL/'pytorch_model.bin',MODEL/'config.json',MODEL/'vocab.txt',MODEL/'special_tokens_map.json',MODEL/'tokenizer_config.json',IR,IR.with_suffix('.bin')]
    if stage == 'production':
        assert readj(OUT/'structure_parallel_benchmark_receipt.json')['status'] == 'PASS'
        assert readj(OUT/'bert_synthetic_benchmark.json')['status'] == 'PASS'
        assert readj(OUT/'bert_checkpoint_provenance.json')['author_weight_identity'] == 'CERTIFIED_BYTE_IDENTICAL'
        assert (ART/'bert_global_projection.npy').exists() and (ART/'bert_local_projection.npy').exists()
        integrity=readj(OUT/'bert_runtime_integrity.json')
        paths += [ROOT/name for name in integrity['files']]
        filename='feature_production_manifest.json'
    else:
        production_check()
        assert readj(OUT/'prepare_receipt.json')['status'] == 'PASS'
        paths += [OUT/'feature_production_manifest.json']
        filename='prefit_manifest.json'
    assert not (OUT/filename).exists(), 'Preserve existing freeze'
    paths = sorted(set(paths))
    jsave(OUT/filename, {'files':{p.relative_to(ROOT).as_posix():sha256(p) for p in paths},
        'status':'FROZEN_'+stage.upper(), 'no_comparative_fits_exist':True,
        'protected_outcomes_opened':False, 'independent_confirmation':False,
        'workers_structure':2, 'threads_bert':4, 'batch_bert':8})
    print('Frozen',stage,len(paths),'files; commit before execution',flush=True)

if __name__ == '__main__': run(sys.argv[1])
