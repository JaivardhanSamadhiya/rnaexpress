"""Independent direct-contact arithmetic, not a production helper import."""
import csv,hashlib,itertools,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RT=.0019872041*298.15
MODES=('no_flip_no_c1c2','coupled_consecutive','released_csv','fit_region_truncated')
PERMISSIONS={
 'released_csv':{(): (True,True),(3,):(True,True),(4,):(False,True),(5,):(False,False),(6,):(False,False),
 (3,4):(False,True),(3,5):(False,False),(3,6):(False,False),(4,5):(False,False),(4,6):(False,False),(5,6):(False,False)},
 'fit_region_truncated':{(): (True,True),(3,):(True,True),(4,):(True,True),(5,):(False,True),(6,):(False,False),
 (3,4):(True,True),(3,5):(False,True),(3,6):(False,False),(4,5):(False,True),(4,6):(False,False),(5,6):(False,False)}}
def parameters():
 receipt=json.loads((ROOT/'results/generalization_pum2_parameter_metadata_20261008/acquisition_receipt_v2.json').read_text())
 assert receipt['resolved_author_commit']=='28ebbad0950a8a915ee09711144d8e5bea8fa79a'
 tables={}
 for record in receipt['records']:
  data=(ROOT/'data/raw/generalization_pum2_parameter_metadata_20261008'/record['filename']).read_bytes()
  assert hashlib.sha256(data).hexdigest()==record['receipt']['sha256']
  reader=csv.DictReader(data.decode('utf-8-sig').splitlines()); rows={}
  for row in reader:
   key=row.pop('');assert key not in rows
   rows[key]={b:float(v) for b,v in row.items()}
   assert all(math.isfinite(v) for v in rows[key].values())
  tables[record['filename']]=rows
 assert set(tables)=={'PUM2_qMotif_term1.csv','PUM2_qMotif_term2_single.csv','PUM2_qMotif_term2_double.csv','PUM2_qMotif_term3.csv'}
 b=tables['PUM2_qMotif_term1.csv'];s=tables['PUM2_qMotif_term2_single.csv'];d=tables['PUM2_qMotif_term2_double.csv'];c=tables['PUM2_qMotif_term3.csv']
 assert set(b)==set(map(str,range(9))) and set(s)==set(map(str,range(3,7))) and set(d)=={'4','5'} and set(c)=={'c1','c2'}
 assert all(set(row)==set('ACGU') for row in list(b.values())+list(s.values()))
 assert all(set(row)=={'NN'} for row in d.values()) and all(set(row)=={'1'} for row in c.values())
 return (b,s,d,c)
def configurations(mode):
 assert mode in MODES
 yield (9,'consecutive',(),(True,True) if mode!='no_flip_no_c1c2' else (False,False))
 if mode not in PERMISSIONS:return
 for gaps in ((3,),(4,),(5,),(6,),(3,4),(3,5),(3,6),(4,5),(4,6),(5,6)):
  yield (9+len(gaps),'single' if len(gaps)==1 else 'two_singles',gaps,PERMISSIONS[mode][gaps])
 yield (11,'adjacent_double',(5,),(False,True))
 yield (11,'adjacent_double',(6,),(False,False))
def coordinates(start,kind,gaps):
 # Nine retained contact coordinates computed directly, no sequence deletion.
 return tuple(start+k+(2*int(k>=gaps[0]) if kind=='adjacent_double' else sum(k>=g for g in gaps)) for k in range(9))
def registers(sequence,p,mode):
 assert sequence and len(sequence)<=260 and (set(sequence)<=set('ACGT') or set(sequence)<=set('ACGU'))
 sequence=sequence.replace('T','U');base,single,double,coupling=p
 for length,kind,gaps,permissions in configurations(mode):
  for start in range(max(0,len(sequence)-length+1)):
   contact=coordinates(start,kind,gaps)
   assert contact[0]==start and contact[-1]==start+length-1 and len(set(contact))==9
   retained=tuple(sequence[pos] for pos in contact)
   terms=[base[str(k)][retained[k]] for k in range(8)]
   if retained[7]=='A':terms.append(base['8'][retained[8]])
   if permissions[0] and retained[4] in ('C','U') and retained[5]=='A' and retained[6]=='G' and retained[7]!='A':terms.append(coupling['c1']['1'])
   if permissions[1] and retained[5]!='A' and retained[6]=='C' and retained[7]!='A':terms.append(coupling['c2']['1'])
   if kind in ('single','two_singles'):
    for order,g in enumerate(gaps):terms.append(single[str(g)][sequence[start+g+order]])
   elif kind=='adjacent_double':terms.append(double[str(gaps[0]-1)]['NN'])
   yield (start,length,kind,gaps),contact,math.fsum(terms)
def score(sequence,p,mode):
 keys=set();energies=[]
 for key,contact,energy in registers(sequence,p,mode):
  assert key not in keys;keys.add(key);energies.append(energy)
 if not energies:return {'available':False,'state_count':0,'logZ':None,'relative_ensemble_energy_kcal':None,'best_state_energy_kcal':None}
 # A distinct arithmetic path for bounded short fragments; no log-sum-exp helper.
 z=math.fsum(math.exp(-energy/RT) for energy in energies)
 assert z>0 and math.isfinite(z)
 logz=math.log(z)
 return {'available':True,'state_count':len(keys),'logZ':logz,'relative_ensemble_energy_kcal':-RT*logz,'best_state_energy_kcal':min(energies)}
