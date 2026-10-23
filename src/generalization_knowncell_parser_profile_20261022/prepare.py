"""Package metadata and byte inventory only; no numerical/native imports."""
import json
from pathlib import Path
import sys
from .common import *


def run():
    assert not any(key.split('.')[0] in ('numpy', 'pandas', 'scipy') for key in sys.modules)
    old = json.loads(RUNTIME.read_bytes()); current = json.loads(PYTHON.read_bytes())
    assert old['status'] == 'PASS' and current['python_version'] == sys.version
    expected = payload_members(old['files'])
    count = check_payload_files(expected)
    versions = {}
    for name, version in (('numpy','1.26.4'), ('pandas','2.2.3'), ('scipy','1.14.1')):
        text = (PREFIX / f'{name}-{version}.dist-info/METADATA').read_text(encoding='utf-8')
        assert '\nName: ' + name + '\n' in '\n' + text and '\nVersion: ' + version + '\n' in '\n' + text
        versions[name] = version
    home = Path(sys.executable).resolve().parent
    python_native = {str(p.resolve()): sha(p) for p in list(home.glob('*.dll')) + list((home/'DLLs').glob('*.dll')) + list((home/'DLLs').glob('*.pyd'))}
    python_native[str(Path(sys.executable).resolve())] = sha(sys.executable)
    assert current['python_native_files'].items() <= python_native.items()
    jsave(INVENTORY, {'status': 'INVENTORIED_EXISTING_PAYLOAD_ONLY_NATIVE_COMPATIBILITY_PENDING',
        'versions': versions, 'prefix': str(PREFIX.resolve()), 'components': list(COMPONENTS),
        'files': expected, 'native_files': native_members(expected), 'file_count': count,
        'old_runtime_receipt_sha256': sha(RUNTIME), 'old_full_prefix_metadata_file_count': len(old['files']),
        'current_python_inventory_sha256': sha(PYTHON), 'python_version': sys.version,
        'current_python_native_files': python_native,
        'old_exact_Python_runtime_identity_passes': False,
        'packages_imported': False, 'biological_inputs_read': False,
        'provenance': 'Existing observed byte inventory; NumPy official wheel parity is separately recorded in original certificate; no new publisher provenance for pandas/SciPy is asserted.'})
    print('PAYLOAD_INVENTORY_ONLY', count, len(python_native), sha(INVENTORY), flush=True)


if __name__ == '__main__': run()
