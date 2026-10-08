"""Explicit root-start native synthetic probe; importing uses stdlib only."""
from __future__ import annotations
from collections import OrderedDict
import gc
import hashlib
import importlib
import sys
import time
import zipfile
from . import common as c
from . import guard as g
from . import head as h
from src.generalization_masked_likelihood_feasibility_20261007 import token_math as m

def synthetic_requests(inventory):
 assert inventory['status']=='FIXED_INVENTED_ONLY' and inventory['original16_preserved'] is True and inventory['project_alleles']==0
 original=inventory['original_alleles'];assert len(original)==16
 assert [hashlib.sha256(s.encode()).hexdigest() for s in original]==inventory['original_sequence_sha256']
 requests=[m.request(row['parent'],row['mutant']) for field in ('original_one_edit_pairs','additional_boundary_multisite_pairs') for row in inventory[field]]
 assert requests[:8]==[m.request(original[i],original[i+1]) for i in range(0,16,2)]
 assert requests[8:]==m.additional_synthetic_requests(original)
 assert len(requests)==28 and [len(r.positions) for r in requests[:8]]==[1]*8
 for row,r in zip([*inventory['original_one_edit_pairs'],*inventory['additional_boundary_multisite_pairs']],requests):
  assert list(r.positions)==row['positions'] and r.context_sha256==row['masked_context_sha256']
 return original,requests

def log_probabilities(logits,np):
 values=logits.astype(np.float64);shifted=values-values.max(axis=-1,keepdims=True)
 result=shifted-np.log(np.sum(np.exp(shifted),axis=-1,keepdims=True))
 assert np.isfinite(result).all()
 return result

def export_head(weights,metadata,removed,np):
 assert not (c.ART/'mlm_head.npz').exists() and not (c.ART/'mlm_head_birth.json').exists()
 c.ART.mkdir(parents=True,exist_ok=True)
 with (c.ART/'mlm_head.npz').open('xb') as stream:np.savez(stream,**weights)
 birth={'status':'RESTRICTED_ORIGINAL_HEAD_EXPORTED_BEFORE_INFERENCE','sha256':c.sha256(c.ART/'mlm_head.npz'),
  'checkpoint_sha256':c.f.CHECKPOINT_SHA,'preparation_sha256':c.sha256(c.MANIFEST),'actual_selected_tensor_metadata':metadata,'legacy_deterministic_buffers':removed}
 c.jsave(c.ART/'mlm_head_birth.json',birth)
 with np.load(c.ART/'mlm_head.npz',allow_pickle=False) as loaded:
  assert set(loaded.files)==set(weights)
  for name,array in weights.items():assert loaded[name].dtype==np.float32 and loaded[name].shape==array.shape and loaded[name].tobytes()==array.tobytes()
 return birth

def execute(manifest,runtime,proof,np):
 # The guard already admitted NumPy and actual BLAS origin in this fresh process.
 torch=importlib.import_module('torch');transformers=importlib.import_module('transformers');ov=importlib.import_module('openvino')
 assert torch.__version__=='2.6.0+cpu' and transformers.__version__=='4.40.2' and np.__version__=='1.26.4'
 assert torch.version.cuda is None
 torch.set_num_threads(2);torch.set_num_interop_threads(1)
 assert torch.get_num_threads()==2 and torch.get_num_interop_threads()==1
 BertConfig=transformers.BertConfig;BertForMaskedLM=transformers.BertForMaskedLM;BertTokenizer=transformers.BertTokenizer
 from src.generalization_splicebert_runtime_compatibility_20261007 import launcher
 inventory=c.readj(c.ART/'runtime_inventory.json')
 package_roots={'numpy':c.RUNTIME_ROOTS['scientific'],'scipy':c.RUNTIME_ROOTS['scientific'],'torch':c.RUNTIME_ROOTS['torch'],
  'transformers':c.RUNTIME_ROOTS['transformers'],'openvino':c.RUNTIME_ROOTS['openvino'],'tokenizers':c.RUNTIME_ROOTS['openvino']}
 origin_proof=g.actual_origin_proof(package_roots,inventory,launcher.process_native_paths())
 # Actual checkpoint aliases are certified BEFORE a tied stock model is even
 # instantiated; a later alias load cannot overwrite and conceal disagreement.
 checkpoint=torch.load(c.CHECKPOINT,weights_only=True,map_location='cpu',mmap=zipfile.is_zipfile(c.CHECKPOINT))
 assert isinstance(checkpoint,(dict,OrderedDict)) and checkpoint
 metadata=h.certify_actual_head(checkpoint,torch)
 assert all(bool(torch.isfinite(value).all()) for value in checkpoint.values())
 weights={name:value.detach().contiguous().numpy().copy() for name,value in checkpoint.items() if name in c.f.HEAD_KEYS}
 config=BertConfig.from_json_file(str(c.f.MODEL/'config.json'))
 assert (config.hidden_size,config.num_hidden_layers,config.vocab_size,config.max_position_embeddings)==(512,6,10,1026)
 assert config.hidden_act=='gelu' and config.layer_norm_eps==1e-12 and config.tie_word_embeddings is True
 assert config.position_embedding_type=='absolute';config.output_hidden_states=False
 model=BertForMaskedLM(config).float().eval()
 state,removed=h.remove_legacy_buffers(checkpoint,model.state_dict(),config,torch)
 model.load_state_dict(state,strict=True)
 assert set(state)==set(model.state_dict()) and all(torch.equal(value,model.state_dict()[name]) for name,value in state.items())
 assert model.cls.predictions.decoder.weight is model.bert.embeddings.word_embeddings.weight
 assert model.cls.predictions.decoder.bias is model.cls.predictions.bias
 assert all(bool(torch.isfinite(value).all()) for value in model.parameters())
 birth=export_head(weights,metadata,removed,np)
 del checkpoint,state;gc.collect()
 original,requests=synthetic_requests(c.readj(c.INVENTORY))
 assert [hashlib.sha256(s.encode()).hexdigest() for s in original]==c.readj(c.f.OLD_OUT/'backend_synthetic_receipt.json')['synthetic_sequence_sha256']
 tokenizer=BertTokenizer.from_pretrained(c.f.MODEL,local_files_only=True)
 assert tokenizer.vocab=={token:i for i,token in enumerate(c.f.VOCAB)} and tokenizer.mask_token_id==4
 for batch,real in m.batches(requests):
  # Author tokenizer metadata independently verifies explicit [MASK] positions.
  texts=[' '.join('[MASK]' if token==4 else c.f.VOCAB[token] for token in r.input_ids[1:-1]) for r in batch]
  authored=tokenizer(texts,padding=False)
  assert all(authored[name]==m.model_inputs(batch)[name] for name in ('input_ids','attention_mask','token_type_ids'))
 core=ov.Core();compiled=core.compile_model(str(c.IR),'CPU',{'INFERENCE_NUM_THREADS':2,'INFERENCE_PRECISION_HINT':'f32','NUM_STREAMS':1})
 assert len(compiled.inputs)==3 and len(compiled.outputs)==1
 assert {p.get_any_name() for p in compiled.inputs}=={'input_ids','attention_mask','token_type_ids'}
 started=time.perf_counter();batches=[];readouts={'stock':[],'numpy_stock_hidden':[],'numpy_IR_hidden':[]};all_edits={key:[] for key in readouts};edit_records={key:[] for key in readouts}
 for batch,real in m.batches(requests):
  inputs=m.model_inputs(batch)
  native={name:torch.tensor(value,dtype=torch.long) for name,value in inputs.items()}
  with torch.inference_mode():result=model(**native,output_hidden_states=True,return_dict=True)
  stock=result.logits.detach().cpu().numpy();hidden=result.hidden_states[-1].detach().cpu().numpy()
  actual=np.asarray(compiled({name:np.asarray(value,dtype=np.int64) for name,value in inputs.items()})[0])
  assert stock.shape==(2,len(batch[0].input_ids),10) and hidden.shape==actual.shape==(2,len(batch[0].input_ids),512)
  paths={'stock':stock,'numpy_stock_hidden':h.numpy_head(hidden,weights,np),'numpy_IR_hidden':h.numpy_head(actual,weights,np)}
  comparisons={'encoder_IR_vs_stock':h.array_parity(actual,hidden,np)}
  stocklogs=log_probabilities(stock,np);stockprob=np.exp(stocklogs)
  for key in ('numpy_stock_hidden','numpy_IR_hidden'):
   comparisons[key+'_logits']=h.array_parity(paths[key],stock,np)
   logs=log_probabilities(paths[key],np)
   comparisons[key+'_log_probabilities']=h.array_parity(logs,stocklogs,np)
   comparisons[key+'_probabilities']=h.array_parity(np.exp(logs),stockprob,np)
  for key,logits in paths.items():
   for index,r in enumerate(batch[:real]):
    scored=m.score(r,logits[index].tolist());readouts[key].append(scored['score']);edit_records[key].append(scored['per_edit']);all_edits[key].extend(e['log_ratio'] for e in scored['per_edit'])
    reverse=m.score(m.request(r.mutant,r.parent),logits[index].tolist());assert reverse['score']==-scored['score']
    assert m.score(m.request(r.parent,r.parent))['score']==0.
   if real==1:assert np.array_equal(logits[0],logits[1]),'Real-tail duplication must yield identical output'
  batches.append({'length_nt':len(batch[0].parent),'real_requests':real,'contexts':[r.context_sha256 for r in batch[:real]],'comparisons':comparisons})
  print('Synthetic masked MLM three-path parity',len(batch[0].parent),'nt PASS',flush=True)
 expected=[r for batch,real in m.batches(requests) for r in batch[:real]]
 assert len(expected)==28 and len(set(expected))==28 and {len(r.parent) for r in expected}=={46,150,190,260}
 score_checks={}
 for key in ('numpy_stock_hidden','numpy_IR_hidden'):
  score_checks[key+'_aggregate']=h.array_parity(np.asarray([readouts[key]],dtype=np.float64),np.asarray([readouts['stock']],dtype=np.float64),np)
  score_checks[key+'_per_edit']=h.array_parity(np.asarray([all_edits[key]],dtype=np.float64),np.asarray([all_edits['stock']],dtype=np.float64),np)
 # All imported sources/natives and runtime rosters remain the pinned bytes.
 origin_proof_after=g.actual_origin_proof(package_roots,inventory,launcher.process_native_paths())
 for key,prefix in c.RUNTIME_ROOTS.items():c.verify_inventory(prefix,inventory['prefixes'][key]['files'])
 g.validate_preparation(manifest)
 assert c.sha256(c.ART/'mlm_head.npz')==birth['sha256'] and c.sha256(c.CHECKPOINT)==c.f.CHECKPOINT_SHA
 c.prerequisite_metadata()
 return {'status':'PASS_SYNTHETIC_MASKED_LIKELIHOOD_BACKEND_ONLY','preparation_sha256':c.sha256(c.MANIFEST),
  'checkpoint_sha256':c.f.CHECKPOINT_SHA,'head_export_birth_sha256':c.sha256(c.ART/'mlm_head_birth.json'),'head_npz_sha256':birth['sha256'],
  'current_numpy_import_receipt_sha256':c.sha256(c.OUT/'current_numpy_import_receipt.json'),'actual_origins_before':origin_proof,'actual_origins_after':origin_proof_after,
  'actual_head_tensor_metadata':metadata,'exact_head_ties_certified_before_stock_load':True,'strict_full_state_load':True,'unsafe_load_fallback':False,
  'legacy_deterministic_buffers':removed,'IR_xml_sha256':c.sha256(c.IR),'IR_bin_sha256':c.sha256(c.IR.with_suffix('.bin')),
  'original_synthetic_alleles':16,'original_masked_pairs':8,'additional_fixed_requests':20,'masked_context_calls':len(batches),
  'comparisons':batches,'per_edit_count':len(all_edits['stock']),'readout_parity':score_checks,'synthetic_readouts':{key:[{'context_sha256':r.context_sha256,'changed_positions':list(r.positions),'score':value,'per_edit':edits} for r,value,edits in zip(expected,values,edit_records[key])] for key,values in readouts.items()},
  'CPU_threads':2,'batch_size':2,'fake_padding':False,'MLM_or_encoder_conversions':0,'total_seconds':time.perf_counter()-started,
  'scope':'Shared union-mask block conditional marginal surrogate; not joint multivariant likelihood or localization direction',
  'SRLE46_outside_author_recommended_domain':True,'project_sequences_read':0,'outcomes_read':False,'model_fits':0,'project_production_authorized':False}

def run(root_start=False):
 # Unauthorized calls fail before incident creation or any numerical import.
 assert root_start,'Explicit root start required'
 c.clean_imports();c.own_fresh()
 try:
  manifest,runtime,proof,np=g.guard(root_start=True)
  receipt=execute(manifest,runtime,proof,np)
  c.jsave(c.OUT/'native_receipt.json',receipt)
 except BaseException as error:
  c.jsave(c.OUT/'native_attempt_incident.json',{'status':'FAILED_PRESERVED_NO_AUTOMATIC_RETRY','error_class':type(error).__name__,'message':str(error),
   'preparation_sha256':c.sha256(c.MANIFEST) if c.MANIFEST.exists() else None,'native_candidates_preserved':True,'unsafe_load_fallback':False,
   'project_sequences_read':0,'outcomes_read':False,'model_fits':0,'old_sources_modified':False})
  raise
 print('Synthetic masked-likelihood native admission PASS; project production remains unauthorized',flush=True)

if __name__=='__main__':
 assert sys.argv[1:]==['--root-start'];run(root_start=True)
