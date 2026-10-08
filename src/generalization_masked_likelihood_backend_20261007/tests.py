"""Standard-library synthetic/mocked admission invariants; no native imports."""
from __future__ import annotations
import ast
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from . import common as c,guard as g,head as h,probe as p
from src.generalization_masked_likelihood_feasibility_20261007 import token_math as m

class Tensor:
 def __init__(self,shape,payload,dtype='float32',finite=True):
  self.shape=shape;self.payload=payload;self.dtype=dtype;self.device=SimpleNamespace(type='cpu');self.finite=finite
 def detach(self):return self
 def contiguous(self):return self
 def numpy(self):return self
 def tobytes(self):return self.payload

def mocked_torch():
 return SimpleNamespace(Tensor=Tensor,float32='float32',long='long',isfinite=lambda t:SimpleNamespace(all=lambda:t.finite),equal=lambda a,b:a.dtype==b.dtype and a.shape==b.shape and a.payload==b.payload)

def checkpoint():
 result={name:Tensor(shape,name.encode()) for name,shape in c.f.HEAD_KEYS.items()}
 result['bert.embeddings.word_embeddings.weight']=Tensor((10,512),b'input-output-shared')
 result['cls.predictions.decoder.weight']=Tensor((10,512),b'input-output-shared')
 result['cls.predictions.bias']=result['cls.predictions.decoder.bias']=Tensor((10,),b'bias-shared')
 return result

class Tests(unittest.TestCase):
 def test_no_numeric_imports(self):c.clean_imports()
 def test_unauthorized_start_before_import_or_write(self):
  with patch.object(g,'guard',side_effect=AssertionError('must not call')),patch.object(c,'jsave',side_effect=AssertionError('must not write')):
   with self.assertRaisesRegex(AssertionError,'Explicit root start'):p.run(False)
  with self.assertRaisesRegex(AssertionError,'Root review'):g.guard(False)
  c.clean_imports()
 def test_fresh_resources_exact_floors(self):
  def state(ram,disk,yes=True):return {'resource_admission_now':yes,'available_RAM_bytes':ram,'workspace_disk_free_bytes':disk}
  self.assertTrue(g.resource_contract(state(3*2**30,5*2**30)))
  for value in (state(3*2**30-1,5*2**30),state(3*2**30,5*2**30-1),state(3*2**30,5*2**30,False)):
   with self.assertRaises(AssertionError):g.resource_contract(value)
 def test_actual_head_mock_admitted_before_alias_load(self):
  d=h.certify_actual_head(checkpoint(),mocked_torch());self.assertEqual(len(d),8)
  tree=ast.parse((c.SRC/'probe.py').read_text());execute=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='execute')
  calls=[ast.unparse(n.func) for n in ast.walk(execute) if isinstance(n,ast.Call)]
  self.assertLess(calls.index('h.certify_actual_head'),calls.index('BertForMaskedLM'))
  self.assertLess(calls.index('h.certify_actual_head'),calls.index('model.load_state_dict'))
 def test_inconsistent_head_alias_rejected(self):
  for key in ('cls.predictions.decoder.weight','cls.predictions.decoder.bias'):
   d=checkpoint();d[key]=Tensor(d[key].shape,b'changed')
   with self.assertRaises(AssertionError):h.certify_actual_head(d,mocked_torch())
 def test_actual_head_shape_dtype_finite_unknown_rejected(self):
  for replacement in (Tensor((1,),b'x'),Tensor((512,512),b'x','float16'),Tensor((512,512),b'x',finite=False)):
   d=checkpoint();d['cls.predictions.transform.dense.weight']=replacement
   with self.assertRaises(AssertionError):h.certify_actual_head(d,mocked_torch())
  d=checkpoint();d['unknown.weight']=Tensor((1,),b'x')
  with self.assertRaises(AssertionError):h.certify_actual_head(d,mocked_torch())
 def test_legacy_buffer_only_canonical_exact(self):
  torch=mocked_torch();torch.arange=lambda n:SimpleNamespace(reshape=lambda *args:Tensor((1,n),b'position','long'))
  torch.zeros=lambda shape,dtype:Tensor(shape,b'zero',dtype)
  cfg=SimpleNamespace(max_position_embeddings=4)
  d={'bert.embeddings.position_ids':Tensor((1,4),b'position','long'),'bert.embeddings.token_type_ids':Tensor((1,4),b'zero','long'),'weight':Tensor((1,),b'w')}
  kept,removed=h.remove_legacy_buffers(d,{'weight':d['weight']},cfg,torch)
  self.assertEqual(set(kept),{'weight'});self.assertEqual(len(removed),2)
  d['bert.embeddings.position_ids']=Tensor((1,4),b'wrong','long')
  with self.assertRaises(AssertionError):h.remove_legacy_buffers(d,{},cfg,torch)
 def test_parity_thresholds_unchanged_and_finite(self):
  h.parity_contract(.001,.0001,.999999)
  for values in ((.001000001,.0001,1),(.001,.000100001,1),(.001,.0001,.999998999),(float('nan'),0,1)):
   with self.assertRaises(AssertionError):h.parity_contract(*values)
 def test_fresh_attempt_preserves_every_candidate(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder)
   with patch.object(c,'OUT',root),patch.object(c,'ART',root):
    c.own_fresh()
    for name in ('native_receipt.json','native_attempt_incident.json','current_numpy_import_receipt.json','mlm_head.npz','mlm_head_birth.json'):
     q=root/name;q.write_bytes(b'old')
     with self.assertRaises(AssertionError):c.own_fresh()
     q.unlink()
 def test_immutable_write_never_overwrites(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder)
   with patch.object(c,'OUT',root):
    q=root/'a.json';c.save(q,b'a');c.save(q,b'a')
    with self.assertRaises(AssertionError):c.save(q,b'b')
 def test_complete_inventory_missing_extra_and_corrupt(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);q=root/'a';q.write_bytes(b'a');files={'a':c.sha256(q)}
   c.verify_inventory(root,files);q.write_bytes(b'b')
   with self.assertRaises(AssertionError):c.verify_inventory(root,files)
   q.write_bytes(b'a');(root/'extra').write_bytes(b'x')
   with self.assertRaises(AssertionError):c.verify_inventory(root,files)
   (root/'extra').unlink();q.unlink()
   with self.assertRaises(AssertionError):c.verify_inventory(root,files)
 def test_package_and_native_origin_is_exact(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);q=root/'numpy.py';n=root/'native.dll';q.write_bytes(b'py');n.write_bytes(b'native')
   inv={'prefixes':{'synthetic':{'path':str(root),'files':{'numpy.py':c.sha256(q),'native.dll':c.sha256(n)}}}}
   result=g.actual_origin_proof({'numpy':root},inv,[n],{'numpy':SimpleNamespace(__file__=q)})
   self.assertTrue(result['actually_loaded_native_files'])
   with self.assertRaises(AssertionError):g.actual_origin_proof({'numpy':root},inv,[root.parent/'native.dll'],{'numpy':SimpleNamespace(__file__=q)})
   with self.assertRaises(AssertionError):g.actual_origin_proof({'numpy':root},inv,[n],{'numpy':SimpleNamespace(__file__=root.parent/'numpy.py')})
 def test_preparation_corruption_and_outside_root(self):
  d={'status':'FROZEN_SYNTHETIC_MASKED_BACKEND_PREPARATION','native_probe_performed':False,'project_production_authorized':False,'files':{'src/a':'good'}}
  g.validate_preparation(d,lambda p:'good')
  with self.assertRaises(AssertionError):g.validate_preparation(d,lambda p:'bad')
  d['files']={'../outside':'good'}
  with self.assertRaises(AssertionError):g.validate_preparation(d,lambda p:'good')
 def test_synthetic_inventory_exact_recipe_and_metadata(self):
  original=m.synthetic_sequences('GCCCACAAGTATCACTAAGC','ATCATAATCAGCCATACCAC')
  rows=lambda req:[{'parent':r.parent,'mutant':r.mutant,'positions':list(r.positions),'masked_context_sha256':r.context_sha256} for r in req]
  inv={'status':'FIXED_INVENTED_ONLY','original16_preserved':True,'project_alleles':0,'original_alleles':original,'original_sequence_sha256':[hashlib.sha256(s.encode()).hexdigest() for s in original],
   'original_one_edit_pairs':rows([m.request(original[i],original[i+1]) for i in range(0,16,2)]),'additional_boundary_multisite_pairs':rows(m.additional_synthetic_requests(original))}
  self.assertEqual(len(p.synthetic_requests(inv)[1]),28)
  inv['additional_boundary_multisite_pairs'][0]['positions']=[1]
  with self.assertRaises(AssertionError):p.synthetic_requests(inv)
 def test_shared_mask_offsets_boundary_multisite_and_reversal(self):
  r=m.request('ACGTAC','TCGTAA');self.assertEqual(r.positions,(0,5));self.assertEqual(r.input_ids,(2,4,7,8,9,6,4,3))
  self.assertEqual(r.input_ids,m.request(r.mutant,r.parent).input_ids)
  logits=[[float(i) for i in range(10)] for _ in r.input_ids]
  self.assertEqual(m.score(r,logits)['score'],-m.score(m.request(r.mutant,r.parent),logits)['score'])
 def test_real_tail_duplication_no_fake_padding(self):
  r=m.request('ACGT','TCGT');batch,real=next(m.batches([r]));self.assertEqual(real,1);self.assertEqual(batch,[r,r])
  inputs=m.model_inputs(batch);self.assertTrue(all(all(x==1 for x in row) for row in inputs['attention_mask']))
  self.assertFalse(any(0 in row for row in inputs['input_ids']))
 def test_union_all_changed_noedit_and_stable_math(self):
  self.assertEqual(m.score(m.request('ACGT','ACGT'))['score'],0)
  r=m.request('ACGT','TGCA');self.assertEqual(r.positions,(0,1,2,3));self.assertEqual(r.input_ids,(2,4,4,4,4,3))
  self.assertTrue(all(math.isfinite(v) for v in m.log_softmax([1e4+i for i in range(10)])))
 def test_all_sources_parse_and_no_top_numeric_imports(self):
  for path in c.SRC.glob('*.py'):
   tree=ast.parse(path.read_text())
   for node in tree.body:
    if isinstance(node,(ast.Import,ast.ImportFrom)):
     names=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module or '']
     self.assertFalse(any(n.split('.')[0] in c.f.BLOCKED for n in names))
  c.clean_imports()

def run():
 c.clean_imports();stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
 print(stream.getvalue(),flush=True);assert result.wasSuccessful()
 c.jsave(c.TESTS,{'status':'PASS','tests':result.testsRun,'test_output':stream.getvalue(),'source_hashes':{p.relative_to(c.ROOT).as_posix():c.sha256(p) for p in sorted(c.SRC.glob('*.py'))},
  'plan_sha256':c.sha256(c.PLAN),'actual_numeric_imports':0,'actual_model_imports':0,'checkpoint_loads':0,'model_calls':0,'outcomes_read':False,'project_sequences_read':0,'model_fits':0,'scope':'STDLIB_MOCK_BACKEND_PREPARATION_ONLY'})
 c.clean_imports()

if __name__=='__main__':run()
