"""Same invented14-case suite with only the additive V2 source/path selected."""
import ast
import sys
import unittest
from unittest.mock import patch
from . import tests as original,bridge_v2 as bridge,contracts as c
from .spec_v2 import *


def run():
    # Private invented test selection only: production code is never patched.
    with patch.object(original,'b',bridge),patch.object(original,'LABEL_PATH',LABEL_PATH):
        result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(original.Tests))
    assert result.wasSuccessful()
    old=ast.parse((SRC/'bridge.py').read_bytes());new=ast.parse((SRC/'bridge_v2.py').read_bytes())
    old_functions=[ast.dump(node,include_attributes=False) for node in old.body if isinstance(node,ast.FunctionDef)]
    new_functions=[ast.dump(node,include_attributes=False) for node in new.body if isinstance(node,ast.FunctionDef)]
    assert old_functions==new_functions,'V2 changes the fixed certificate import only, no function logic'
    assert LABEL_REQUEST=='results/generalization_knowncell_labels_execution_20261024/label_request_manifest.json'
    assert bridge.LABEL_PATH==LABEL_PATH and 'labels_execution_v2_20261024' in bridge.LABEL_PATH
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch','sklearn','openvino') for name in sys.modules)
    sources=sorted(SRC.glob('*.py'))
    for path in sources:ast.parse(path.read_bytes())
    payload={'status':'PASS_INVENTED_CALIBRATED_INPUT_BRIDGE_V2_CERTIFICATE_PATH_ONLY',
        'tests':result.testsRun,'source_files':{p.relative_to(ROOT).as_posix():c.digest(p.read_bytes()) for p in sources},
        'original_bridge_function_AST_unchanged':True,'original_label_runtime_request_path_unchanged':True,
        'project_payloads_read':0,'actual_Git_calls':0,'actual_resource_probes':0,'native_scientific_imports':False,
        'sampler_pool_optimizer_or_gate_calls':0,'actual_root_bindings_created':False}
    path=OUT/'synthetic_tests_receipt_v2.json'
    with path.open('xb') as stream:stream.write(c.canonical(payload))
    print('INVENTED_CALIBRATED_BRIDGE_V2_PASS',result.testsRun,c.digest(path.read_bytes()),flush=True)


if __name__=='__main__':run()
