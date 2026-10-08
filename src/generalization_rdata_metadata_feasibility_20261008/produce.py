
"""Bounded whole-RObject parsing; export only fixed annotation metadata columns."""
from .loader import *
from . import decode
import zipfile,gzip,io,gc,time,subprocess
ALLOW=("tileID","group","mutType","mutLoc","type","mutation","idx","coord")
def certify():
    path=OUT/"metadata_parse_manifest.json"
    assert subprocess.check_output(["git","show","HEAD:"+path.relative_to(ROOT).as_posix()],cwd=ROOT)==path.read_bytes()
    value=read(path);assert value["status"]=="FROZEN_AUXILIARY_ANNOTATION_METADATA_PARSE_ONLY"
    for name,digest in value["files"].items():assert sha(ROOT/name)==digest,name
    assert read(OUT/"pilot_receipt_v2.json")["status"]=="PASS_CUSTOM_PARSER_OFFICIAL_TINY_FIXTURES"
    return value
def object_count(obj):
    stack=[obj];seen=set()
    while stack:
        current=stack.pop()
        if current is None or not hasattr(current,"info") or id(current) in seen:continue
        seen.add(id(current));assert len(seen)<=500000,"RObject node cap exceeded"
        stack.extend((current.attributes,current.tag,current.referenced_object))
        if hasattr(current.value,"info"):stack.append(current.value)
        elif isinstance(current.value,(tuple,list)):stack.extend(value for value in current.value if hasattr(value,"info"))
    return len(seen)
def run(root_start=False):
    assert root_start;manifest=certify();assert not (OUT/"annotation_metadata_receipt.json").exists()
    parser,np,proof=load();archive=ROOT/manifest["author_archive_path"]
    symbols=read(ROOT/"results/generalization_auxiliary_binding_metadata_20261008/raw_annotation_symbol_presence_01.json")
    assert sha(archive)==symbols["zip_sha256"]
    expected={r["zip_member"]:r for r in symbols["records"]};records=[];files={};all_status=True
    with zipfile.ZipFile(archive) as z:
        assert len(expected)==5
        for member in sorted(expected):
            start=time.monotonic();raw=z.read(member);before=expected[member]
            assert hashlib.sha256(raw).hexdigest()==before["stored_member_sha256"]
            payload=gzip.GzipFile(fileobj=io.BytesIO(raw)).read(64*1024**2+1)
            assert len(payload)==before["decompressed_bytes"]<=64*1024**2
            assert hashlib.sha256(payload).hexdigest()==before["decompressed_sha256"]
            parsed=parser.parse_data(payload,expand_altrep=False,altrep_constructor_dict={},extension=".rdata")
            nodes=object_count(parsed.object);global_objects=decode.pairs(parsed.object)
            structural=[{"name":name,"type":decode.kind(obj)} for name,obj in global_objects.items()]
            assert "tile.annot" in global_objects,"STOP_METADATA_MISSING"
            columns=decode.columns(global_objects["tile.annot"]);assert "tileID" in columns
            rows={};column_metadata={}
            for name in ALLOW:
                if name in columns:
                    values,meta=decode.column(columns[name],allow_number=name in ("mutLoc","idx"))
                    rows[name]=values;column_metadata[name]=meta
            length=len(rows["tileID"]);assert 0<length<=5000 and len(set(rows["tileID"]))==length
            assert all(identifier is not None for identifier in rows["tileID"])
            assert all(len(values)==length for values in rows.values())
            values=[{name:column[i] for name,column in rows.items()} for i in range(length)]
            output=OUT/(Path(member).stem+"_annotation_metadata.json")
            with output.open("xb") as f:f.write((json.dumps({"source_zip_member":member,"column_metadata":column_metadata,
                "all_annotation_column_names":list(columns),"exported_allowlist_columns":list(rows),"rows":values,
                "parent_mutant_ancestry_admitted":False},sort_keys=True,indent=2,allow_nan=False)+"\n").encode())
            files[output.relative_to(ROOT).as_posix()]=sha(output)
            records.append({"source_zip_member":member,"annotation_rows":length,"all_annotation_column_names":list(columns),
                "exported_columns":list(rows),"global_structural_names_and_types":structural,"RObject_nodes":nodes,
                "whole_RData_count_arrays_internally_materialized":True,"scientific_count_analysis":False,
                "parent_mutant_ancestry_admitted":False,"elapsed_seconds":time.monotonic()-start})
            print(Path(member).name,"annotation rows",length,"columns",",".join(rows),"no ancestry admitted",flush=True)
            del parsed,global_objects,columns,raw,payload;gc.collect()
    assert len(records)==5;certify()
    result={"status":"PASS_AUTHOR_ANNOTATION_METADATA_ONLY_ANCESTRY_NOT_YET_ADMITTED",
        "metadata_parse_manifest_sha256":sha(OUT/"metadata_parse_manifest.json"),"records":records,"files":files,"runtime":proof,
        "whole_RObjects_and_numeric_count_arrays_internally_parsed":True,"annotation_only_byte_parsing":False,
        "count_value_scientific_analysis_or_export":False,"stock_class_conversion_executed":False,
        "R_expressions_evaluated":False,"parent_mutant_pair_admission":False,"models_fit":0,
        "new_localization_outcomes_read":False,"independent_R_runtime_comparison":False}
    with (OUT/"annotation_metadata_receipt.json").open("xb") as f:f.write((json.dumps(result,sort_keys=True,indent=2)+"\n").encode())
if __name__=="__main__":run("--root-start" in sys.argv[1:])
