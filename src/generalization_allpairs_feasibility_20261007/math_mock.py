"""Pure stdlib invented-example kernels, not a project fit implementation."""
from collections import Counter
import itertools
import math

def finite(values):assert all(math.isfinite(float(v)) for v in values)

def loss_residual(margin,sign,weight):
 finite((margin,sign,weight));assert sign in (-1,1) and weight>0
 loss=weight*(max(0.,-margin)+math.log1p(math.exp(-abs(margin))))
 if margin>=0:
  e=math.exp(-margin);q=e/(1.+e)
 else:q=1./(1.+math.exp(margin))
 return loss,-weight*sign*q

def non_tied_pairs(labels,indices):
 counts=Counter(labels[i] for i in indices);n=len(indices)
 return n*(n-1)//2-sum(k*(k-1)//2 for k in counts.values())

def prepare_contexts(labels,contexts,cap_edges,masses):
 """Freeze cap-positive contexts and their exact old cap loss mass for both."""
 finite(labels);assert set(contexts)==set(cap_edges)==set(masses)
 retained={};total=0.
 for name,indices in contexts.items():
  assert len(set(indices))==len(indices) and len(indices)>=2
  allowed=set(indices);edges=cap_edges[name]
  assert all(a<b and a in allowed and b in allowed for a,b in edges) and len(set(edges))==len(edges)
  valid=[(a,b) for a,b in edges if labels[a]!=labels[b]]
  assert masses[name]>0 and math.isfinite(masses[name])
  if valid:retained[name]={'indices':list(indices),'valid_cap_edges':valid,'mass':masses[name]};total+=masses[name]
 assert retained and total>0
 for row in retained.values():row['mass']/=total
 return retained

def objective_candidate(matrix,beta,labels,prepared,penalty,mode='all'):
 """Exact utility-space residual then X^T candidate gradient, with no pair-X."""
 assert mode in ('all','cap') and len(matrix)==len(labels) and len(beta)==len(matrix[0]) and penalty>0
 finite(beta);finite(labels)
 for row in matrix:assert len(row)==len(beta);finite(row)
 utility=[math.fsum(a*b for a,b in zip(row,beta)) for row in matrix];finite(utility)
 candidate_gradient=[0.]*len(matrix);loss=0.;counts={}
 for name,context in prepared.items():
  indices=context['indices']
  pairs=itertools.combinations(indices,2) if mode=='all' else iter(context['valid_cap_edges'])
  count=non_tied_pairs(labels,indices) if mode=='all' else len(context['valid_cap_edges'])
  assert count>0;weight=context['mass']/count;actual=0
  for a,b in pairs:
   if labels[a]==labels[b]:continue
   sign=1 if labels[a]>labels[b] else -1;margin=sign*(utility[a]-utility[b])
   value,residual=loss_residual(margin,sign,weight);loss+=value;candidate_gradient[a]+=residual;candidate_gradient[b]-=residual;actual+=1
  assert actual==count;counts[name]=actual
  assert abs(math.fsum(candidate_gradient[i] for i in indices))<1e-12
 loss+=penalty*.5*math.fsum(b*b for b in beta)
 gradient=[math.fsum(matrix[i][j]*candidate_gradient[i] for i in range(len(matrix)))+penalty*beta[j] for j in range(len(beta))]
 finite([loss]+gradient)
 return loss,gradient,candidate_gradient,counts

def materialized_reference(matrix,beta,labels,prepared,penalty,mode='all'):
 """Separate tiny full pair-feature construction for synthetic identity only."""
 pair_rows=[]
 for context in prepared.values():
  edges=list(itertools.combinations(context['indices'],2)) if mode=='all' else context['valid_cap_edges']
  valid=[(a,b) for a,b in edges if labels[a]!=labels[b]]
  for a,b in valid:
   pair_rows.append(([x-y for x,y in zip(matrix[a],matrix[b])],1 if labels[a]>labels[b] else -1,context['mass']/len(valid)))
 loss=penalty*.5*math.fsum(b*b for b in beta);gradient=[penalty*b for b in beta]
 for difference,sign,weight in pair_rows:
  margin=sign*math.fsum(d*b for d,b in zip(difference,beta));value,residual=loss_residual(margin,sign,weight);loss+=value
  for j,d in enumerate(difference):gradient[j]+=d*residual
 return loss,gradient

def cap_rms(matrix,labels,prepared):
 """Only old valid cap edges establish scales/support, once, for both arms."""
 result=[]
 for j in range(len(matrix[0])):
  squared=[]
  for context in prepared.values():
   weight=context['mass']/len(context['valid_cap_edges'])
   squared.extend(weight*(matrix[a][j]-matrix[b][j])**2 for a,b in context['valid_cap_edges'])
  result.append(math.sqrt(math.fsum(squared)))
 supported=[v>=1e-8 for v in result]
 return [v if active else 1. for v,active in zip(result,supported)],supported
