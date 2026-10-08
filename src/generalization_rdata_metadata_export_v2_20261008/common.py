from src.generalization_rdata_metadata_feasibility_20261008.loader import ROOT,load,read,sha
from pathlib import Path
import json,hashlib,sys,subprocess
NS="generalization_rdata_metadata_export_v2_20261008"
OUT=ROOT/"results"/NS
OLD_OUT=ROOT/"results/generalization_rdata_metadata_feasibility_20261008"
def certify():
    path=OUT/"metadata_parse_manifest.json"
    assert subprocess.check_output(["git","show","HEAD:"+path.relative_to(ROOT).as_posix()],cwd=ROOT)==path.read_bytes()
    value=read(path)
    assert value["status"]=="FROZEN_V2_METADATA_SUBTREE_EXPORT_WHOLE_FILE_PARSE"
    assert value["worker_RAM_cap_MiB"]==768 and value["worker_wall_time_seconds"]==180
    assert value["metadata_subtree_node_cap"]==500000 and value["metadata_subtree_edge_cap"]==1000000
    for name,digest in value["files"].items():assert sha(ROOT/name)==digest,name
    assert read(OUT/"pilot_receipt.json")["status"]=="PASS_V2_OFFICIAL_TINY_FIXTURES"
    return value
