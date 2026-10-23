"""Same runtime/science/resource settings; distinct bound attempt outputs."""
import json
from pathlib import Path
from src.generalization_knowncell_parser_profile_v3_20261023.common import (
    ROOT,RUNTIME,PYTHON,PREFIX,INVENTORY,THREAD_ENV,OPTIONS,PENALTIES,NATIVE_PASS,
    sha,resource_failure,check_thread_environment,certificate_python_files,
)

NS='generalization_knowncell_parser_profile_v4_20261023'
SRC,REP,OUT=[ROOT/part/NS for part in ('src','reports','results')]
MANIFEST=OUT/'preparation_manifest.json'
BASE_MANIFEST=ROOT/'results/generalization_knowncell_parser_profile_v3_20261023/preparation_manifest.json'
BASE_MANIFEST_SHA='52a26ff64a5217608e3f82c058e9d8d03d68098fe7586da43904826b27b6c567'
STATUS='FROZEN_INVENTED_ONE_THREAD_PROFILE_INITIAL_MANIFEST_BINDING_V4'


def jsave(path,value):
    path=Path(path)
    assert path.parent.resolve()==OUT.resolve()
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n')
