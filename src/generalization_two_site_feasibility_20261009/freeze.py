"""Sequence-free immutable design admission; creates manifest before WT scan."""
from .common import ROOT,OUT,REP,sha,read,save
from .design import RULE,SOURCES
INPUTS=[
 "results/generalization_prelib_design_metadata_20261008/design_metadata_receipt_v2.json",
 "results/generalization_prelib_design_metadata_20261008/design_metadata_manifest_v2.json",
 "results/generalization_prelib_design_metadata_20261008/TableS4_PRELibB_metadata_v2.json",
 "results/generalization_prelib_point_ancestry_20261008/point_metadata_receipt_v2.json",
 "results/generalization_prelib_point_ancestry_20261008/metadata_manifest_v2.json",
 "results/generalization_prelib_point_ancestry_20261008/parent_template_metadata_v2.json",
 "results/generalization_pum2_parameter_metadata_20261008/acquisition_receipt_v2.json",
 "src/generalization_pum2_fixed_math_20261008/model.py",
 "src/generalization_pum2_fixed_math_20261008/produce_features.py",
 "src/generalization_prelib_native_reference_20261009/acquire.py",
 "reports/generalization_prelib_native_reference_20261009/protocol.md",
 "reports/generalization_pum2_fixed_math_20261008/protocol.md",
 "reports/generalization_pum2_fixed_math_20261008/feature_protocol.md",
 "reports/generalization_prelib_design_metadata_20261008/protocol.md",
 "reports/generalization_prelib_design_metadata_20261008/protocol_v2.md",
 "reports/generalization_prelib_point_ancestry_20261008/protocol_v2.md",
 "reports/generalization_joint_accessibility_20261007/protocol.md",
 "src/generalization_joint_accessibility_20261007/scoring.py",
]+["data/raw/generalization_pum2_parameter_metadata_20261008/"+name for name in (
 "PUM2_qMotif_term1.csv","PUM2_qMotif_term2_single.csv","PUM2_qMotif_term2_double.csv","PUM2_qMotif_term3.csv")]
def run():
 src=ROOT/"src"/OUT.name
 own=sorted(src.glob("*.py"))+[src/".gitattributes",REP/"protocol.md",REP/".gitattributes",OUT/".gitattributes",OUT/"synthetic_tests_receipt.json"]
 receipt=read(OUT/"synthetic_tests_receipt.json")
 assert receipt["status"]=="PASS_SYNTHETIC_ONLY" and receipt["sequence_values_read"] is False
 for rel,digest in receipt["source_files"].items():assert sha(ROOT/rel)==digest
 assert set(receipt["source_files"])=={p.relative_to(ROOT).as_posix() for p in src.glob("*.py")}
 files={p.relative_to(ROOT).as_posix():sha(p) for p in own+[ROOT/r for r in INPUTS]}
 path=OUT/"design_manifest.json"
 save(path,{"status":"FROZEN_OUTCOME_BLIND_TWO_SITE_WT_GEOMETRY_DESIGN","rule":RULE,"primary_sources":SOURCES,
  "files":files,"WT_sequences_inspected_before_manifest":False,"outcomes_read":False,"models_fit":0,
  "future_audit_requires_manifest_committed_to_HEAD":True,"no_existing_artifact_changed":True})
 print("DESIGN_ONLY",len(files),sha(path),flush=True)
if __name__=="__main__":run()
