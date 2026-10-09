"""Standard-library study contracts; no numerical or biological imports."""
from pathlib import Path
import hashlib,itertools,math
ROOT=Path(__file__).resolve().parents[2]
NS='generalization_prelib_pooled_lineage_20261009'
OUT=ROOT/'results'/NS
MODES=('no_flip_no_c1c2','coupled_consecutive','released_csv','fit_region_truncated')
KMERS=tuple(''.join(x) for k in (1,2,3) for x in itertools.product('ACGT',repeat=k))
ARMS=('kmer84','kmer84_plus_releasedPUM2','kmer84_plus_duplicateTGT')
LAMBDAS=(.005,.05,.5)
TOL=1e-12
VIEWS=tuple((pc,ip,inp) for pc in (.5,1.) for ip,inp in (('mean','mean'),('1','mean'),('2','mean'),('mean','1'),('mean','2'),('1','1'),('1','2'),('2','1'),('2','2')))
def view_name(v):return 'pc'+str(v[0])+'_IP'+v[1]+'_Input'+v[2]
PRIMARY=view_name(VIEWS[0])
def vector(sequence):
 assert sequence and set(sequence)<=set('ACGT')
 return [sum(sequence[i:i+len(k)]==k for i in range(max(0,len(sequence)-len(k)+1)))/max(1,len(sequence)-len(k)+1) for k in KMERS]
def delta_vector(parent,mutant):return [a-b for a,b in zip(vector(mutant),vector(parent))]
def weights(rows):
 assert rows
 genes=sorted({x['lineage'] for x in rows});backgrounds={g:{x['parent_excel_row'] for x in rows if x['lineage']==g} for g in genes}
 sizes={(g,b):sum(x['lineage']==g and x['parent_excel_row']==b for x in rows) for g in genes for b in backgrounds[g]}
 value=[1/(len(genes)*len(backgrounds[x['lineage']])*sizes[x['lineage'],x['parent_excel_row']]) for x in rows]
 assert abs(math.fsum(value)-1)<1e-12
 return value
def macro_errors(rows,truth,prediction):
 assert len(rows)==len(truth)==len(prediction) and rows
 groups={}
 for row,y,p in zip(rows,truth,prediction):
  assert math.isfinite(y) and math.isfinite(p)
  groups.setdefault((row['lineage'],row['parent_excel_row']),[]).append(abs(y-p))
 gene={}
 for (g,b),values in groups.items():gene.setdefault(g,[]).append(math.fsum(values)/len(values))
 per={g:math.fsum(v)/len(v) for g,v in gene.items()}
 return math.fsum(per.values())/len(per),per
def choose_lambda(scores):
 assert set(scores)==set(LAMBDAS) and all(math.isfinite(v) for v in scores.values())
 best=min(scores.values())
 return max(lam for lam,value in scores.items() if value<=best+TOL)
def sample_effect(counts,protein,view):
 pc,ip,inp=view
 def logmean(prefix,choice):
  values=[counts[prefix+'_'+column+'.raw']['value'] for column in (('1','2') if choice=='mean' else (choice,))]
  assert all(isinstance(x,int) and x>=0 for x in values)
  return math.fsum(math.log2(x+pc) for x in values)/len(values)
 return logmean(protein+'_IP',ip)-logmean('Input',inp)
def targets(rows,raw,protein):
 return {view_name(v):[sample_effect(raw[r['source_variant_excel_row']]['raw_counts'],protein,v)-sample_effect(raw[r['parent_excel_row']]['raw_counts'],protein,v) for r in rows] for v in VIEWS}
def average_ranks(values):
 ordered=sorted(range(len(values)),key=lambda i:values[i]);rank=[0.]*len(values);start=0
 while start<len(ordered):
  stop=start+1
  while stop<len(ordered) and values[ordered[stop]]==values[ordered[start]]:stop+=1
  value=(start+1+stop)/2
  for i in ordered[start:stop]:rank[i]=value
  start=stop
 return rank
def correlation(a,b):
 assert len(a)==len(b) and a
 ma=math.fsum(a)/len(a);mb=math.fsum(b)/len(b)
 aa=math.fsum((v-ma)**2 for v in a);bb=math.fsum((v-mb)**2 for v in b)
 return None if aa==0 or bb==0 else math.fsum((x-ma)*(y-mb) for x,y in zip(a,b))/math.sqrt(aa*bb)
def menu_metrics(ids,truth,pred):
 assert ids and len(set(ids))==len(ids) and len(ids)==len(truth)==len(pred)
 high=max(truth);low=min(truth);span=high-low;phigh=max(pred);plow=min(pred)
 imax=min((i for i,p in enumerate(pred) if p>=phigh-TOL),key=lambda i:ids[i])
 imin=min((i for i,p in enumerate(pred) if p<=plow+TOL),key=lambda i:ids[i])
 regret_max=0. if span<=TOL else (high-truth[imax])/span
 regret_min=0. if span<=TOL else (truth[imin]-low)/span
 return {'spearman':correlation(average_ranks(truth),average_ranks(pred)),'normalized_regret_max':regret_max,'normalized_regret_min':regret_min,
 'normalized_regret_both':.5*(regret_max+regret_min),'flat_truth':span<=TOL,'flat_prediction':phigh-plow<=TOL,'selected_max_ID':ids[imax],'selected_min_ID':ids[imin]}
def quantile(values,q):
 assert values and 0<=q<=1
 values=sorted(values);position=(len(values)-1)*q;i=int(position);j=min(i+1,len(values)-1)
 return values[i]+(values[j]-values[i])*(position-i)
def comparison(candidate,control):
 assert set(candidate)==set(control) and len(candidate)==7
 differences={g:control[g]-candidate[g] for g in candidate};baseline=math.fsum(control.values())/7
 gain=math.fsum(differences.values())/7
 best=min(differences,key=lambda g:(-differences[g],g))
 return {'macro_MAE_gain':gain,'relative_MAE_gain':None if baseline<=TOL else gain/baseline,'zero_control_MAE':baseline<=TOL,
 'improved_lineages':sum(v>TOL for v in differences.values()),'lineage_gains':differences,'best_lineage':best,
 'leave_best_lineage_out_gain':math.fsum(v for g,v in differences.items() if g!=best)/6}
