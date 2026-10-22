"""Independent core/contact/pair construction; shared certified selective metadata reader."""
import math
from .common import ROOT,OUT,sha,read,save
from .audit import bind_manifest,load_wt
from src.generalization_prelib_native_reference_20261009.acquire import fresh as metadata_guard
from src.generalization_pum2_fixed_math_20261008.model import load_parameters
def independent_windows(sequence):
 fixed={0:"T",1:"G",2:"T",3:"A",5:"A",6:"T",7:"A"};sites=[];terminal=[]
 for i in range(max(0,len(sequence)-7)):
  if all(sequence[i+k]==base for k,base in fixed.items()):
   if i+9<=len(sequence):sites.append(i)
   else:terminal.append(i)
 return sites,terminal
def independent_pairs(starts):
 return [(a,b,b-a-9) for a in starts for b in starts if a<b and b-a>=9]
def verify_record(row,record,params):
 s=row["Sequence"];starts,terminal=independent_windows(s)
 assert record["source_parent_ID"]==row["ID"] and record["source_excel_row"]==row["source_excel_row"]
 assert [r["start_0based"] for r in record["sites"]]==starts
 assert [r["core_start_0based"] for r in record["terminal_ineligible_cores"]]==terminal
 energies={}
 for item in record["sites"]:
  i=item["start_0based"];x=s[i:i+9].replace("T","U")
  assert item["core_RNA"]==x[:8] and item["contact_RNA"]==x and item["core_end_0based_exclusive"]==i+8 and item["contact_end_0based_exclusive"]==i+9
  assert x[7]=="A","Canonical core implies both published coupling predicates are false"
  independent=math.fsum(params.base[(k,b)] for k,b in enumerate(x))
  assert abs(independent-item["fixed_consecutive_energy_kcal"])<1e-12
  energies[i]=item["fixed_consecutive_energy_kcal"]
 expected=independent_pairs(starts)
 assert [(p["left_start_0based"],p["right_start_0based"],p["intervening_bases"]) for p in record["all_nonoverlapping_pairs"]]==expected
 assert record["site_count"]==len(starts) and record["nonoverlapping_pair_count"]==len(expected)
 for p in record["all_nonoverlapping_pairs"]:
  a,b=p["left_start_0based"],p["right_start_0based"]
  assert p["left_contact_end_0based_exclusive"]==a+9 and p["right_contact_end_0based_exclusive"]==b+9 and p["core_gap_bases"]==b-a-8
  assert p["pair_energy_sum_kcal"]==math.fsum((energies[a],energies[b]))
 canonical=min(record["all_nonoverlapping_pairs"],key=lambda p:(p["pair_energy_sum_kcal"],p["left_start_0based"],p["right_start_0based"])) if expected else None
 assert record["selected_pair"]==canonical
def run():
 metadata_guard();path,m=bind_manifest();roster,n=load_wt();birth=read(OUT/"WT_geometry_birth_receipt.json")
 assert birth["design_manifest_sha256"]==sha(path)
 output=OUT/"WT_two_site_geometry.json";assert birth["files"]=={output.relative_to(ROOT).as_posix():sha(output)}
 x=read(output);assert x["design_manifest_sha256"]==sha(path) and x["rule"]==m["rule"] and x["semantic_sequence_rows_decoded"]==8
 records=x["WT_records"];assert len(records)==8 and len({r["prefix"] for r in records})==8
 byprefix={r["prefix"]:r for r in records};params=load_parameters()
 for parent,row in roster:
  r=byprefix[parent["prefix"]];assert r["nominal_lineage"]==parent["lineage"] and r["mPRE_background"] is False
  assert r["source_sequence_sha256"]==parent["parent_sequence_sha256"]==r["sequence_sha256"] and r["source_sequence_length"]==140
  verify_record(row,r,params)
 assert x["source_rows_lexically_skipped_except_WT"]==n-8 and x["WT_native_templates"]==8 and x["nominal_lineages"]==7
 assert x["WT_templates_with_qualifying_pair"]==sum(r["selected_pair"] is not None for r in records)
 assert x["nominal_lineages_with_qualifying_pair"]==len({r["nominal_lineage"] for r in records if r["selected_pair"] is not None})
 assert x["outcomes_read"] is False and x["models_fit"]==x["folds_run"]==0
 metadata_guard()
 save(OUT/"independent_geometry_replay.json",{"status":"PASS_WT_ONLY_INDEPENDENT_SITE_PAIR_GEOMETRY",
  "design_manifest_sha256":sha(path),"birth_receipt_sha256":sha(OUT/"WT_geometry_birth_receipt.json"),
  "geometry_sha256":sha(output),"WT_templates":8,"nominal_lineages":7,
  "independent_core_and_pairs":True,"independent_scalar_energy_bound":1e-12,
  "exact_pair_selection_uses_certified_canonical_saved_energy_to_preserve_float_ties":True,
  "selective_metadata_reader_shared_and_disclosed":True,"outcomes_read":False,"folds_run":0,"models_fit":0})
 print("WT_GEOMETRY_REPLAY_PASS",flush=True)
if __name__=="__main__":run()
