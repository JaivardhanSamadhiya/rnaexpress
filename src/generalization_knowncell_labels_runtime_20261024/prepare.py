"""Source/software freeze only; neither labels request nor runtime is invoked."""
import ast
from pathlib import Path
import sys
from .spec import *
from . import contracts as c
from src.generalization_knowncell_metadata_verification_execution_20261024 import common as saved


def run():
    assert not (ROOT/REQUEST).exists(),'Actual request belongs to a future committed stage admission'
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch','sklearn','openvino') for name in sys.modules)
    raw=(ROOT/ORIGINAL_PROVIDER_PREPARATION).read_bytes();assert c.digest(raw)==ORIGINAL_PROVIDER_SHA
    original=c.decode(raw);pins=dict(original['files'])
    pins[ORIGINAL_PROVIDER_PREPARATION]=ORIGINAL_PROVIDER_SHA
    for name,want in pins.items():assert c.digest((ROOT/name).read_bytes())==want,name
    sources=sorted((ROOT/'src'/NS).glob('*.py'))
    receipt_path=ROOT/'results'/NS/'synthetic_tests_receipt.json';receipt=c.decode(receipt_path.read_bytes())
    assert receipt['status']=='PASS_INVENTED_LABELS_RUNTIME_STATE_NOT_ACTUAL_PROVIDER' and receipt['tests']>=6
    assert receipt['sources']=={path.relative_to(ROOT).as_posix():c.digest(path.read_bytes()) for path in sources}
    assert receipt['actual_runtime_invocations']==receipt['actual_resource_probes']==receipt['project_payload_reads']==receipt['model_fits']==0
    own=sources+[ROOT/folder/NS/'.gitattributes' for folder in ('src','reports','results','artifacts')]
    own += [receipt_path,ROOT/'reports'/NS/'protocol.md']
    for path in own:
        raw=path.read_bytes()
        if path.suffix=='.py':ast.parse(raw.decode('utf8'))
        pins[path.relative_to(ROOT).as_posix()]=c.digest(raw)
    saved.save_new(ROOT/PREPARATION,{'status':PREPARATION_STATUS,'files':pins,
        'runtime_provider_module':MODULE,'runtime_provider_qualname':'provide','shared_cache_prefix':str(CACHE_PREFIX),
        'actual_runtime_invoked':False,'data_access_authorized':False,'scientific_imports':False,
        'old_provider_and_parser_source_unchanged':True,'original_provider_preparation_sha256':ORIGINAL_PROVIDER_SHA,
        'only_supported_request':REQUEST,'phases':list(PHASES),'root_owned_lifetime_controller_still_required':True,
        'actual_current_origin_acceptance_still_pending':True,'model_fits':0})
    print('LABELS_RUNTIME_SOURCE_READY',len(pins),c.digest((ROOT/PREPARATION).read_bytes()),flush=True)


if __name__=='__main__':run()
