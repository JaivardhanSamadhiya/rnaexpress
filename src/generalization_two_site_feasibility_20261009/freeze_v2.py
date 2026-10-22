"""Additive v2 source-bound final resource checks; no sequence reading."""
from .common import ROOT,OUT,REP,sha,read,save
def run():
 old=OUT/"design_manifest.json";v1=read(old)
 for rel,h in v1["files"].items():assert sha(ROOT/rel)==h,rel
 t=OUT/"synthetic_tests_receipt_v2.json";receipt=read(t)
 assert receipt["status"]=="PASS_SYNTHETIC_ONLY_V2_FINAL_CAPS" and receipt["sequence_values_read"] is False
 assert receipt["original_design_manifest_sha256"]==sha(old)
 assert receipt["original_synthetic_receipt_sha256"]==sha(OUT/"synthetic_tests_receipt.json")
 for rel,h in receipt["source_files"].items():assert sha(ROOT/rel)==h,rel
 files=dict(v1["files"])
 paths=[old,t,REP/"readiness_v2.md"]+[ROOT/r for r in receipt["source_files"]]
 for p in paths:files[p.relative_to(ROOT).as_posix()]=sha(p)
 p=OUT/"design_manifest_v2.json"
 save(p,{"status":"FROZEN_ADDITIVE_FINAL_RESOURCE_CAP_CHECK","original_design_manifest_sha256":sha(old),
  "scientific_rule_unchanged":True,"files":files,"source_peer_requested_fix":"Final30s check after completed child; final lifetime peak query fails closed",
  "WT_sequences_inspected_before_v2_manifest":False,"outcomes_read":False,"models_fit":0,
  "original_v1_preserved":True,"future_supervised_audit_and_replay_entrypoint":"supervise_v2"})
 print("ADDITIVE_V2_DESIGN_ONLY",len(files),sha(p),flush=True)
if __name__=="__main__":run()
