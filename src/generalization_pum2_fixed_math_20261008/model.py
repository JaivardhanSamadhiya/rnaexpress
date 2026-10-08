"""Independent register-state implementation; no copied author code or fitted parameters."""
from dataclasses import dataclass
from pathlib import Path
import csv,hashlib,itertools,json,math
ROOT=Path(__file__).resolve().parents[2]
R_KCAL=.0019872041;TEMPERATURE_K=298.15;RT=R_KCAL*TEMPERATURE_K
MODES=('no_flip_no_c1c2','coupled_consecutive','released_csv','fit_region_truncated')
@dataclass(frozen=True)
class Parameters:
 base:dict
 single:dict
 double:dict
 coupling:dict
@dataclass(frozen=True)
class State:
 start:int
 length:int
 kind:str
 gaps:tuple
 removed:tuple
 retained:str
 coupling_flags:tuple
 energy_kcal:float
 @property
 def key(self):return (self.start,self.length,self.kind,self.gaps)

def table(text,columns,indices):
 rows=list(csv.reader(text.splitlines()));assert rows and rows[0][0]==''
 header=rows[0];assert len(header)==len(set(header)) and set(header[1:])==set(columns)
 result={}
 for row in rows[1:]:
  assert len(row)==len(header) and row[0] in indices and row[0] not in result
  values={c:float(row[header.index(c)]) for c in columns};assert all(math.isfinite(v) for v in values.values())
  result[row[0]]=values
 assert set(result)==set(indices)
 return result

def load_parameters():
 path=ROOT/'results/generalization_pum2_parameter_metadata_20261008/acquisition_receipt_v2.json'
 receipt=json.loads(path.read_text());assert receipt['status']=='PASS_FOUR_FIXED_PUBLIC_PARAMETER_BYTES_AT_RESOLVED_COMMIT'
 assert receipt['resolved_author_commit']=='28ebbad0950a8a915ee09711144d8e5bea8fa79a'
 raw=ROOT/'data/raw/generalization_pum2_parameter_metadata_20261008';texts={}
 for record in receipt['records']:
  data=(raw/record['filename']).read_bytes();assert hashlib.sha256(data).hexdigest()==record['receipt']['sha256']
  texts[record['filename']]=data.decode('utf-8-sig')
 base=table(texts['PUM2_qMotif_term1.csv'],'ACGU',[str(i) for i in range(9)])
 single=table(texts['PUM2_qMotif_term2_single.csv'],'ACGU',[str(i) for i in range(3,7)])
 double=table(texts['PUM2_qMotif_term2_double.csv'],['NN'],['4','5'])
 coupling=table(texts['PUM2_qMotif_term3.csv'],['1'],['c1','c2'])
 return Parameters({(int(i),b):v for i,rs in base.items() for b,v in rs.items()},
  {(int(i),b):v for i,rs in single.items() for b,v in rs.items()},
  {int(i):rs['NN'] for i,rs in double.items()},{i:rs['1'] for i,rs in coupling.items()})

def normalize(sequence):
 assert isinstance(sequence,str) and sequence and len(sequence)<=10000
 # A literal DNA source may be scored as RNA; no strand flip, padding or maturity claim.
 assert set(sequence)<=set('ACGT') or set(sequence)<=set('ACGU'),'Nonliteral/mixed alphabet sequence'
 return sequence.replace('T','U')

def bound_energy(retained,params,flags):
 assert len(retained)==9 and set(retained)<=set('ACGU') and len(flags)==2
 value=sum(params.base[(i,b)] for i,b in enumerate(retained) if i<8 or retained[7]=='A')
 if flags[0] and retained[4] in 'CU' and retained[5]=='A' and retained[6]=='G' and retained[7]!='A':value+=params.coupling['c1']
 if flags[1] and retained[5]!='A' and retained[6]=='C' and retained[7]!='A':value+=params.coupling['c2']
 return value

def guards(gaps,kind,mode):
 assert mode in MODES
 if mode=='no_flip_no_c1c2':return (False,False)
 if not gaps:return (True,True)
 if kind=='adjacent_double':
  assert gaps in ((5,),(6,))
  return (False,gaps==(5,))
 assert kind in ('single','two_singles') and all(g in (3,4,5,6) for g in gaps)
 if mode=='released_csv':return (all(g==3 for g in gaps),all(g<5 for g in gaps))
 assert mode=='fit_region_truncated'
 return (max(gaps)<=4,max(gaps)<=5)

def states(sequence,params,mode='released_csv'):
 assert mode in MODES;sequence=normalize(sequence);n=len(sequence)
 configs=[(9,'consecutive',(),())]
 if mode in ('released_csv','fit_region_truncated'):
  configs += [(10,'single',(g,),(g,)) for g in (3,4,5,6)]
  configs += [(11,'two_singles',(g,h),(g,h+1)) for g,h in itertools.combinations((3,4,5,6),2)]
  configs += [(11,'adjacent_double',(g,),(g,g+1)) for g in (5,6)]
 for length,kind,gaps,removed in configs:
  for start in range(max(0,n-length+1)):
   segment=sequence[start:start+length];retained=''.join(b for i,b in enumerate(segment) if i not in removed)
   flags=guards(gaps,kind,mode);energy=bound_energy(retained,params,flags)
   if kind=='single':energy+=params.single[(gaps[0],segment[removed[0]])]
   elif kind=='two_singles':energy+=sum(params.single[(g,segment[i])] for g,i in zip(gaps,removed))
   elif kind=='adjacent_double':energy+=params.double[gaps[0]-1]
   yield State(start,length,kind,gaps,removed,retained,flags,energy)

def log_partition(energies):
 values=[-e/RT for e in energies]
 if not values:return None
 assert all(math.isfinite(v) for v in values)
 maximum=max(values)
 return maximum+math.log(math.fsum(math.exp(v-maximum) for v in values))

def score(sequence,params,mode='released_csv'):
 registers=list(states(sequence,params,mode));n=len(registers)
 assert len({s.key for s in registers})==n,'State counted more than once'
 if not registers:return {'available':False,'state_count':0,'logZ':None,'relative_ensemble_energy_kcal':None,'best_state_energy_kcal':None}
 logz=log_partition(s.energy_kcal for s in registers)
 return {'available':True,'state_count':n,'logZ':logz,'relative_ensemble_energy_kcal':-RT*logz,'best_state_energy_kcal':min(s.energy_kcal for s in registers)}
