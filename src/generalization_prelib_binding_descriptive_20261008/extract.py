"""Selected raw-count preservation and pairing-invariant descriptive association."""
from pathlib import Path
import collections,datetime,decimal,hashlib,io,json,math,re,subprocess,zipfile
import xml.etree.ElementTree as ET
from src.generalization_prelib_header_inventory_20261008.inventory import N,xread
ROOT=Path(__file__).resolve().parents[2]
NS="generalization_prelib_binding_descriptive_20261008";OUT=ROOT/"results"/NS
FIELDS={"A":"ID","C":"Sequence","L":"Input_1.raw","M":"Input_2.raw",
        "N":"PUM1_IP_1.raw","O":"PUM1_IP_2.raw","P":"PUM2_IP_1.raw","Q":"PUM2_IP_2.raw"}
COUNTS=tuple(FIELDS[c] for c in ("L","M","N","O","P","Q"))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def save(p,x):
 data=(json.dumps(x,sort_keys=True,indent=2,allow_nan=False)+"\n").encode()
 assert len(data)<=40*2**20,"Bounded output exceeded"
 with p.open("xb") as f:f.write(data)
def certify():
 p=OUT/"descriptive_manifest.json";m=read(p)
 assert subprocess.check_output(["git","show","HEAD:"+p.relative_to(ROOT).as_posix()],cwd=ROOT)==p.read_bytes()
 for name,digest in m["files"].items():assert sha(ROOT/name)==digest,name
 assert m["training_pairs_admitted"]==m["models_fit"]==0
 return m
def text_cell(cell,shared):
 assert cell is not None and cell.find("m:f",N) is None,"Missing or formula identity"
 typ=cell.attrib.get("t","n");v=cell.find("m:v",N)
 if typ=="s":
  assert v is not None;slot=int(v.text);assert 0<=slot<len(shared);value=shared[slot]
 elif typ=="inlineStr":value="".join(t.text or "" for t in cell.iter("{"+N["m"]+"}t"))
 elif typ=="str":value=None if v is None else v.text
 else:raise AssertionError("Source identity is not a literal string")
 assert isinstance(value,str) and len(value)<=10000
 return value
def count_cell(cell):
 if cell is None:return {"value":None,"source_token":None,"missing_kind":"absent_cell"}
 assert cell.find("m:f",N) is None,"Formula raw count refused; cached value never used"
 assert cell.attrib.get("t","n")=="n","Raw count must be numerical literal or blank"
 v=cell.find("m:v",N)
 if v is None or v.text is None:return {"value":None,"source_token":None,"missing_kind":"blank_numeric_cell"}
 token=v.text;number=decimal.Decimal(token)
 assert number.is_finite() and number==number.to_integral() and 0<=number<=10**12,"Invalid nonnegative integral raw count"
 return {"value":int(number),"source_token":token,"missing_kind":None}
def decode(z,worksheet,expected):
 shared=[]
 if "xl/sharedStrings.xml" in z.namelist():
  root=ET.fromstring(xread(z,"xl/sharedStrings.xml"))
  shared=["".join(t.text or "" for t in si.iter("{"+N["m"]+"}t")) for si in root]
  assert len(shared)<=100000 and all(len(s)<=10000 for s in shared)
 rows={};header_seen=False;last=0
 for event,row in ET.iterparse(io.BytesIO(xread(z,worksheet)),events=("end",)):
  if row.tag!="{"+N["m"]+"}row":continue
  number=int(row.attrib["r"]);assert last<number<=7000;last=number
  cells={}
  for cell in row:
   match=re.fullmatch(r"([A-Z]+)(\d+)",cell.attrib["r"]);assert match and int(match[2])==number
   if match[1] in FIELDS:
    assert match[1] not in cells,"Duplicate selected cell"
    cells[match[1]]=cell
  if number==1:
   assert {c:text_cell(cells.get(c),shared) for c in FIELDS}==FIELDS,"Raw field/header identity mismatch"
   header_seen=True
  elif number in expected:
   e=expected[number]
   # Certify both literal identities before opening any count in this row.
   assert text_cell(cells.get("A"),shared)==e["ID"],"Source row ID mismatch"
   assert text_cell(cells.get("C"),shared)==e["Sequence"],"Source row sequence mismatch"
   rows[number]={"source_excel_row":number,"ID":e["ID"],"Sequence":e["Sequence"],
     "sequence_sha256":hashlib.sha256(e["Sequence"].encode()).hexdigest(),
     "raw_counts":{FIELDS[c]:count_cell(cells.get(c)) for c in FIELDS if c not in ("A","C")}}
  row.clear()
 assert header_seen and set(rows)==set(expected),"Cohort source row missing"
 return rows
def mean_log(values,pseudo):
 assert pseudo in (.5,1.)
 if any(x is None for x in values):return None
 assert len(values)==2 and all(type(x) is int and 0<=x<=10**12 for x in values)
 return sum(math.log2(x+pseudo) for x in values)/2

def effect(mutant,parent,protein,pseudo):
 def pair(row,prefix):return [row["raw_counts"][prefix+str(i)+".raw"]["value"] for i in (1,2)]
 mi=pair(mutant,protein+"_IP_");pi=pair(parent,protein+"_IP_")
 mn=pair(mutant,"Input_");pn=pair(parent,"Input_")
 components=[mean_log(v,pseudo) for v in (mi,pi,mn,pn)]
 if any(v is None for v in components):
  return {"complete":False,"delta_mean_log_enrichment":None,"delta_logIP":None,"delta_logInput":None,
          "crossed_input_deltas":None,"missing_source_counts":sum(v is None for a in (mi,pi,mn,pn) for v in a)}
 mip,pip,minp,pinp=components
 ipdelta=[math.log2(x+pseudo)-math.log2(y+pseudo) for x,y in zip(mi,pi)]
 inputdelta=[math.log2(x+pseudo)-math.log2(y+pseudo) for x,y in zip(mn,pn)]
 crossed=[[x-y for y in inputdelta] for x in ipdelta]
 delta=(mip-pip)-(minp-pinp)
 assert abs(delta-sum(v for a in crossed for v in a)/4)<1e-12
 return {"complete":True,"mutant_mean_log_enrichment":mip-minp,"parent_mean_log_enrichment":pip-pinp,
         "delta_mean_log_enrichment":delta,"delta_logIP":mip-pip,"delta_logInput":minp-pinp,
         "IP_column_deltas":ipdelta,"Input_column_deltas":inputdelta,"crossed_input_deltas":crossed,
         "crossed_cells_are_not_four_independent_replicates":True}
def run():
 m=certify();points=read(ROOT/m["point_relations"]);parents=read(ROOT/m["parent_metadata"])
 design=read(ROOT/m["source_design"]);byrow={r["source_excel_row"]:r for r in design["rows"]}
 assert len(byrow)==6293 and len(points)==4054 and len(parents)==16
 expected={p["source_excel_row"]:byrow[p["source_excel_row"]] for p in parents}
 for p in parents:
  e=expected[p["source_excel_row"]]
  assert e["ID"]==p["source_parent_ID"] and hashlib.sha256(e["Sequence"].encode()).hexdigest()==p["parent_sequence_sha256"]
 for p in points:
  e=byrow[p["source_variant_excel_row"]];parent=expected[p["parent_excel_row"]]
  assert e["ID"]==p["source_variant_ID"] and parent["ID"]==p["source_parent_ID"]
  assert p["literal_one_substitution_checked"] and p["issue"] is None
  pos=p["source_coordinate_0based"];assert parent["Sequence"][pos]==p["ref"]
  assert parent["Sequence"][:pos]+p["alt"]+parent["Sequence"][pos+1:]==e["Sequence"]
  assert hashlib.sha256(e["Sequence"].encode()).hexdigest()==p["variant_sequence_sha256"]
  assert e["source_excel_row"] not in expected
  expected[e["source_excel_row"]]=e
 assert len(expected)==4070 and len({r["ID"] for r in expected.values()})==4070
 assert len({r["Sequence"] for r in expected.values()})==4070
 headers=read(ROOT/m["header_receipt"])
 book=next(b for b in headers["workbooks"] if b["bundle_member"]=="TableS4_PRELibB.xlsx")
 sheet=book["sheets"][0];assert sheet["name"]=="PRELibB.nice"
 assert {h["cell"][:-1]:h["value"] for h in sheet["headers"] if h["cell"][:-1] in FIELDS}==FIELDS
 save(OUT/"outcome_exposure_started.json",{"UTC":datetime.datetime.now(datetime.timezone.utc).isoformat(),
   "manifest_sha256":sha(OUT/"descriptive_manifest.json"),"resource_is_exposed_development_after_this_run":True,
   "selected_raw_count_cells_to_be_opened":4070*6,"nonselected_numerical_endpoints_closed":True,"training_pairs_admitted":0})
 with zipfile.ZipFile(ROOT/m["archive_path"]) as bundle:
  payload=bundle.read(book["bundle_member"]);assert len(payload)<=4*2**20 and hashlib.sha256(payload).hexdigest()==book["workbook_sha256"]
  with zipfile.ZipFile(io.BytesIO(payload)) as z:
   assert len(z.infolist())<=100 and sum(i.file_size for i in z.infolist())<=64*2**20
   rows=decode(z,sheet["worksheet_member"],expected)
 save(OUT/"selected_raw_count_rows.json",{"source_workbook_SHA256":book["workbook_sha256"],"source_sheet":sheet["name"],
    "field_columns":FIELDS,"rows":[rows[i] for i in sorted(rows)],"unselected_values_semantically_decoded":False,
    "source_UMI_processing_independently_replayed":False,"replicate_pairing_independently_certified":False})
 effects=[]
 for p in points:
  mutant=rows[p["source_variant_excel_row"]];parent=rows[p["parent_excel_row"]]
  effects.append({"source_variant_ID":p["source_variant_ID"],"source_variant_excel_row":p["source_variant_excel_row"],
    "source_parent_ID":p["source_parent_ID"],"parent_excel_row":p["parent_excel_row"],"lineage_nominal":p["lineage"],
    "prefix":p["prefix"],"mPRE_background":p["mPRE_background"],"training_pair_admitted":False,
    "association_effects":{protein:{str(pseudo):effect(mutant,parent,protein,pseudo) for pseudo in (.5,1.)} for protein in ("PUM1","PUM2")}})
 save(OUT/"descriptive_point_association_effects.json",effects)
 parent_controls=[]
 for p in parents:
  row=rows[p["source_excel_row"]]
  parent_controls.append({"source_parent_ID":p["source_parent_ID"],"effects":{
    protein:{str(a):effect(row,row,protein,a) for a in (.5,1.)} for protein in ("PUM1","PUM2")}})
 for p in parent_controls:
  for endpoint in p["effects"].values():
   for x in endpoint.values():assert not x["complete"] or x["delta_mean_log_enrichment"]==0
 save(OUT/"parent_self_delta_controls.json",parent_controls)
 count_summary={c:{"missing":sum(r["raw_counts"][c]["value"] is None for r in rows.values()),
   "observed_zero":sum(r["raw_counts"][c]["value"]==0 for r in rows.values())} for c in COUNTS}
 completeness={protein:sum(e["association_effects"][protein]["0.5"]["complete"] for e in effects) for protein in ("PUM1","PUM2")}
 receipt={"status":"PASS_FIXED_POINT_COHORT_RAW_COUNTS_AND_PAIRING_INVARIANT_DESCRIPTIVE_ASSOCIATION_NOT_TRAINING_ADMISSION",
  "manifest_sha256":sha(OUT/"descriptive_manifest.json"),"source_workbook_sha256":book["workbook_sha256"],
  "selected_source_rows":len(rows),"point_relations":len(effects),"parent_rows":len(parents),"raw_count_cells":len(rows)*6,
  "raw_count_summary":count_summary,"complete_point_effects_by_protein":completeness,"cohort_outcome_filtered":False,
  "pseudocounts_fixed_before_values":[.5,1.],"input_IP_suffix_pairing_assumed":False,"independent_replicates_not_inferred":True,
  "not_a_DESeq2_author_result_reproduction":True,"author_plasmid_and_padj_filter_not_reproduced":True,
  "no_binding_affinity_or_localization_claim":True,"whole_workbook_XML_and_sharedstrings_internally_loaded":True,
  "nonselected_l2fc_plasmid_normalized_occupancy_expression_values_closed":True,"training_pairs_admitted":0,"models_fit":0,
  "files":{p.relative_to(ROOT).as_posix():sha(p) for p in (OUT/"selected_raw_count_rows.json",OUT/"descriptive_point_association_effects.json",OUT/"parent_self_delta_controls.json",OUT/"outcome_exposure_started.json")}}
 save(OUT/"descriptive_receipt.json",receipt);print(json.dumps(receipt,sort_keys=True),flush=True)
if __name__=="__main__":run()
