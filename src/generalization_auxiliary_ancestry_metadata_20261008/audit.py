from pathlib import Path
import json,hashlib,subprocess,collections,re
from . import checks as c
ROOT=Path(__file__).resolve().parents[2];NS="generalization_auxiliary_ancestry_metadata_20261008";OUT=ROOT/"results"/NS
ANN=ROOT/"results/generalization_rdata_metadata_export_v2_20261008"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding="utf8"))
def save(p,value):
 with p.open("xb") as f:f.write((json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+"\n").encode())
def run():
 manifest=read(OUT/"metadata_manifest.json")
 assert manifest["status"]=="FROZEN_AUTHOR_RULE_ANCESTRY_AND_INFERRED_INSERT_AUDIT_ONLY"
 assert subprocess.check_output(["git","show","HEAD:"+(OUT/"metadata_manifest.json").relative_to(ROOT).as_posix()],cwd=ROOT)==(OUT/"metadata_manifest.json").read_bytes()
 for name,digest in manifest["files"].items():assert sha(ROOT/name)==digest,name
 recovered=read(ANN/"annotation_metadata_receipt.json")
 assert recovered["status"]=="PASS_AUTHOR_ANNOTATION_METADATA_ONLY_ANCESTRY_NOT_YET_ADMITTED"
 for name,digest in recovered["files"].items():assert sha(ROOT/name)==digest
 interiors=read(ROOT/"results/generalization_auxiliary_binding_metadata_20261008/inferred_tile_interiors.json")
 sequences={(r["pool"],r["source_named_tile"]):r["inferred_DNA_interior"] for r in interiors}
 allrows={pool:read(ANN/("git_"+name+"_raw_annotation_metadata.json"))["rows"] for pool,name in
          (("ms2_4x","ms2"),("wrap53mt","WRAP53"),("hTR","hTR"))}
 aliases=[]
 for pool,rows in allrows.items():
  names=[c.alias(pool,r["tileID"]) for r in rows]
  assert len(names)==len(set(names)) and set(names)=={r["source_named_tile"] for r in interiors if r["pool"]==pool}
  aliases.append({"pool":pool,"complete_ID_set_bijection":True,"rows":len(rows),
      "namespace_alias_explicitly_provided_by_author":pool=="wrap53mt",
      "literal_rule":"identity" if pool=="wrap53mt" else "fixed pool-specific namespace rewrite; numeric token unchanged",
      "nearest_sequence_matching":False})
 records=[];quartets=[];unparented=[]
 def seq(pool,row):return sequences[pool,c.alias(pool,row["tileID"])]
 def add(pool,parent,variant,rule,positions=None,ref_alt=None,complement=False):
  a=seq(pool,parent);b=seq(pool,variant);edits=c.diff(a,b);issue=None
  try:
   if positions is not None:edits=c.expected_check(a,b,positions,ref_alt,complement)
  except AssertionError as error:issue=str(error)
  record={"pool":pool,"author_parent_tileID":parent["tileID"],"author_variant_tileID":variant["tileID"],
      "author_rule":rule,"literal_design":variant,"author_ID_ancestry_unambiguous":True,
      "parent_inferred_insert_sha256":hashlib.sha256(a.encode()).hexdigest(),
      "variant_inferred_insert_sha256":hashlib.sha256(b.encode()).hexdigest(),
      "inferred_insert_lengths":[len(a),len(b)],"equal_length_substitution_count":None if edits is None else len(edits),
      "actual_changed_positions_1based":[] if edits is None else list(edits),
      "actual_ref_alt_pairs":[] if edits is None else list(edits.values()),
      "design_coordinates_sequence_consistent":None if positions is None else issue is None,
      "consistency_issue":issue,"within_1_to_6_substitutions":edits is not None and 1<=len(edits)<=6,
      "one_RNA_lineage_for_splits":"hTR" if pool=="hTR" else pool,
      "source_certified_mature_RNA":False,"training_pair_admitted":False,"count_values_analyzed":False}
  records.append(record)
 rows=allrows["ms2_4x"];parent=c.single(rows,"group","WT")
 for row in rows:
  if row["group"]=="Single":
   match=re.fullmatch(r"([ACGT])to([ACGT])",row["mutType"]);assert match
   loc=int(row["mutLoc"]);assert 1<=loc<=19 and match[1]!=match[2]
   positions={offset+loc for offset in (14,47,87,132)}
   add("ms2_4x",parent,row,"nar_manuscript.Rmd:146-154; unique group WT",positions,(match[1],match[2]))
  elif row["group"]!="WT":unparented.append({"pool":"ms2_4x","tileID":row["tileID"],"reason":"Control or Stem: not included in the frozen Single parent rule"})
 rows=allrows["wrap53mt"];parent=c.single(rows,"type","wt")
 lookup=collections.defaultdict(list)
 for row in rows:
  lookup[row["idx"]].append(row)
  if row["mutation"] in ("complement","5p","3p","compensatory"):
   add("wrap53mt",parent,row,"nar_manuscript.Rmd:546-559/602-604; unique type wt",c.index_set(row["idx"]),complement=True)
  elif row["type"]!="wt":unparented.append({"pool":"wrap53mt","tileID":row["tileID"],"reason":"Control, not a designed mutant parent relation"})
 for row in rows:
  if row["mutation"]=="compensatory":
   parts=row["idx"].split(",");assert len(parts)==2
   arms=[single for part in parts for single in lookup[part] if single["mutation"] in ("5p","3p")]
   assert len(arms)==2 and {r["mutation"] for r in arms}=={"5p","3p"}
   arm5=next(r for r in arms if r["mutation"]=="5p");arm3=next(r for r in arms if r["mutation"]=="3p")
   try:passed=c.quartet_union(seq("wrap53mt",parent),seq("wrap53mt",arm5),seq("wrap53mt",arm3),seq("wrap53mt",row));issue=None
   except AssertionError as error:passed=False;issue=str(error)
   quartets.append({"pool":"wrap53mt","parent":parent["tileID"],"arm5":arm5["tileID"],"arm3":arm3["tileID"],
       "comp":row["tileID"],"exact_disjoint_edit_union":passed,"issue":issue,"observed_folding_or_binding_rescue":False})
 rows=allrows["hTR"];controls=[r for r in rows if r["type"]=="Control"]
 parents={r["coord"]:c.single(controls,"coord",r["coord"]) for r in controls};groups=collections.defaultdict(dict)
 for row in rows:
  if row["type"] in ("Mut1bp","Mut4bp"):
   parent=parents[row["coord"]];start,end=c.coord(row["coord"])
   assert len(seq("hTR",parent))==end-start+1
   width=1 if row["type"]=="Mut1bp" else 4
   left=int(row["bpLoc5prime"]);right=int(row["bpLoc3prime"])
   p5=set(range(left-start+1,left-start+1+width))
   p3=set(range(right-start+2-width,right-start+2))
   assert p5|p3<=set(range(1,end-start+2))
   positions=p5 if row["mutation"]=="5 prime" else p3 if row["mutation"]=="3 prime" else p5|p3
   assert row["mutation"] in ("5 prime","3 prime","complementary")
   add("hTR",parent,row,"nar_manuscript.Rmd:339-345; exact coord Control lookup",positions,complement=True)
   key=tuple(row[name] for name in ("coord","region","bpLoc5prime","bpLoc3prime","type"))
   assert row["mutation"] not in groups[key],"Duplicate quartet arm"
   groups[key][row["mutation"]]=row
  elif row["coord"] in ("hTR:34-190","hTR:210-366") and row["mutation"] in ("Deletion","Replace"):
   add("hTR",parents[row["coord"]],row,"nar_manuscript.Rmd:287-292; exact coord Control lookup")
  elif row["type"]!="Control":unparented.append({"pool":"hTR","tileID":row["tileID"],"reason":"Random or outside explicit parent rule"})
 for key,group in groups.items():
  assert set(group)=={"5 prime","3 prime","complementary"},"Incomplete author stem quartet"
  parent=parents[key[0]];arm5=group["5 prime"];arm3=group["3 prime"];comp=group["complementary"]
  try:passed=c.quartet_union(seq("hTR",parent),seq("hTR",arm5),seq("hTR",arm3),seq("hTR",comp));issue=None
  except AssertionError as error:passed=False;issue=str(error)
  quartets.append({"pool":"hTR","group_key":list(key),"parent":parent["tileID"],"arm5":arm5["tileID"],"arm3":arm3["tileID"],
      "comp":comp["tileID"],"exact_disjoint_edit_union":passed,"issue":issue,"observed_folding_or_binding_rescue":False})
 save(OUT/"author_design_relations.json",records);save(OUT/"compensatory_sequence_quartets.json",quartets);save(OUT/"unparented_annotation_rows.json",unparented)
 summaries=[]
 for pool in allrows:
  rr=[r for r in records if r["pool"]==pool]
  summaries.append({"pool":pool,"author_ID_relations":len(rr),"unique_parent_IDs":len({r["author_parent_tileID"] for r in rr}),
   "equal_length_edit_histogram":dict(collections.Counter(str(r["equal_length_substitution_count"]) for r in rr)),
   "coordinate_sequence_checked":sum(r["design_coordinates_sequence_consistent"] is not None for r in rr),
   "coordinate_sequence_failures":sum(r["design_coordinates_sequence_consistent"] is False for r in rr),
   "inferred_insert_1_to_6_substitutions":sum(r["within_1_to_6_substitutions"] for r in rr)})
 result={"status":"COMPLETE_OUTCOME_FREE_AUTHOR_ANCESTRY_AND_INFERRED_INSERT_AUDIT","pools":summaries,"ID_aliases":aliases,
    "source_manifest_sha256":sha(OUT/"metadata_manifest.json"),"compensatory_quartets":len(quartets),
    "quartet_union_failures":sum(not r["exact_disjoint_edit_union"] for r in quartets),
    "three_RNA_lineages_not_independent_parent_ID_count":True,"hTR_overlapping_fragments_same_split_lineage":True,
    "mature_RNA_or_primer_boundary_source_certificate":False,"training_pairs_admitted":0,"models_fit":0,"count_values_analyzed":False,
    "metadata_completion_is_not_biological_or_training_admission":True,
    "files":{p.relative_to(ROOT).as_posix():sha(p) for p in (OUT/"author_design_relations.json",OUT/"compensatory_sequence_quartets.json",OUT/"unparented_annotation_rows.json")}}
 save(OUT/"ancestry_audit_receipt.json",result)
 print(json.dumps({"status":result["status"],"pools":summaries,"quartets":len(quartets),"quartet_union_failures":result["quartet_union_failures"]},sort_keys=True),flush=True)
if __name__=="__main__":run()
