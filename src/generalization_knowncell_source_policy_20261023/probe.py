"""Invented subprocess test of an absent CPython cache prefix; no biology."""
import hashlib
import json
import os
from pathlib import Path
import py_compile
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'results/generalization_knowncell_source_policy_20261023'
PROFILE = ROOT/'results/generalization_knowncell_parser_profile_v4_20261023/preparation_manifest.json'
EXPECTED = '61781e1ef932a2eb36a368279d96bd52b35bf0eaf286dc8f80021e42fd5a2daa'
PREFIX = ROOT/'results/generalization_knowncell_parser_profile_v4_20261023/never_created_source_cache'


def run():
    assert hashlib.sha256(PROFILE.read_bytes()).hexdigest() == EXPECTED
    assert not PREFIX.exists()
    with tempfile.TemporaryDirectory(prefix='invented_cache_policy_') as folder:
        path = Path(folder)
        source = path/'invented_policy_module.py'
        source.write_text('value = 11\n', encoding='utf-8')
        stamp = source.stat()
        py_compile.compile(str(source), doraise=True)
        source.write_text('value = 22\n', encoding='utf-8')
        os.utime(source, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
        program = 'import invented_policy_module as m,sys,json; print(json.dumps({"value":m.value,"prefix":sys.pycache_prefix,"no_write":sys.dont_write_bytecode}))'
        plain_env = dict(os.environ)
        plain_env.pop('PYTHONPYCACHEPREFIX', None)
        normal = json.loads(subprocess.check_output([sys.executable,'-S','-B','-c',program], cwd=path, env=plain_env))
        bypass_env = dict(plain_env, PYTHONPYCACHEPREFIX=str(PREFIX))
        bypass = json.loads(subprocess.check_output([sys.executable,'-S','-B','-c',program], cwd=path, env=bypass_env))
        assert normal['value'] == 11 and bypass['value'] == 22
        assert bypass['prefix'] == str(PREFIX) and bypass['no_write'] is True
        assert not PREFIX.exists()
    record = {'status':'PASS_INVENTED_SOURCE_CACHE_BYPASS_WITH_ABSENT_PREFIX',
              'normal_stale_cache_value':normal['value'], 'bypass_current_source_value':bypass['value'],
              'PYTHONPYCACHEPREFIX':str(PREFIX), 'prefix_absent_before_and_after':True,
              'python_executable':sys.executable, 'python_executable_sha256':hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(),
              'native_profile_manifest_sha256':EXPECTED, 'profile_source_or_scientific_cases_changed':False,
              'scientific_packages_imported':False, 'project_inputs_read':0,
              'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    with (OUT/'source_cache_policy_receipt.json').open('x', encoding='utf-8', newline='\n') as handle:
        handle.write(json.dumps(record, sort_keys=True, indent=2)+'\n')
    print('INVENTED_CACHE_BYPASS_PASS', flush=True)


if __name__ == '__main__':
    run()
