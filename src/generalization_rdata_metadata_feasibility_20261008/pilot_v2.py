
"""Reviewed v2 official integer dataframe fixture; old failed pilot preserved."""
from .loader import *
from . import decode
import zipfile
def run():
    parser,np,proof=load()
    wheel=ROOT/"data/raw"/NS/"rdata-1.1.0-py3-none-any.whl"
    assert sha(wheel)==read(OUT/"wheel_source_receipt.json")["wheel_sha256"]
    fixtures={}
    with zipfile.ZipFile(wheel) as z:
        for name in ("test_vector","test_dataframe"):
            path="rdata/tests/data/"+name+".rda";body=z.read(path)
            parsed=parser.parse_data(body,expand_altrep=False,altrep_constructor_dict={},extension=".rda")
            bindings=decode.pairs(parsed.object);assert set(bindings)=={name}
            fixtures[name]={"fixture_sha256":hashlib.sha256(body).hexdigest(),"global_name":name}
            if name=="test_vector":
                obj=bindings[name];assert decode.kind(obj)=="REAL"
                np.testing.assert_array_equal(obj.value,[1.,2.,3.])
            else:
                columns=decode.columns(bindings[name]);assert set(columns)=={"class","value"}
                values,_=decode.column(columns["class"]);assert values==["a","b","b"]
                assert decode.kind(columns["value"])=="INT"
                np.testing.assert_array_equal(columns["value"].value,[1.,2.,3.])
    result={"status":"PASS_CUSTOM_PARSER_OFFICIAL_TINY_FIXTURES","fixtures":fixtures,"runtime":proof,
        "author_RData_parsed":False,"count_analysis":False,"models_fit":0,
        "custom_loader_not_stock_initializer":True,"stock_parser_source_unchanged":True,
        "comparison_to_independent_R_runtime":False}
    with (OUT/"pilot_receipt_v2.json").open("xb") as f:f.write((json.dumps(result,sort_keys=True,indent=2)+"\n").encode())
    print("PASS two official tiny fixtures; no author RData parsed.",flush=True)
if __name__=="__main__":run()
