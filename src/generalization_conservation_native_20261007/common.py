"""Fixed exact-coordinate identities and two-stage source certification."""
from __future__ import annotations
from pathlib import Path
import gzip,hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
NS='generalization_conservation_native_20261007'
SRC,REP,OUT,ART=[ROOT/top/NS for top in ('src','reports','results','artifacts')]
FEAS=ROOT/'results/generalization_conservation_features_feasibility_20261007'
MAP=ROOT/'results/generalization_conservation_mapping_20261007'
TRACKS=('phyloP60wayAll','phastCons60way')
MAPPED='reference_site_vector_unique_complete_candidates'
MAP_SHA='ae393a91e19b1394763a27d49275df078aabac5688bb33f26214b040e2d43c62'
REPLAY_SHA='cc41a93dca06f1f528720d8ddfd24f4f4b563fc81ff244f3bf142465e4e23218'
FEAS_SHA='a954739e4193b2d937062ea3cd2ca77b2aa26d1e7572dd5d2071dc182a635316'
API='https://api.genome.ucsc.edu'
MAX_RESPONSE=4_000_000
MAX_TOTAL=100_000_000
RATE=1.05
SCHEMA_DESIGN=OUT/'code_schema_design_manifest.json'
VALUE_DESIGN=OUT/'value_extraction_manifest.json'
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def save(path,data):
 p=Path(path).resolve();assert any(p.is_relative_to(d.resolve()) for d in (SRC,REP,OUT,ART))
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==data,'Preserve existing artifact: '+str(p)
 else:
  with p.open('xb') as f:f.write(data)
def jsave(path,data):save(path,(json.dumps(data,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())
def gread(path):return json.loads(gzip.decompress(Path(path).read_bytes()))
def bind_mapping():
 assert sha(MAP/'mapping_receipt.json')==MAP_SHA and sha(MAP/'independent_mapping_replay_receipt.json')==REPLAY_SHA
 r=read(MAP/'mapping_receipt.json');v=read(MAP/'independent_mapping_replay_receipt.json')
 assert r['status']=='COMPLETED_FULL_COORDINATE_METADATA_ONLY' and v['status']=='PASS_FULL_DIRECT_COORDINATE_REPLAY_ONLY'
 assert v['mapping_receipt_sha256']==MAP_SHA and r['original_candidate_rows']==26258
 for relative,digest in r['files'].items():assert sha(ROOT/relative)==digest
 return r,v
def bind_feasibility():
 assert sha(FEAS/'preparation_receipt.json')==FEAS_SHA,'Preserved v1 feasibility identity changed'
 receipt=read(FEAS/'preparation_receipt.json');assert receipt['file_count']==len(receipt['files'])==23
 for section in ('files','external_coordinate_and_metadata_bindings'):
  for relative,digest in receipt[section].items():assert sha(ROOT/relative)==digest,'Preserved v1 feasibility bytes changed: '+relative
 return receipt
def certify(path,committed=True):
 m=read(path)
 for relative,digest in m['files'].items():assert sha(ROOT/relative)==digest,'Pinned byte change: '+relative
 if committed:
  relative=Path(path).relative_to(ROOT).as_posix()
  b=subprocess.run(['git','show','HEAD:'+relative],cwd=ROOT,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout
  assert hashlib.sha256(b).hexdigest()==sha(path),'Root must commit exact manifest before network calls'
 bind_mapping();bind_feasibility()
 return m
def reference_inventory():
 bind_feasibility()
 sites=read(FEAS/'certified_site_inventory.json');rows=gread(FEAS/'all_original_row_site_metadata.json.gz')
 assert len(sites)==15132 and len(rows)==26258 and len({r['intervention_id'] for r in rows})==26258
 ref={(s['chrom'],s['position0']):s['reference'] for s in sites}
 assert len(ref)==15132
 for r in rows:
  cc=r['edited_site_coordinates'];assert bool(cc)==(r['mapping_status']==MAPPED)
  for c in cc:
   assert ref[c['chrom'],c['genomic_position0']]==c['genomic_reference']
   assert c['genomic_reference'] in 'ACGT' and c['genomic_alternate'] in 'ACGT' and c['genomic_reference']!=c['genomic_alternate']
 return sites,rows
