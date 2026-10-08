
"""Custom partial-package loader for reviewed untouched rdata parser sources."""
from pathlib import Path
import json,hashlib,sys,types,importlib,importlib.machinery,ctypes
ROOT=Path(__file__).resolve().parents[2];NS="generalization_rdata_metadata_feasibility_20261008"
OUT=ROOT/"results"/NS;VENDOR=ROOT/"data/interim"/NS
SCI=ROOT/"data/interim/mechanism_v2/runtime"
REFERENCE=ROOT/"artifacts/generalization_splicebert_runtime_compatibility_20261007/scientific_runtime_receipt.json"
def read(path):return json.loads(Path(path).read_text(encoding="utf8"))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load():
    from src.generalization_rbp_cellaxis_downstream_20261007.runtime_guard import python_contract
    reference=read(REFERENCE);python_contract(reference)
    assert not any(name=="rdata" or name.startswith("rdata.") for name in sys.modules)
    assert not any(name in sys.modules for name in ("numpy","pandas","xarray"))
    receipt=read(OUT/"wheel_source_receipt.json")
    assert receipt["status"]=="PASS_FIXED_WHEEL_BYTES_AND_SOURCE_INVENTORY_ONLY"
    for name,digest in receipt["selected_sources"].items():assert sha(VENDOR/name)==digest,name
    sys.path.insert(0,str(SCI));import numpy as np
    assert np.__version__=="1.26.4" and Path(np.__file__).resolve().is_relative_to(SCI.resolve())
    rel=Path(np.__file__).resolve().relative_to(SCI.resolve()).as_posix()
    assert sha(np.__file__)==reference["files"][rel]
    package=types.ModuleType("rdata");package.__path__=[str(VENDOR/"rdata")];package.__package__="rdata"
    package.__spec__=importlib.machinery.ModuleSpec("rdata",loader=None,is_package=True)
    package.__spec__.submodule_search_locations=package.__path__
    sys.modules["rdata"]=package
    parser=importlib.import_module("rdata.parser")
    origins={}
    for name,module in sorted(sys.modules.items()):
        if name.startswith("rdata."):
            path=Path(module.__file__).resolve();assert path.is_relative_to(VENDOR.resolve())
            key=path.relative_to(VENDOR.resolve()).as_posix();assert sha(path)==receipt["selected_sources"][key]
            origins[name]={"path":path.relative_to(ROOT).as_posix(),"sha256":sha(path)}
    assert not any(name.startswith("rdata.conversion") for name in sys.modules)
    assert "pandas" not in sys.modules and "xarray" not in sys.modules
    return parser,np,{"custom_partial_package_named_rdata":True,"stock_rdata_initializer_executed":False,
        "stock_conversion_executed":False,"loaded_parser_sources":origins,"numpy_init_sha256":sha(np.__file__),
        "numpy_version":np.__version__,"numpy_origin":Path(np.__file__).relative_to(ROOT).as_posix(),
        "pinned_python_contract_verified":True,"numpy_init_origin_is_not_a_full_native_DLL_attestation":True}
