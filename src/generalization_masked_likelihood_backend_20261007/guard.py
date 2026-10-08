"""Fresh resource/runtime admission; never reruns the completed encoder guard."""
from __future__ import annotations
import importlib
import os
from pathlib import Path
import sys
from . import common as c

def resource_contract(state):
 assert state['resource_admission_now'] and state['available_RAM_bytes']>=3*1024**3 and state['workspace_disk_free_bytes']>=5*1024**3,'Fresh >=3GiB RAM and >=5GiB disk required'
 return state

def validate_preparation(manifest,hasher=c.sha256):
 assert manifest['status']=='FROZEN_SYNTHETIC_MASKED_BACKEND_PREPARATION'
 assert manifest['native_probe_performed'] is False and manifest['project_production_authorized'] is False
 for name,expected in manifest['files'].items():
  path=(c.ROOT/name).resolve();assert path.is_relative_to(c.ROOT)
  assert hasher(path)==expected,'Preparation/prerequisite changed: '+name

def guard(root_start=False):
 assert root_start,'Root review, exact commit, and explicit native start required'
 c.clean_imports();c.own_fresh()
 from src.generalization_splicebert_20261007 import backend_probe as old
 first=resource_contract(old.resource_state())
 assert os.environ.get('OPENBLAS_NUM_THREADS')==os.environ.get('OMP_NUM_THREADS')=='2'
 assert os.environ.get('PYTHONDONTWRITEBYTECODE')=='1' and os.environ.get('PYTHONUTF8')=='1'
 c.committed(c.MANIFEST);manifest=c.readj(c.MANIFEST);validate_preparation(manifest)
 for name in manifest['own_committed_files']:c.committed(c.ROOT/name)
 for name in manifest['committed_prerequisites']:c.committed(c.ROOT/name)
 c.prerequisite_metadata()
 # Original manifests are preserved and all original hashes still hold. The
 # original guard's no-existing-IR clause is intentionally not rerun.
 for path in (c.f.OLD_OUT/'backend_preparation_manifest.json',c.f.REPAIR_OUT/'preparation_manifest.json',c.FEASIBILITY):
  for name,expected in c.readj(path)['files'].items():assert c.sha256(c.ROOT/name)==expected,name
 audit=c.readj(c.f.OLD_OUT/'resource_audit.json')
 assert audit['status']=='PASS' and audit['author_archive_identity']=='All selected checkpoint/tokenizer members byte-identical'
 for name,row in audit['cached_files'].items():
  assert (c.f.MODEL/name).stat().st_size==row['bytes'] and c.sha256(c.f.MODEL/name)==row['sha256']
 assert c.sha256(c.CHECKPOINT)==c.f.CHECKPOINT_SHA
 assert c.ARCHIVE.stat().st_size==audit['archive_bytes'] and c.sha256(c.ARCHIVE)==audit['archive_sha256']
 for key,prefix in c.RUNTIME_ROOTS.items():c.verify_inventory(prefix,c.readj(c.ART/'runtime_inventory.json')['prefixes'][key]['files'])
 reused=c.readj(c.f.OLD_OUT/'reused_runtime_receipt.json');assert reused['status']=='PASS'
 for name,expected in reused['files'].items():assert c.sha256(Path(name))==expected,name
 runtime=c.readj(c.SCIENTIFIC)
 assert Path(sys.executable).resolve()==Path(runtime['python_executable']).resolve()
 assert sys.version_info[:2]==(3,12) and sys.implementation.cache_tag=='cpython-312'
 for name,expected in runtime['python_native_files'].items():assert c.sha256(name)==expected
 # Same fixed local import roots, with the independently certified scientific
 # NumPy prefix first. No site processing, downloads, accounts, or installs.
 order=('scientific','dependencies','torch','openvino','transformers','python_packages')
 for key in reversed(order):sys.path.insert(0,str(c.RUNTIME_ROOTS[key]))
 for name in ('HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE'):os.environ[name]='1'
 from src.generalization_splicebert_runtime_compatibility_20261007 import launcher
 c.clean_imports();origin=launcher.select_prefix()
 second=resource_contract(old.resource_state())
 # This is the first actual numerical import, after both fresh resource checks.
 numpy=importlib.import_module('numpy');proof=launcher.numpy_proof(numpy,runtime)
 assert proof['numpy_origin']==origin
 third=resource_contract(old.resource_state())
 proof.update({'first_resource':first,'second_resource':second,'before_Torch_resource':third,'new_preparation_sha256':c.sha256(c.MANIFEST)})
 c.jsave(c.OUT/'current_numpy_import_receipt.json',proof)
 return manifest,runtime,proof,numpy

def actual_origin_proof(package_roots,inventory,native_paths,modules=None):
 """Bind actual package sources and loaded runtime PYD/DLLs after imports."""
 modules=sys.modules if modules is None else modules
 roots={key:Path(value).resolve() for key,value in package_roots.items()}
 allowed={Path(row['path']).resolve()/name:digest for row in inventory['prefixes'].values() for name,digest in row['files'].items()}
 native_names={path.name.lower() for path in allowed if path.suffix.lower() in ('.pyd','.dll')}
 found={}
 for name,module in tuple(modules.items()):
  top=name.split('.')[0]
  if top not in roots:continue
  location=getattr(module,'__file__',None)
  if not location:continue
  path=Path(location).resolve();assert path.is_relative_to(roots[top]),'Imported package resolved elsewhere: '+name
  assert path in allowed and c.sha256(path)==allowed[path],name
  found[str(path)]=allowed[path]
 actual_native={}
 for item in native_paths:
  path=Path(item).resolve()
  if path.name.lower() in native_names or any(path.is_relative_to(Path(row['path']).resolve()) for row in inventory['prefixes'].values()):
   assert path in allowed and c.sha256(path)==allowed[path],'Native model/runtime dependency resolved elsewhere: '+str(path)
   actual_native[str(path)]=allowed[path]
 assert found and actual_native
 return {'imported_package_files':found,'actually_loaded_native_files':actual_native,'SciPy_used_for_head_GELU':False}
