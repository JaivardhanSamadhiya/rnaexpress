from pathlib import Path
import json,hashlib,zipfile,io,posixpath,xml.etree.ElementTree as ET,subprocess,re
ROOT=Path(__file__).resolve().parents[2];NS="generalization_prelib_header_inventory_20261008";OUT=ROOT/"results"/NS
N={"m":"http://schemas.openxmlformats.org/spreadsheetml/2006/main",
 "r":"http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def xread(z,name,cap=32*1024**2):
 info=z.getinfo(name);assert info.file_size<=cap
 value=z.read(name);assert len(value)<=cap
 return value
def column_index(cell):
 m=re.fullmatch(r"([A-Z]+)1",cell);assert m
 index=0
 for letter in m[1]:index=index*26+ord(letter)-64
 return index
def run():
 manifest=read(OUT/"inventory_manifest.json")
 p=OUT/"inventory_manifest.json";assert subprocess.check_output(["git","show","HEAD:"+p.relative_to(ROOT).as_posix()],cwd=ROOT)==p.read_bytes()
 for name,digest in manifest["files"].items():assert sha(ROOT/name)==digest,name
 acquisition=read(ROOT/"results/generalization_prelib_metadata_acquisition_20261008/acquisition_receipt.json")
 assert acquisition["status"]=="PASS_PRIMARY_PUBLIC_ARCHIVE_BYTES_CRC_AND_INVENTORY"
 archive=ROOT/acquisition["archive_path"];assert sha(archive)==acquisition["archive_sha256"]
 books=[]
 with zipfile.ZipFile(archive) as bundle:
  for name in sorted(n for n in bundle.namelist() if n.endswith(".xlsx")):
   payload=bundle.read(name);assert len(payload)<=4*1024**2
   with zipfile.ZipFile(io.BytesIO(payload)) as z:
    assert len(z.infolist())<=100 and sum(i.file_size for i in z.infolist())<=64*1024**2
    relationships=ET.fromstring(xread(z,"xl/_rels/workbook.xml.rels",1024**2))
    rels={r.attrib["Id"]:r.attrib for r in relationships}
    workbook=ET.fromstring(xread(z,"xl/workbook.xml",1024**2))
    shared=[]
    if "xl/sharedStrings.xml" in z.namelist():
     sharedroot=ET.fromstring(xread(z,"xl/sharedStrings.xml"))
     shared=["".join(t.text or "" for t in si.iter("{"+N["m"]+"}t")) for si in sharedroot]
     assert len(shared)<=100000 and all(len(s)<=10000 for s in shared)
    sheets=[]
    for sheet in workbook.find("m:sheets",N):
     rel=rels[sheet.attrib["{"+N["r"]+"}id"]]
     assert rel.get("TargetMode","Internal")=="Internal"
     target=rel["Target"];path=target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/"+target)
     assert path.startswith("xl/worksheets/") and ".." not in path.split("/")
     headers=[];first_row_seen=False
     # Stop the streaming semantic parse immediately after row1; no later cell values traversed.
     for event,row in ET.iterparse(io.BytesIO(xread(z,path)),events=("end",)):
      if row.tag!="{"+N["m"]+"}row":continue
      assert row.attrib["r"]=="1","First row is not header row1"
      first_row_seen=True
      for cell in row:
       index=column_index(cell.attrib["r"]);assert index<=256
       typ=cell.attrib.get("t","n")
       if cell.find("m:f",N) is not None:
        header={"cell":cell.attrib["r"],"type":"formula_header_not_evaluated","value":None}
       elif typ=="s":
        value=cell.find("m:v",N);assert value is not None
        slot=int(value.text);assert 0<=slot<len(shared)
        header={"cell":cell.attrib["r"],"type":"shared_string_header","value":shared[slot]}
       elif typ=="inlineStr":
        header={"cell":cell.attrib["r"],"type":"inline_string_header","value":"".join(t.text or "" for t in cell.iter("{"+N["m"]+"}t"))}
       elif typ=="str":
        value=cell.find("m:v",N);header={"cell":cell.attrib["r"],"type":"literal_string_header","value":None if value is None else value.text}
       else:header={"cell":cell.attrib["r"],"type":"nonstring_header_presence_only","value":None}
       assert header["value"] is None or len(header["value"])<=10000
       headers.append(header)
      break
     sheets.append({"name":sheet.attrib["name"],"worksheet_member":path,"row1_present":first_row_seen,"headers":headers,
       "later_rows_semantically_traversed":False})
    books.append({"bundle_member":name,"workbook_sha256":hashlib.sha256(payload).hexdigest(),"sheets":sheets,
      "shared_strings_loaded_internally":True,"shared_strings_reported_except_row1_headers":False,
      "numerical_outcome_values_analyzed":False,"formula_or_external_link_execution":False})
 result={"status":"PASS_BOUNDED_WORKBOOK_SHEET_AND_ROW1_HEADER_INVENTORY_ONLY","source_manifest_sha256":sha(p),
   "archive_sha256":sha(archive),"workbooks":books,"design_rows_exported":0,"parent_pairs_admitted":0,
   "models_fit":0,"numerical_outcome_analysis":False,"whole_worksheet_XML_bytes_loaded_but_only_header_row_semantically_traversed":True}
 with (OUT/"header_inventory_receipt.json").open("xb") as f:f.write((json.dumps(result,sort_keys=True,indent=2)+"\n").encode())
 for book in books:
  print(book["bundle_member"],[(s["name"],[h["value"] for h in s["headers"]]) for s in book["sheets"]],flush=True)
if __name__=="__main__":run()
