from pathlib import Path
import json,hashlib,zipfile,io,xml.etree.ElementTree as ET,re,subprocess
from src.generalization_prelib_header_inventory_20261008.inventory import xread,N
ROOT=Path(__file__).resolve().parents[2];NS="generalization_prelib_design_metadata_20261008";OUT=ROOT/"results"/NS
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(p,value):
 with p.open("xb") as f:f.write((json.dumps(value,sort_keys=True,indent=2)+"\n").encode())
def letter(cell):
 m=re.fullmatch(r"([A-Z]+)(\d+)",cell);assert m
 return m[1],int(m[2])
def decode(z,worksheet,selected):
 shared=[]
 if "xl/sharedStrings.xml" in z.namelist():
  root=ET.fromstring(xread(z,"xl/sharedStrings.xml"))
  shared=["".join(t.text or "" for t in si.iter("{"+N["m"]+"}t")) for si in root]
  assert len(shared)<=100000 and all(len(s)<=10000 for s in shared)
 rows=[];observed_header=None
 for event,row in ET.iterparse(io.BytesIO(xread(z,worksheet)),events=("end",)):
  if row.tag!="{"+N["m"]+"}row":continue
  number=int(row.attrib["r"]);assert 1<=number<=10000
  values={}
  for cell in row:
   column,cellrow=letter(cell.attrib["r"]);assert cellrow==number
   if column not in selected:continue
   assert cell.find("m:f",N) is None,"Formula in selected metadata field"
   typ=cell.attrib.get("t","n");node=cell.find("m:v",N)
   if typ=="s":
    assert node is not None;slot=int(node.text);assert 0<=slot<len(shared);value=shared[slot]
   elif typ=="inlineStr":value="".join(t.text or "" for t in cell.iter("{"+N["m"]+"}t"))
   elif typ=="str":value=None if node is None else node.text
   else:
    assert typ=="n" and selected[column] in ("Subset","Number of oligos"),"Nonliteral string design field"
    if node is None or node.text is None:value=None
    else:
     from decimal import Decimal
     numeric=Decimal(node.text);assert numeric.is_finite() and numeric==numeric.to_integral() and 0<=numeric<=10000
     value=int(numeric)
   assert value is None or isinstance(value,int) or isinstance(value,str) and len(value)<=10000
   values[selected[column]]=value
  if number==1:
   assert all(values.get(name)==name for name in selected.values());observed_header=True
  elif values:rows.append({"source_excel_row":number,**{name:values.get(name) for name in selected.values()}})
  row.clear()
 assert observed_header and len(rows)<=7000
 return rows
def run():
 manifest=read(OUT/"design_metadata_manifest.json");p=OUT/"design_metadata_manifest.json"
 assert subprocess.check_output(["git","show","HEAD:"+p.relative_to(ROOT).as_posix()],cwd=ROOT)==p.read_bytes()
 for name,digest in manifest["files"].items():assert sha(ROOT/name)==digest,name
 headers=read(ROOT/"results/generalization_prelib_header_inventory_20261008/header_inventory_receipt.json")
 assert headers["status"]=="PASS_BOUNDED_WORKBOOK_SHEET_AND_ROW1_HEADER_INVENTORY_ONLY"
 acq=read(ROOT/"results/generalization_prelib_metadata_acquisition_20261008/acquisition_receipt.json")
 archive=ROOT/acq["archive_path"];assert sha(archive)==acq["archive_sha256"]
 books={b["bundle_member"]:b for b in headers["workbooks"]}
 records=[];files={}
 with zipfile.ZipFile(archive) as bundle:
  for member,allowed in manifest["allowlist"].items():
   book=books[member];assert len(book["sheets"])==1
   sheet=book["sheets"][0]
   selected={h["cell"][:-1]:h["value"] for h in sheet["headers"] if h["value"] in allowed}
   assert set(selected.values())==set(allowed)
   payload=bundle.read(member);assert hashlib.sha256(payload).hexdigest()==book["workbook_sha256"]
   with zipfile.ZipFile(io.BytesIO(payload)) as z:rows=decode(z,sheet["worksheet_member"],selected)
   output=OUT/(member[:-5]+"_metadata.json")
   save(output,{"source_workbook_member":member,"source_workbook_sha256":book["workbook_sha256"],"sheet":sheet["name"],
       "selected_columns_only":allowed,"rows":rows,"nonselected_values_analyzed":False,"parent_pairs_admitted":0})
   files[output.relative_to(ROOT).as_posix()]=sha(output)
   sequence_field="Baseline sequence" if "Baseline sequence" in allowed else "Sequence" if "Sequence" in allowed else None
   summary={"workbook":member,"rows":len(rows),"selected_fields":allowed}
   if sequence_field:
    seqs=[r[sequence_field] for r in rows]
    summary["sequence_lengths"]=sorted(set(len(s) for s in seqs if s is not None))
    summary["nonliteral_ACGT_sequence_rows"]=sum(not isinstance(s,str) or not set(s)<=set("ACGT") for s in seqs)
   if "Number of oligos" in allowed:summary["reported_design_oligo_count_sum"]=sum(r["Number of oligos"] for r in rows if isinstance(r["Number of oligos"],int))
   records.append(summary);print(json.dumps(summary,sort_keys=True),flush=True)
 save(OUT/"design_metadata_receipt.json",{"status":"PASS_PRELIB_FIXED_DESIGN_FIELDS_ONLY","manifest_sha256":sha(p),
    "records":records,"files":files,"parent_pairs_admitted":0,"count_or_outcome_values_analyzed":False,"models_fit":0,
    "shared_string_and_worksheet_bytes_internally_loaded":True,"only_allowlisted_cells_semantically_decoded":True})
if __name__=="__main__":run()
