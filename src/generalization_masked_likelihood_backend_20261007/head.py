"""Native helpers are inert until supplied actual certified arrays/tensors."""
from __future__ import annotations
import math
from . import common as c

def certify_actual_head(checkpoint,torch):
 required=dict(c.f.HEAD_KEYS);required['bert.embeddings.word_embeddings.weight']=(10,512)
 assert all(isinstance(k,str) and isinstance(v,torch.Tensor) for k,v in checkpoint.items())
 assert set(k for k in checkpoint if not k.startswith('bert.'))==set(c.f.HEAD_KEYS)
 metadata={}
 for name,shape in required.items():
  value=checkpoint[name]
  assert tuple(value.shape)==shape and value.dtype==torch.float32 and value.device.type=='cpu'
  assert bool(torch.isfinite(value).all())
  metadata[name]={'shape':list(shape),'dtype':'float32','finite':True,'sha256':c.tensor_digest_bytes(value.detach().contiguous().numpy().tobytes())}
 c.f.certify_alias_metadata(metadata,tied=True)
 assert torch.equal(checkpoint['cls.predictions.decoder.weight'],checkpoint['bert.embeddings.word_embeddings.weight'])
 assert torch.equal(checkpoint['cls.predictions.decoder.bias'],checkpoint['cls.predictions.bias'])
 return metadata

def numpy_head(hidden,weights,np,eps=1e-12):
 assert eps==1e-12 and hidden.dtype==np.float32 and hidden.shape[-1]==512 and np.isfinite(hidden).all()
 pre=hidden@weights['cls.predictions.transform.dense.weight'].T+weights['cls.predictions.transform.dense.bias']
 # Exact erf GELU, matching stock ACT2FN['gelu']; no scipy runtime is needed.
 erf=np.fromiter((math.erf(float(x)/math.sqrt(2.)) for x in pre.ravel()),dtype=np.float64,count=pre.size).reshape(pre.shape).astype(np.float32)
 activated=pre*np.float32(.5)*(np.float32(1.)+erf)
 mean=np.mean(activated,axis=-1,keepdims=True,dtype=np.float32)
 variance=np.mean((activated-mean)**2,axis=-1,keepdims=True,dtype=np.float32)
 normalized=(activated-mean)/np.sqrt(variance+np.float32(eps))
 transformed=normalized*weights['cls.predictions.transform.LayerNorm.weight']+weights['cls.predictions.transform.LayerNorm.bias']
 logits=transformed@weights['cls.predictions.decoder.weight'].T+weights['cls.predictions.bias']
 assert logits.dtype==np.float32 and logits.shape==(*hidden.shape[:-1],10) and np.isfinite(logits).all()
 return logits

def parity_contract(maximum,mean,cosine):
 assert all(math.isfinite(x) for x in (maximum,mean,cosine))
 assert maximum<=.001 and mean<=.0001 and cosine>=.999999,'Unchanged native parity threshold failed'
 return {'maximum_absolute_difference':maximum,'mean_absolute_difference':mean,'minimum_token_cosine':cosine,'thresholds':{'maximum':.001,'mean':.0001,'minimum_cosine':.999999}}

def array_parity(actual,reference,np):
 assert actual.shape==reference.shape and actual.size and np.isfinite(actual).all() and np.isfinite(reference).all()
 a=actual.astype(np.float64);r=reference.astype(np.float64);difference=np.abs(a-r)
 dots=np.sum(a*r,axis=-1);na=np.linalg.norm(a,axis=-1);nr=np.linalg.norm(r,axis=-1)
 bothzero=(na==0)&(nr==0);assert np.all((na>0)&(nr>0)|bothzero),'One zero vector makes cosine undefined'
 cosine=np.ones_like(dots);valid=~bothzero;cosine[valid]=dots[valid]/(na[valid]*nr[valid])
 return parity_contract(float(difference.max()),float(difference.mean()),float(cosine.min()))

def remove_legacy_buffers(state,model_state,config,torch):
 result=dict(state);removed=[]
 for name in ('bert.embeddings.position_ids','bert.embeddings.token_type_ids'):
  if name in result and name not in model_state:
   expected=torch.arange(config.max_position_embeddings).reshape(1,-1) if name.endswith('position_ids') else torch.zeros((1,config.max_position_embeddings),dtype=torch.long)
   assert result[name].dtype==torch.long and torch.equal(result[name],expected),'Noncanonical legacy deterministic buffer'
   result.pop(name);removed.append(name)
 return result,removed
