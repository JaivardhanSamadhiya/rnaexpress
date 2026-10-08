"""Metadata-only immutable preparation; no native probe entrypoint exists."""
import ast
import json
from . import common as c
from . import token_math as m


def run():
    c.clean_imports()
    target=c.OUT/'preparation_manifest.json';assert not target.exists()
    resource=c.readj(c.OLD_OUT/'resource_audit.json')
    assert resource['status']=='PASS' and resource['author_archive_identity']=='All selected checkpoint/tokenizer members byte-identical'
    assert resource['cached_files']['pytorch_model.bin']['sha256']==c.CHECKPOINT_SHA
    assert resource['cached_files']['pytorch_model.bin']['bytes']==78883755
    config=c.readj(c.MODEL/'config.json');vocab=(c.MODEL/'vocab.txt').read_text().splitlines()
    assert vocab==c.VOCAB and config['architectures']==['BertForMaskedLM']
    assert (config['hidden_size'],config['num_hidden_layers'],config['vocab_size'])==(512,6,10)
    assert config['hidden_act']=='gelu' and config['layer_norm_eps']==1e-12
    for name in ('config.json','vocab.txt','tokenizer_config.json','tokenizer.json','special_tokens_map.json'):
        assert c.sha256(c.MODEL/name)==resource['cached_files'][name]['sha256']
    context_path=c.ROOT/'artifacts/generalization_20261007/reporter_context_metadata.json'
    assert c.sha256(context_path)=='e7ee4fea706d3b7e611f63d491304cfe835efcd3c9b6a9a4f0282abf384f725c'
    context=c.readj(context_path)['local_design'];original=m.synthetic_sequences(context['left_20nt_dna'],context['right_20nt_dna'])
    pairs=[m.request(original[i],original[i+1]) for i in range(0,16,2)];extra=m.additional_synthetic_requests(original)
    c.jsave(c.ART/'synthetic_inventory.json',{'status':'FIXED_INVENTED_ONLY','original_alleles':original,
        'original_sequence_sha256':[__import__('hashlib').sha256(s.encode()).hexdigest() for s in original],
        'original_one_edit_pairs':[{'parent':r.parent,'mutant':r.mutant,'positions':r.positions,'masked_context_sha256':r.context_sha256} for r in pairs],
        'additional_boundary_multisite_pairs':[{'parent':r.parent,'mutant':r.mutant,'positions':r.positions,'masked_context_sha256':r.context_sha256} for r in extra],
        'original16_preserved':True,'project_alleles':0,'synthetic_native_calls':0})
    old_source=c.ROOT/'src/generalization_splicebert_20261007/backend_probe.py'
    tree=ast.parse(old_source.read_text());assert any(isinstance(n,ast.FunctionDef) and n.name=='synthetic_sequences' for n in tree.body)
    backend=c.readj(c.OLD_OUT/'backend_synthetic_receipt.json');compat=c.readj(c.REPAIR_OUT/'backend_compatibility_receipt.json');proof=c.readj(c.REPAIR_OUT/'numpy_import_receipt.json')
    scientific_receipt=c.ROOT/'artifacts/generalization_splicebert_runtime_compatibility_20261007/scientific_runtime_receipt.json'
    observed={k:compat[k] for k in ('IR_xml_sha256','IR_bin_sha256','repair_preparation_sha256')}
    observed.update({'numpy_origin':proof['numpy_origin'],'native_core_origin':proof['native_core_origin'],
        'native_core_sha256':proof['native_core_sha256'],'backend_sha256':c.sha256(c.OLD_OUT/'backend_synthetic_receipt.json'),
        'numpy_proof_sha256':c.sha256(c.REPAIR_OUT/'numpy_import_receipt.json'),'scientific_runtime_receipt_sha256':c.sha256(scientific_receipt)})
    assert c.certify_encoder_metadata(backend,compat,proof,observed)
    assert [__import__('hashlib').sha256(s.encode()).hexdigest() for s in original]==backend['synthetic_sequence_sha256']
    tests=c.readj(c.OUT/'synthetic_tests_receipt.json');sources={p.relative_to(c.ROOT).as_posix():c.sha256(p) for p in sorted(c.SRC.glob('*.py'))}
    assert tests['status']=='PASS' and tests['source_hashes']==sources and tests['plan_sha256']==c.sha256(c.REP/'plan.md')
    assert tests['actual_numeric_imports']==tests['actual_model_imports']==tests['checkpoint_loads']==tests['model_calls']==0
    paths=[p for folder in (c.SRC,c.ART,c.OUT,c.REP) for p in folder.rglob('*') if p.is_file()]
    paths += [c.OLD_OUT/'resource_audit.json',c.OLD_OUT/'backend_preparation_manifest.json',c.OLD_OUT/'backend_synthetic_receipt.json',
        c.REPAIR_OUT/'preparation_manifest.json',c.REPAIR_OUT/'backend_compatibility_receipt.json',c.REPAIR_OUT/'numpy_import_receipt.json',scientific_receipt,
        old_source,c.ROOT/'src/generalization_splicebert_runtime_compatibility_20261007/launcher.py',context_path,
        c.ROOT/'.transformers_runtime/transformers/models/bert/modeling_bert.py',c.ROOT/'.transformers_runtime/transformers/configuration_utils.py',
        c.ROOT/'src/modeling/splicebert_features.py',c.ROOT/'src/modeling/utrbert_features.py']
    paths += [c.MODEL/n for n in ('config.json','vocab.txt','tokenizer_config.json','tokenizer.json','special_tokens_map.json')]
    c.jsave(target,{'status':'FROZEN_MASKED_LIKELIHOOD_PREPARATION_ONLY','files':{p.relative_to(c.ROOT).as_posix():c.sha256(p) for p in sorted(set(paths))},
        'checkpoint_bytes_read':0,'checkpoint_loads':0,'actual_numeric_imports':0,'actual_model_imports':0,'native_calls':0,
        'metadata_backend_and_repair_PASS':True,'actual_MLM_head_and_ties_verified':False,'new_native_probe_authorized':False,
        'future_guard_requires_actual_runtime_and_IR_rehash':True,'root_review_commit_and_new_explicit_start_required':True,
        'original_synthetic_alleles':16,'shared_original_masked_pairs':8,'additional_fixed_multisite_pairs':20,
        'MLM_conversions':0,'candidate_backend':'unchanged accepted encoderIR + original independently evaluated NumPyMLMhead; stock localMLM synthetic reference',
        'scope':'block-masked conditional marginal surrogate, not joint likelihood/effect/localization probability',
        'project_sequences_read':0,'outcomes_read':False,'fits':0,'feature_production_authorized':False})
    c.clean_imports();print('Masked-likelihood preparation ready; native probe still unauthorized',c.sha256(target),flush=True)


if __name__=='__main__':run()
