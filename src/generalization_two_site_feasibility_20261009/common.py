from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
NS="generalization_two_site_feasibility_20261009"
OUT=ROOT/"results"/NS
REP=ROOT/"reports"/NS
MAX_INPUT_BYTES=10*2**20
DESIGN=ROOT/"results/generalization_prelib_design_metadata_20261008/TableS4_PRELibB_metadata_v2.json"
PARENTS=ROOT/"results/generalization_prelib_point_ancestry_20261008/parent_template_metadata_v2.json"
ANCESTRY=ROOT/"results/generalization_prelib_point_ancestry_20261008/point_metadata_receipt_v2.json"
PARAMETER=ROOT/"results/generalization_pum2_parameter_metadata_20261008/acquisition_receipt_v2.json"
def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for block in iter(lambda:f.read(65536),b""):h.update(block)
 return h.hexdigest()
def strict_pairs(pairs):
 d={}
 for k,v in pairs:
  if k in d:raise ValueError("Duplicate JSON key")
  d[k]=v
 return d
def read(path):
 p=Path(path);assert p.stat().st_size<=MAX_INPUT_BYTES
 return json.loads(p.read_text(encoding="utf-8"),object_pairs_hook=strict_pairs)
def save(path,value):
 with Path(path).open("xb") as f:
  f.write((json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+"\n").encode())
def data_sha(value):
 return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
