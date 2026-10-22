"""Additive parser repair freeze; hash-only biological inputs, no WT decoding."""
from .common import ROOT,OUT,REP,read,sha,save
def run():
 p1=OUT/"design_manifest.json";p2=OUT/"design_manifest_v2.json";m1=read(p1);m2=read(p2)
 for m in (m1,m2):
  for rel,h in m["files"].items():assert sha(ROOT/rel)==h,rel
 t=OUT/"synthetic_tests_receipt_v3.json";r=read(t)
 assert r["status"]=="PASS_INVENTED_BOUNDED_JSON_V3" and r["biological_values_read"] is False
 assert r["original_design_manifest_sha256"]==sha(p1) and r["v2_design_manifest_sha256"]==sha(p2)
 for rel,h in r["source_files"].items():assert sha(ROOT/rel)==h,rel
 files=dict(m2["files"])
 added=[p2,t,REP/"parser_repair_v3.md",OUT/"audit_worker_v2.log",OUT/"audit_supervisor_receipt_v2.json"]+[ROOT/rel for rel in r["source_files"]]
 for p in added:files[p.relative_to(ROOT).as_posix()]=sha(p)
 p=OUT/"design_manifest_v3.json"
 save(p,{"status":"FROZEN_ADDITIVE_BOUNDED_JSON_PARSER_V3","files":files,
  "original_design_manifest_sha256":sha(p1),"v2_design_manifest_sha256":sha(p2),
  "scientific_rule_unchanged":True,"prior_failed_audit_and_logs_preserved":True,
  "WT_or_parameter_values_loaded_during_preparation":False,"models_fit":0,"folds_run":0,
  "future_entrypoint":"supervise_v3","separate_parser_completion_receipt_required":True})
 print("ADDITIVE_V3_DESIGN_ONLY",len(files),sha(p),flush=True)
if __name__=="__main__":run()
