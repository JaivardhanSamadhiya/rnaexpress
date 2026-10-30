"""Software bytes only: fresh native membership and fixed scientific packages."""
import json
import sys
import time
from pathlib import Path
from . import policy as p
from .profile import native_roster


def run():
    p.source_mode()
    started = time.monotonic()
    prior_path = p.ROOT/'results/generalization_software_recheck_20261029/inventory.json'
    prior = p.checked_document(prior_path,'2f9f0a254aa64d1748cea46990f0058501abf027a56807bcde461b0f0cff94b5')
    old = p.checked_document(p.OLD_INVENTORY,p.OLD_SHA)
    expected = old['selected_scientific_payload_files']
    native = native_roster()
    actual = set()
    for component in {key.split('/')[0] for key in expected}:
        root = p.PREFIX/component
        paths = [root] if root.is_file() else root.rglob('*')
        for path in paths:
            if not path.is_file():continue
            assert not path.is_symlink() and path.resolve().is_relative_to(p.PREFIX.resolve())
            key = path.relative_to(p.PREFIX).as_posix()
            assert key in expected and p.sha(path) == expected[key],key
            actual.add(key)
    assert actual == set(expected) and len(actual) == 7998
    assert native_roster() == native, 'native drift during inventory'
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch') for name in sys.modules)
    p.OUT.mkdir(parents=True,exist_ok=True)
    old_native = prior['registered_native_files_sha256']
    value = dict(status='SOFTWARE_BYTES_CURRENT_NATIVE_MEMBERSHIP_NOT_NUMERICAL_ADMISSION',
        client_date='2026-10-30',python_version=sys.version,
        registered_native_files_sha256=native,native_members=len(native),
        changed_vs_oct29=[key for key in old_native if native.get(key) != old_native[key]],
        added_vs_oct29=[key for key in native if key not in old_native],
        prior_inventory_sha256=p.sha(prior_path),scientific_payload_files_rehashed=len(actual),
        scientific_payload_membership_and_bytes_unchanged=True,
        scientific_package_imports=0,biological_input_reads=0,biological_fits=0,
        actual_loaded_origins_certified=False,numerical_compatibility_established=False,
        elapsed_seconds=time.monotonic()-started)
    p.dump(p.OUT/'software_inventory.json',value)
    print(json.dumps(dict(status=value['status'],native_members=len(native),
        changed_registered=len(value['changed_vs_oct29']),added=len(value['added_vs_oct29']),
        scientific_files=len(actual),sha256=p.sha(p.OUT/'software_inventory.json'))))


if __name__ == '__main__':run()
