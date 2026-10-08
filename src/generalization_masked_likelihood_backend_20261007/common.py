"""Standard-library identities; importing never loads numerical packages."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from src.generalization_masked_likelihood_feasibility_20261007 import common as f

ROOT=f.ROOT
NS='generalization_masked_likelihood_backend_20261007'
SRC,ART,OUT,REP=[ROOT/p/NS for p in ('src','artifacts','results','reports')]
MANIFEST=OUT/'preparation_manifest.json'
TESTS=OUT/'synthetic_tests_receipt.json'
PLAN=REP/'plan.md'
IR=ROOT/'artifacts/generalization_splicebert_20261007/backend/splicebert_1024_fp32.xml'
CHECKPOINT=f.MODEL/'pytorch_model.bin'
ARCHIVE=ROOT/'data/external/splicebert/models.tar.gz'
FEASIBILITY=f.OUT/'preparation_manifest.json'
INVENTORY=f.ART/'synthetic_inventory.json'
SCIENTIFIC=ROOT/'artifacts/generalization_splicebert_runtime_compatibility_20261007/scientific_runtime_receipt.json'
RUNTIME_ROOTS={
 'scientific':ROOT/'data/interim/mechanism_v2/runtime',
 'torch':ROOT/'artifacts/generalization_splicebert_20261007/cpu_runtime',
 'dependencies':ROOT/'artifacts/generalization_splicebert_20261007/dependency_runtime',
 'openvino':ROOT/'artifacts/generalization_next_20261007/runtime',
 'transformers':ROOT/'.transformers_runtime',
 'python_packages':ROOT/'.python_packages',
}
PREREQUISITES=[FEASIBILITY,
 f.OLD_OUT/'backend_preparation_manifest.json',f.OLD_OUT/'backend_synthetic_receipt.json',f.OLD_OUT/'resource_audit.json',
 f.OLD_OUT/'cpu_runtime_extraction_receipt.json',f.OLD_OUT/'dependency_runtime_receipt.json',f.OLD_OUT/'reused_runtime_receipt.json',
 f.REPAIR_OUT/'preparation_manifest.json',f.REPAIR_OUT/'numpy_import_receipt.json',f.REPAIR_OUT/'backend_compatibility_receipt.json',
 SCIENTIFIC,ROOT/'results/generalization_next_20261007/bert_runtime_integrity.json',
 ROOT/'artifacts/generalization_splicebert_runtime_compatibility_20261007/numpy_official_member_parity.json',
 IR,IR.with_suffix('.bin')]

sha256=f.sha256
readj=f.readj
clean_imports=f.clean_imports

def save(path,payload):
 path=Path(path).resolve()
 assert any(path.is_relative_to(p.resolve()) for p in (SRC,ART,OUT,REP))
 path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists():assert path.read_bytes()==payload,'Preserve earlier artifact: '+str(path)
 else:
  with path.open('xb') as stream:stream.write(payload)

def jsave(path,value):
 save(path,(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n').encode())

def committed(path):
 path=Path(path).resolve();assert path.is_relative_to(ROOT)
 assert subprocess.check_output(['git','show','HEAD:'+path.relative_to(ROOT).as_posix()],cwd=ROOT)==path.read_bytes(),'Commit exact bytes before native start: '+str(path)

def own_fresh():
 for path in (OUT/'native_receipt.json',OUT/'native_attempt_incident.json',OUT/'current_numpy_import_receipt.json',ART/'mlm_head.npz',ART/'mlm_head_birth.json'):
  assert not path.exists(),'Preserve completed/failed/candidate native attempt: '+str(path)

def file_inventory(prefix):
 prefix=Path(prefix).resolve();result={}
 assert prefix.is_relative_to(ROOT) and prefix.is_dir()
 for path in sorted(prefix.rglob('*')):
  assert not path.is_symlink(),'No runtime symlinks'
  if path.is_file():result[path.relative_to(prefix).as_posix()]=sha256(path)
 assert result
 return result

def verify_inventory(prefix,files):
 prefix=Path(prefix).resolve()
 actual={p.relative_to(prefix).as_posix() for p in prefix.rglob('*') if p.is_file()}
 assert actual==set(files),'Runtime file roster changed: '+str(prefix)
 for name,expected in files.items():
  path=(prefix/name).resolve();assert path.is_relative_to(prefix) and not (prefix/name).is_symlink()
  assert sha256(path)==expected,'Runtime bytes changed: '+str(path)

def prerequisite_metadata():
 backend=readj(f.OLD_OUT/'backend_synthetic_receipt.json');compat=readj(f.REPAIR_OUT/'backend_compatibility_receipt.json');proof=readj(f.REPAIR_OUT/'numpy_import_receipt.json')
 observed={k:compat[k] for k in ('IR_xml_sha256','IR_bin_sha256','repair_preparation_sha256')}
 observed.update({'numpy_origin':proof['numpy_origin'],'native_core_origin':proof['native_core_origin'],'native_core_sha256':proof['native_core_sha256'],
  'backend_sha256':sha256(f.OLD_OUT/'backend_synthetic_receipt.json'),'numpy_proof_sha256':sha256(f.REPAIR_OUT/'numpy_import_receipt.json'),'scientific_runtime_receipt_sha256':sha256(SCIENTIFIC)})
 f.certify_encoder_metadata(backend,compat,proof,observed)
 assert sha256(IR)==backend['IR_xml_sha256'] and sha256(IR.with_suffix('.bin'))==backend['IR_bin_sha256']
 assert readj(FEASIBILITY)['status']=='FROZEN_MASKED_LIKELIHOOD_PREPARATION_ONLY'
 return backend,compat,proof

def tensor_digest_bytes(payload):return hashlib.sha256(payload).hexdigest()
