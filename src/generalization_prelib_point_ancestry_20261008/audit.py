from pathlib import Path
import json,hashlib,collections,re,subprocess
ROOT=Path(__file__).resolve().parents[2];NS="generalization_prelib_point_ancestry_20261008";OUT=ROOT/"results"/NS
TEMPLATES={"Context_NORAD_PRE4_rep3_5":"NORAD","Context_NORAD_PRE9_rep7_5":"NORAD",
 "Hafner_HIAT1":"HIAT1","Hafner_MGEA5":"MGEA5","Hafner_PGBD4":"PGBD4","Hafner_APIS1":"AP1S1",
 "ENCODE_Pum1_SMARCA2":"SMARCA2","ENCODE_Pum1_IRF2BP1":"IRF2BP1"}
KINDS=frozenset(("Mut","4mer","6mer","10mer","ReplaceMer"))
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def parent_for(rows,prefix):
 candidates=[r for r in rows if r["ID"].split(":")[0]==prefix and r["ID"].split(":")[1] not in KINDS]
 assert len(candidates)==1,"Ambiguous or absent baseline within literal author ID hierarchy"
 return candidates[0]
def check(parent,variant,prefix):
 match=re.fullmatch(re.escape(prefix)+r":Mut:(\d+):([ACGT])->([ACGT])",variant["ID"]);assert match
 pos=int(match[1]);ref=match[2];alt=match[3];a=parent["Sequence"];b=variant["Sequence"]
 assert len(a)==len(b)==140 and set(a+b)<=set("ACGT")
 assert 1<=pos<=140 and ref!=alt and a[pos-1]==ref and b[pos-1]==alt
 changed=[i+1 for i,(x,y) in enumerate(zip(a,b)) if x!=y]
 assert changed==[pos],"Literal point-edit design is not exactly one physical substitution"
 return pos,ref,alt
def save(p,x):
 with p.open("xb") as f:f.write((json.dumps(x,sort_keys=True,indent=2)+"\n").encode())
def run():
 p=OUT/"metadata_manifest.json";manifest=read(p)
 assert subprocess.check_output(["git","show","HEAD:"+p.relative_to(ROOT).as_posix()],cwd=ROOT)==p.read_bytes()
 for name,digest in manifest["files"].items():assert sha(ROOT/name)==digest,name
 design=ROOT/"results/generalization_prelib_design_metadata_20261008"
 rows=read(design/"TableS4_PRELibB_metadata_v2.json")["rows"]
 a=read(design/"TableS2_PRELibA_metadata_v2.json")["rows"];s3=read(design/"TableS3_PRELibB_design_metadata_v2.json")["rows"]
 ids=collections.defaultdict(list)
 for row in rows:ids[row["ID"]].append(row)
 collisions=[{"source_ID":name,"excel_rows":[r["source_excel_row"] for r in group],
   "different_sequence_count":len({r["Sequence"] for r in group})} for name,group in ids.items() if len(group)>1]
 records=[];parents=[];unresolved=[]
 for template,gene in TEMPLATES.items():
  for mutant_pre in (False,True):
   prefix=("m"+template if mutant_pre and not template.startswith("Context_") else template.replace("Context_","Context_m",1) if mutant_pre else template)
   parent=parent_for(rows,prefix)
   sourceA=[r["ID"] for r in a if r["Sequence"]==parent["Sequence"]]
   source3=[{"Name":r["Name"],"excel_row":r["source_excel_row"],"design_oligos":r["Number of oligos"]} for r in s3 if r["Baseline sequence"]==parent["Sequence"]]
   parents.append({"prefix":prefix,"lineage":gene,"genomic_gene_identity_independently_certified":False,"mPRE_background":mutant_pre,
      "source_parent_ID":parent["ID"],"source_excel_row":parent["source_excel_row"],"sourceA_exact_sequence_IDs":sourceA,
      "sourceS3_exact_sequence_design_rows":source3,"parent_sequence_sha256":hashlib.sha256(parent["Sequence"].encode()).hexdigest(),
      "author_explicit_parent_pointer_present":False,"source_ID_hierarchy_reconstructed_not_nearest_sequence":True})
   assert len(ids[parent["ID"]])==1,"Colliding source parent ID"
   for row in rows:
    if row["ID"].split(":")[0]!=prefix or row["ID"].split(":")[1]!="Mut":continue
    assert len(ids[row["ID"]])==1,"Colliding point-edit source ID"
    try:
     pos,ref,alt=check(parent,row,prefix);issue=None
    except AssertionError as error:pos=ref=alt=None;issue=str(error) or "Point-edit metadata contract mismatch"
    record={"source_parent_ID":parent["ID"],"source_variant_ID":row["ID"],"source_variant_excel_row":row["source_excel_row"],
      "parent_excel_row":parent["source_excel_row"],"prefix":prefix,"lineage":gene,"template_family":template,
      "mPRE_background":mutant_pre,"coordinate_1based":pos,"ref":ref,"alt":alt,"literal_one_substitution_checked":issue is None,
      "issue":issue,"variant_sequence_sha256":hashlib.sha256(row["Sequence"].encode()).hexdigest(),
      "source_ID_hierarchy_reconstructed_not_explicit_author_pointer":True,"author_mature_RNA_boundaries_certified":False,
      "training_pair_admitted":False,"numerical_outcomes_analyzed":False}
    records.append(record)
    if issue:unresolved.append(record["source_variant_ID"])
 save(OUT/"reconstructed_point_design_relations.json",records);save(OUT/"parent_template_metadata.json",parents);save(OUT/"all_source_ID_collisions.json",collisions)
 summary={"status":"COMPLETE_LITERAL_POINT_EDIT_HIERARCHY_RECONSTRUCTION_NOT_TRAINING_ADMISSION","source_manifest_sha256":sha(p),
   "sourceB_rows":len(rows),"sourceB_unique_IDs":len(ids),"ID_collision_groups":len(collisions),
   "collision_groups_differing_sequences":sum(r["different_sequence_count"]>1 for r in collisions),
   "point_design_relations":len(records),"literal_one_substitution_pass":sum(r["literal_one_substitution_checked"] for r in records),
   "coordinate_or_sequence_flags":len(unresolved),"source_template_backgrounds":len(parents),"named_parent_lineages":len({r["lineage"] for r in parents}),
   "hTR_or_other_independent_confirmation_claim":False,"source_mature_RNA_boundaries_certified":False,"source_gene_names_not_independent_genomic_mapping":True,
   "parent_mutant_pointer_reconstructed_from_literal_hierarchy":True,"training_pairs_admitted":0,"models_fit":0,"binding_outcomes_analyzed":False,
   "files":{q.relative_to(ROOT).as_posix():sha(q) for q in (OUT/"reconstructed_point_design_relations.json",OUT/"parent_template_metadata.json",OUT/"all_source_ID_collisions.json")}}
 save(OUT/"point_metadata_receipt.json",summary);print(json.dumps(summary,sort_keys=True),flush=True)
if __name__=="__main__":run()
