"""Scoped source-preserving parser repair; original geometry/scientific rules unchanged."""
from contextlib import contextmanager
import subprocess,sys
from .common import ROOT,OUT,read,sha,save
from . import audit,replay
from .selective_metadata_v3 import selected_rows
from .supervise_v2 import bind_v2
from src.generalization_prelib_native_reference_20261009.acquire import fresh as metadata_guard
def bind_v3():
 p=OUT/"design_manifest_v3.json";m=read(p)
 assert m["status"]=="FROZEN_ADDITIVE_BOUNDED_JSON_PARSER_V3"
 assert subprocess.check_output(["git","show","HEAD:"+p.relative_to(ROOT).as_posix()],cwd=ROOT)==p.read_bytes()
 for rel,h in m["files"].items():assert sha(ROOT/rel)==h,rel
 prior,original=bind_v2()
 assert m["v2_design_manifest_sha256"]==sha(prior)
 assert m["original_design_manifest_sha256"]==sha(original)
 return p,prior,original
@contextmanager
def parser_binding():
 original=audit.selected_rows;audit.selected_rows=selected_rows
 try:yield
 finally:audit.selected_rows=original
def execute_stage(stage):
 assert stage in ("audit","replay")
 with parser_binding():
  (audit.run if stage=="audit" else replay.run)()
def run(stage):
 assert stage in ("audit","replay");metadata_guard();p,prior,original=bind_v3()
 before=audit.selected_rows
 try:execute_stage(stage)
 except Exception as error:
  assert audit.selected_rows is before
  save(OUT/(stage+"_parser_failure_v3.json"),{"status":"PRESERVED_V3_WORKER_FAILURE","error_class":type(error).__name__,
   "message":str(error),"v3_design_manifest_sha256":sha(p),"parser_binding_restored":True})
  raise
 assert audit.selected_rows is before
 names=("WT_two_site_geometry.json","WT_geometry_birth_receipt.json") if stage=="audit" else ("independent_geometry_replay.json","WT_geometry_birth_receipt.json","WT_two_site_geometry.json")
 save(OUT/(stage+"_parser_compatibility_receipt_v3.json"),{"status":"PASS_ADDITIVE_V3_PARSER_STAGE_COMPLETION","stage":stage,
  "v3_design_manifest_sha256":sha(p),"v2_design_manifest_sha256":sha(prior),"original_design_manifest_sha256":sha(original),
  "parser_binding_restored":True,"original_scientific_rule_and_stage_sources_unchanged":True,
  "new_parser_source_sha256":sha(ROOT/"src"/OUT.name/"selective_metadata_v3.py"),
  "files":{("results/"+OUT.name+"/"+name):sha(OUT/name) for name in names},
  "downstream_requires_this_additive_receipt_not_original_birth_alone":True,"models_fit":0,"folds_run":0})
 print("V3_PARSER_STAGE",stage,"PASS",flush=True)
if __name__=="__main__":run(sys.argv[1])
