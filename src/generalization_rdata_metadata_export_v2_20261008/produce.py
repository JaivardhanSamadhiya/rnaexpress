from .common import *
from . import metadata as m
from src.generalization_rdata_metadata_feasibility_20261008 import decode as d
import zipfile,gzip,io,gc,time
def run(root_start=False):
    assert root_start;manifest=certify();assert not (OUT/"annotation_metadata_receipt.json").exists()
    parser,np,proof=load();archive=ROOT/manifest["author_archive_path"]
    symbols=read(ROOT/"results/generalization_auxiliary_binding_metadata_20261008/raw_annotation_symbol_presence_01.json")
    assert sha(archive)==symbols["zip_sha256"]
    expected={r["zip_member"]:r for r in symbols["records"]};records=[];files={}
    with zipfile.ZipFile(archive) as z:
        assert len(expected)==5
        for member in sorted(expected):
            start=time.monotonic();raw=z.read(member);before=expected[member]
            assert hashlib.sha256(raw).hexdigest()==before["stored_member_sha256"]
            with gzip.GzipFile(fileobj=io.BytesIO(raw)) as g:payload=g.read(64*1024**2+1)
            assert len(payload)==before["decompressed_bytes"]<=64*1024**2
            assert hashlib.sha256(payload).hexdigest()==before["decompressed_sha256"]
            parsed=parser.parse_data(payload,expand_altrep=False,altrep_constructor_dict={},extension=".rdata")
            globals_,annotation=m.select_annotation(parsed.object)
            result=m.export(annotation)
            result["source_zip_member"]=member
            output=OUT/(Path(member).stem+"_annotation_metadata.json")
            with output.open("xb") as f:f.write((json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n").encode())
            files[output.relative_to(ROOT).as_posix()]=sha(output)
            records.append({"source_zip_member":member,"annotation_rows":len(result["rows"]),
                "exported_columns":result["exported_allowlist_columns"],"all_annotation_column_names":result["all_annotation_column_names"],
                "annotation_RObject_nodes":result["annotation_RObject_nodes"],"whole_global_RObject_node_count_measured":False,
                "global_structural_names_and_types":[{"name":name,"type":d.kind(obj)} for name,obj in globals_.items()],
                "whole_count_arrays_internally_materialized":True,"count_analysis_or_export":False,"ancestry_admitted":False,
                "elapsed_seconds":time.monotonic()-start})
            print(Path(member).name,"annotation rows",len(result["rows"]),"metadata nodes",result["annotation_RObject_nodes"],"no ancestry admitted",flush=True)
            del parsed,globals_,annotation,raw,payload,result;gc.collect()
    assert len(records)==5;certify()
    result={"status":"PASS_AUTHOR_ANNOTATION_METADATA_ONLY_ANCESTRY_NOT_YET_ADMITTED","records":records,"files":files,
        "metadata_parse_manifest_sha256":sha(OUT/"metadata_parse_manifest.json"),"runtime":proof,
        "count_arrays_internally_parsed":True,"count_values_analyzed_or_exported":False,"R_expressions_evaluated":False,
        "stock_class_conversion":False,"parent_pair_admission":False,"models_fit":0,"new_localization_outcomes_read":False,
        "whole_global_RObject_node_count_measured":False,"original_failed_parser_preserved":True}
    with (OUT/"annotation_metadata_receipt.json").open("xb") as f:f.write((json.dumps(result,sort_keys=True,indent=2)+"\n").encode())
if __name__=="__main__":run("--root-start" in sys.argv[1:])
