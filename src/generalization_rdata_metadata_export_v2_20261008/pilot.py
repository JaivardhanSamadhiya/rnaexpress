from .common import *
from . import metadata as m
from src.generalization_rdata_metadata_feasibility_20261008 import decode as d
import zipfile
def run():
    parser,np,proof=load()
    wheel=ROOT/"data/raw/generalization_rdata_metadata_feasibility_20261008/rdata-1.1.0-py3-none-any.whl"
    assert sha(wheel)==read(OLD_OUT/"wheel_source_receipt.json")["wheel_sha256"]
    fixtures={}
    with zipfile.ZipFile(wheel) as z:
        for name in ("test_vector","test_dataframe"):
            body=z.read("rdata/tests/data/"+name+".rda")
            parsed=parser.parse_data(body,expand_altrep=False,altrep_constructor_dict={},extension=".rda")
            bindings=d.pairs(parsed.object);assert set(bindings)=={name}
            fixtures[name]={"fixture_sha256":hashlib.sha256(body).hexdigest(),"nodes":m.count_metadata_nodes(bindings[name])}
            if name=="test_vector":
                values,meta=m.column(bindings[name],True);assert values==[1,2,3]
            else:
                columns=d.columns(bindings[name]);assert set(columns)=={"class","value"}
                values,_=m.column(columns["class"]);assert values==["a","b","b"]
                values,_=m.column(columns["value"],True);assert values==[1,2,3]
    result={"status":"PASS_V2_OFFICIAL_TINY_FIXTURES","fixtures":fixtures,"runtime":proof,"author_data_parsed":False,"count_analysis":False,"models_fit":0,"independent_R_runtime_parity":False}
    with (OUT/"pilot_receipt.json").open("xb") as f:f.write((json.dumps(result,sort_keys=True,indent=2)+"\n").encode())
    print("PASS v2 literal traversal and columns against two official tiny fixtures",flush=True)
if __name__=="__main__":run()
