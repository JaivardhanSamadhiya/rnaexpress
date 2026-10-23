"""Identical scientific/resource settings, with two explicit old cache pins."""
import json
from pathlib import Path
from src.generalization_knowncell_parser_profile_20261022.common import (
    ROOT,RUNTIME,PYTHON,PREFIX,THREAD_ENV,OPTIONS,PENALTIES,NATIVE_PASS,
    sha,resource_failure,check_thread_environment,certificate_python_files,
)

NS='generalization_knowncell_parser_profile_v3_20261023'
SRC,REP,OUT=[ROOT/part/NS for part in ('src','reports','results')]
MANIFEST=OUT/'preparation_manifest.json'
INVENTORY=OUT/'payload_inventory.json'
BASE_OUT=ROOT/'results/generalization_knowncell_parser_profile_20261022'
BASE_MANIFEST=BASE_OUT/'preparation_manifest_reviewed_v2.json'
BASE_INVENTORY=BASE_OUT/'payload_inventory.json'
BASE_MANIFEST_SHA='41d808e2faddb49e7d1030b70429970bfdbbc999067e136d9fc44941150dacf8'
STATUS='FROZEN_INVENTED_ONE_THREAD_PANDAS_SCIPY_CACHE_CLOSURE_PROFILE_V3'
ADDITIONAL_CACHES={
    '__pycache__/six.cpython-312.pyc':'2fc898ba80bcfb113342227edf336e24464df508595c14fc0a7d5e8890036b39',
    '__pycache__/threadpoolctl.cpython-312.pyc':'ec9cbda12b506fe60ba25f4a4f479750478ce6b52043dea0d3cffa8fbbb699bd',
}


def expanded_files(base,old_full):
    assert all(name not in base for name in ADDITIONAL_CACHES)
    assert all(old_full.get(name)==want for name,want in ADDITIONAL_CACHES.items())
    return dict(base,**ADDITIONAL_CACHES)


def jsave(path,value):
    path=Path(path)
    assert path.parent.resolve()==OUT.resolve()
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n')
