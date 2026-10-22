"""Exactly8 WT metadata rows; existing metadata1.3GiB admission; no scientific runtime."""
import hashlib,json,subprocess,sys,time
from .common import ROOT,OUT,DESIGN,PARENTS,ANCESTRY,PARAMETER,MAX_INPUT_BYTES,sha,read,save
from .design import RULE
from .geometry import audit_sequence
from .selective_metadata import selected_rows
from src.generalization_prelib_native_reference_20261009.acquire import fresh as metadata_guard
from src.generalization_pum2_fixed_math_20261008.model import load_parameters,bound_energy
EXPECTED=frozenset(("Context_NORAD_PRE4_rep3_5","Context_NORAD_PRE9_rep7_5","Hafner_HIAT1",
 "Hafner_MGEA5","Hafner_PGBD4","Hafner_APIS1","ENCODE_Pum1_SMARCA2","ENCODE_Pum1_IRF2BP1"))
def bind_manifest(require_head=True):
 path=OUT/"design_manifest.json";m=read(path);assert m["rule"]==RULE
 if require_head:
  assert subprocess.check_output(["git","show","HEAD:"+path.relative_to(ROOT).as_posix()],cwd=ROOT)==path.read_bytes()
 for rel,digest in m["files"].items():assert sha(ROOT/rel)==digest,rel
 return path,m
def load_wt():
 a=read(ANCESTRY);assert a["status"]=="COMPLETE_LITERAL_ZERO_BASED_POINT_EDIT_RECONSTRUCTION_NOT_TRAINING_ADMISSION"
 assert a["binding_outcomes_analyzed"] is False and a["coordinate_or_sequence_flags"]==0
 assert a["files"][PARENTS.relative_to(ROOT).as_posix()]==sha(PARENTS)
 d=read(ROOT/"results/generalization_prelib_design_metadata_20261008/design_metadata_receipt_v2.json")
 assert d["status"]=="PASS_PRELIB_FIXED_DESIGN_FIELDS_V2_UNEVALUATED_FORMULA_TOTAL"
 assert d["files"][DESIGN.relative_to(ROOT).as_posix()]==sha(DESIGN)
 parents=read(PARENTS);assert len(parents)==16 and all(type(p["mPRE_background"]) is bool for p in parents)
 parents=[p for p in parents if not p["mPRE_background"]]
 assert len(parents)==8 and {p["prefix"] for p in parents}==EXPECTED
 assert len({p["source_excel_row"] for p in parents})==8 and len({p["source_parent_ID"] for p in parents})==8
 assert len({p["lineage"] for p in parents})==7
 assert DESIGN.stat().st_size<=MAX_INPUT_BYTES
 rows,n=selected_rows(DESIGN.read_text(encoding="utf-8"),{p["source_excel_row"] for p in parents})
 assert n==6293
 result=[]
 for parent in parents:
  row=rows[parent["source_excel_row"]];s=row["Sequence"]
  assert row["ID"]==parent["source_parent_ID"] and len(s)==140 and set(s)<=set("ACGT")
  assert hashlib.sha256(s.encode()).hexdigest()==parent["parent_sequence_sha256"]
  result.append((parent,row))
 return result,n
def run():
 available=metadata_guard();path,m=bind_manifest();start=time.monotonic();roster,n=load_wt();params=load_parameters()
 records=[]
 for parent,row in roster:
  record={"prefix":parent["prefix"],"source_parent_ID":parent["source_parent_ID"],
   "source_excel_row":parent["source_excel_row"],"nominal_lineage":parent["lineage"],
   "mPRE_background":False,"source_sequence_length":140,"source_sequence_sha256":parent["parent_sequence_sha256"],
   **audit_sequence(row["Sequence"],lambda x:bound_energy(x,params,(True,True)))}
  records.append(record)
 metadata_guard()
 output=OUT/"WT_two_site_geometry.json"
 save(output,{"status":"COMPLETE_WT_ONLY_GEOMETRY_NOT_FOLDING_OR_BINDING_OR_LOCALIZATION",
  "design_manifest_sha256":sha(path),"rule":RULE,"WT_records":records,
  "source_rows_lexically_skipped_except_WT":n-len(roster),"semantic_sequence_rows_decoded":len(roster),
  "WT_native_templates":8,"nominal_lineages":7,"source_resource":"PRELibB nativeWT-only",
  "site_counts":[{"prefix":r["prefix"],"sites":r["site_count"],"pairs":r["nonoverlapping_pair_count"]} for r in records],
  "WT_templates_with_qualifying_pair":sum(r["selected_pair"] is not None for r in records),
  "nominal_lineages_with_qualifying_pair":len({r["nominal_lineage"] for r in records if r["selected_pair"] is not None}),
  "all_zero_and_sparse_templates_retained":True,"mutant_or_mPRE_sequence_scan":False,
  "outcomes_read":False,"scientific_runtime_loaded":False,"folds_run":0,"models_fit":0,
  "available_RAM_before_bytes":available,"elapsed_seconds":time.monotonic()-start})
 save(OUT/"WT_geometry_birth_receipt.json",{"status":"IMMUTABLE_FIRST_CREATION_GEOMETRY_RECEIPT",
  "design_manifest_sha256":sha(path),"files":{output.relative_to(ROOT).as_posix():sha(output)},
  "independent_replay_pending":True,"outcomes_read":False,"models_fit":0})
 print("WT_GEOMETRY_ONLY",len(records),"paired WT",sum(r["selected_pair"] is not None for r in records),flush=True)
if __name__=="__main__":run()
