"""Metadata/source inventory only, no numerical imports or checkpoint load."""
from __future__ import annotations
import ast
import sys
from pathlib import Path
from . import common as c
from .probe import synthetic_requests

def run():
 c.clean_imports();c.own_fresh();assert not c.MANIFEST.exists(),'Preserve previous preparation'
 backend,compat,proof=c.prerequisite_metadata();original,requests=synthetic_requests(c.readj(c.INVENTORY))
 tests=c.readj(c.TESTS);assert tests['status']=='PASS' and tests['actual_numeric_imports']==tests['actual_model_imports']==tests['checkpoint_loads']==tests['model_calls']==0
 sources={p.relative_to(c.ROOT).as_posix():c.sha256(p) for p in sorted(c.SRC.glob('*.py'))}
 assert tests['source_hashes']==sources and tests['plan_sha256']==c.sha256(c.PLAN)
 for path in c.SRC.glob('*.py'):ast.parse(path.read_text())
 for path in (c.FEASIBILITY,c.f.OLD_OUT/'backend_preparation_manifest.json',c.f.REPAIR_OUT/'preparation_manifest.json'):
  c.committed(path)
  for name,expected in c.readj(path)['files'].items():
   if (c.ROOT/name).resolve()==c.CHECKPOINT.resolve():
    assert expected==c.f.CHECKPOINT_SHA # Never read/load checkpoint tensors here.
   else:assert c.sha256(c.ROOT/name)==expected,name
 prefixes={}
 for key,path in c.RUNTIME_ROOTS.items():
  files=c.file_inventory(path)
  prefixes[key]={'path':str(path.resolve()),'files':files,'file_count':len(files),'total_bytes':sum((path/name).stat().st_size for name in files)}
  print('Masked preparation complete runtime metadata',key,len(files),'files',flush=True)
 # Validate current observed complete roots against all earlier certified
 # subsets; the complete additional roots are explicitly source snapshots.
 for key,receipt_path in (('scientific',c.SCIENTIFIC),('torch',c.f.OLD_OUT/'cpu_runtime_extraction_receipt.json'),('dependencies',c.f.OLD_OUT/'dependency_runtime_receipt.json')):
  old=c.readj(receipt_path);assert old['status']=='PASS' and prefixes[key]['files']==old['files']
 ov=c.readj(c.ROOT/'results/generalization_next_20261007/bert_runtime_integrity.json')
 assert {str((c.RUNTIME_ROOTS['openvino']/name).relative_to(c.ROOT).as_posix()):value for name,value in prefixes['openvino']['files'].items()}==ov['files']
 scientific=c.readj(c.SCIENTIFIC)
 for name,expected in scientific['python_native_files'].items():assert c.sha256(name)==expected
 assert Path(sys.executable).resolve()==Path(scientific['python_executable']).resolve()
 c.jsave(c.ART/'runtime_inventory.json',{'status':'COMPLETE_OBSERVED_RUNTIME_SOURCE_SNAPSHOT','prefixes':prefixes,
  'python_executable':str(Path(sys.executable).resolve()),'python_native_files':scientific['python_native_files'],
  'whole_runtime_is_reproducible_build':False,'original_wheel_parity_prerequisite_receipts':[str(p.relative_to(c.ROOT)) for p in c.PREREQUISITES if 'runtime' in p.name or 'parity' in p.name],
  'numeric_or_model_packages_imported':False,'checkpoint_loads':0})
 own=[p for folder in (c.SRC,c.ART,c.OUT,c.REP) for p in folder.rglob('*') if p.is_file()]
 paths=own+c.PREREQUISITES+[c.INVENTORY,
  c.ROOT/'src/generalization_splicebert_20261007/backend_probe.py',c.ROOT/'src/generalization_splicebert_20261007/resources.py',
  c.ROOT/'src/generalization_splicebert_runtime_compatibility_20261007/launcher.py',c.ROOT/'src/generalization_splicebert_runtime_compatibility_20261007/common.py',
  c.ROOT/'.transformers_runtime/transformers/models/bert/modeling_bert.py',c.ROOT/'.transformers_runtime/transformers/activations.py',
  c.ROOT/'.transformers_runtime/transformers/configuration_utils.py']
 paths.extend(c.f.SRC.glob('*.py'))
 paths.extend(c.f.MODEL/name for name in ('config.json','vocab.txt','tokenizer.json','tokenizer_config.json','special_tokens_map.json'))
 assert c.CHECKPOINT not in paths and c.ARCHIVE not in paths
 c.jsave(c.MANIFEST,{'status':'FROZEN_SYNTHETIC_MASKED_BACKEND_PREPARATION','files':{p.relative_to(c.ROOT).as_posix():c.sha256(p) for p in sorted(set(paths))},
  'own_committed_files':[p.relative_to(c.ROOT).as_posix() for p in sorted(set(own))],
  'committed_prerequisites':[p.relative_to(c.ROOT).as_posix() for p in (c.FEASIBILITY,c.f.OLD_OUT/'backend_preparation_manifest.json',c.f.REPAIR_OUT/'preparation_manifest.json',c.f.OLD_OUT/'backend_synthetic_receipt.json',c.f.REPAIR_OUT/'backend_compatibility_receipt.json',c.f.REPAIR_OUT/'numpy_import_receipt.json')],
  'original_checkpoint_expected_sha256':c.f.CHECKPOINT_SHA,'author_archive_expected_sha256':c.readj(c.f.OLD_OUT/'resource_audit.json')['archive_sha256'],
  'runtime_inventory_sha256':c.sha256(c.ART/'runtime_inventory.json'),'runtime_prefix_count':6,'runtime_files':sum(p['file_count'] for p in prefixes.values()),
  'actual_numeric_imports':0,'actual_model_imports':0,'checkpoint_bytes_read':0,'checkpoint_loads':0,'native_probe_performed':False,
  'project_production_authorized':False,'root_review_commit_explicit_start_required':True,'resource_RAM_GiB':3,'resource_disk_GiB':5,
  'CPU_threads':2,'batch_size':2,'original_invented_alleles':len(original),'original_masked_pairs':8,'additional_fixed_requests':20,
  'stock_reference_models':1,'reuse_accepted_encoder_IR':True,'encoder_or_MLM_conversions':0,'actual_head_alias_certification_still_required':True,
  'unsafe_load_fallback':False,'actual_process_NumPy_BLAS_origin_check_required':True,'automatic_retry':False,
  'outcomes_read':False,'project_sequences_read':0,'model_fits':0,'method_novelty_claim':False})
 c.clean_imports();print('Masked synthetic backend preparation PASS; native start still requires root review/commit',c.sha256(c.MANIFEST),flush=True)

if __name__=='__main__':run()
