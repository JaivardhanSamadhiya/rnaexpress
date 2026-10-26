"""Deferred current software byte guard; actual owned FIT is not implemented."""
import os
from pathlib import Path
import sys
from . import contracts as c,spec


class PendingCurrentContext(RuntimeError):pass


def source_mode():
    assert spec.ROOT.resolve()==spec.EXPECTED_ROOT.resolve() and spec.ROOT.drive.casefold()=='c:'
    assert sys.flags.no_site==1 and sys.dont_write_bytecode is True
    assert sys.pycache_prefix==str(spec.CACHE_PREFIX) and not os.path.lexists(spec.CACHE_PREFIX)
    assert all(os.environ.get(key)=='1' for key in spec.THREAD_KEYS)
    assert os.environ.get('PYTHONUTF8')==os.environ.get('PYTHONDONTWRITEBYTECODE')=='1'


def _bound(name,want):
    path=spec.ROOT/c.relative(name);assert not path.is_symlink() and path.resolve().is_relative_to(spec.ROOT.resolve())
    raw=path.read_bytes();assert c.digest(raw)==c.sha(want),name
    return raw


def _software_contract(inventory,receipt,child,certificate):
    """Supplied records, not proof that a provider/owner ran in this process."""
    assert inventory['status']=='PASS_CDRIVE_CURRENT42_UNCHANGED7998_BYTES_COMPATIBILITY_PENDING'
    assert inventory['private_material_verification_sha256']==spec.MATERIAL_VERIFICATION_SHA
    assert inventory['selected_scientific_payload_file_count']==len(inventory['selected_scientific_payload_files'])==7998
    assert inventory['current_native_file_count']==len(inventory['current_bundled_stdlib_native_files'])==42
    assert receipt['status']=='PASS_INVENTED_CURRENT42_RUNTIME_COMPATIBILITY_NOT_BIOLOGICAL_ADMISSION' and receipt['failure'] is None
    assert receipt['preparation_manifest_sha256']==spec.PROFILE_MANIFEST_SHA
    assert receipt['invented_optimizer_units']==child['invented_optimizer_units']==12
    # Raw child bytes are checked by _bound before decoding. Never substitute
    # a reserialization hash for the profile's actual raw-file hash.
    c.sha(receipt['child_completion_sha256'])
    assert receipt['full_FIT_or_old_interpreter_parity_established'] is receipt['biological_admission_granted'] is False
    assert child['status']=='PASS_INVENTED_CURRENT42_PAGED_PARSER_OPTIMIZER_EXTRAS'
    assert child['fresh_inventory_sha256']==spec.INVENTORY_SHA
    assert child['biological_rows_read']==child['biological_model_fits']==receipt['biological_rows_read']==receipt['scientific_attempts']==0
    for proof in (child['initial_native_proof'],child['final_native_proof']):
        assert proof['status']=='PASS_ACTUAL_CURRENT42_NATIVE_AND_UNCHANGED_LOADED_SCIENTIFIC_ORIGINS'
        assert proof['old_exact_runtime_identity_passes'] is proof['old_interpreter_bitwise_parity_established'] is False
        assert proof['fresh_inventory_sha256']==spec.INVENTORY_SHA
    assert certificate['status']=='VERIFIED_CDRIVE_CURRENT42_INVENTED_COMPATIBILITY_NOT_BIOLOGICAL_ADMISSION'
    assert certificate['initial_manifest_sha256']==spec.PROFILE_MANIFEST_SHA
    assert certificate['fresh_current_bundled_native_count']==42 and certificate['invented_optimizer_units']==12
    assert certificate['buffer_hash_checks']==3 and certificate['retained_invented_padding_bytes']==384*2**20
    assert certificate['saved_before_after_origin_proofs_consistent_with_fresh_bytes'] is True
    assert certificate['all_recorded_resource_snapshots_pass'] is True
    assert certificate['metadata_array_label_FIT_admissions_granted_here'] is False
    assert certificate['old_exact_runtime_identity_passes'] is certificate['old_interpreter_bitwise_parity_established'] is False
    assert certificate['biological_rows_read']==certificate['new_jobs_or_model_fits']==0
    assert certificate['canonical_original_V4_result_sha256']==child['canonical_result_sha256']
    return {'status':'VERIFIED_SAVED_CURRENT_COMPATIBILITY_NOT_CURRENT_LOADED_ORIGINS_OR_FIT',
        'inventory_sha256':spec.INVENTORY_SHA,'profile_receipt_sha256':spec.PROFILE_RECEIPT_SHA,
        'independent_certificate_sha256':spec.PROFILE_CERTIFICATE_SHA,
        'old_current_native_PASS_reused':False,'actual_current_loaded_origins_verified_here':False,
        'actual_owned_Job_verified_here':False,'actual_stage_authority_granted_here':False}


def verify_current_software_bytes():
    """No public probe/bootstrap parameter; missing proof fails before reads.

    This byte checker never returns an actual runtime/stage capability.
    A real owned provider with fresh resource/proof actions is still missing.
    It performs no scientific imports or old native-admission calls.
    """
    try:c.sha(spec.PROFILE_CERTIFICATE_SHA)
    except AssertionError as error:
        raise PendingCurrentContext('Missing reviewed independent current-profile certificate') from error
    source_mode()
    inventory=c.decode(_bound(spec.INVENTORY,spec.INVENTORY_SHA))
    from src.generalization_cdrive_numeric_profile_20261025 import spec as profile_spec
    assert Path(sys.executable).resolve()==profile_spec.EXPECTED_PYTHON.resolve()
    assert inventory['python_version']==sys.version and inventory['python_cache_tag']==sys.implementation.cache_tag=='cpython-312'
    manifest=c.decode(_bound(spec.PROFILE_MANIFEST,spec.PROFILE_MANIFEST_SHA))
    for name,want in manifest['files'].items():_bound(name,want)
    # Complete 7998 byte checks, not the old current_payload/attestation path.
    payload=inventory['selected_scientific_payload_files']
    assert len(payload)==7998
    actual={p.relative_to(spec.PREFIX).as_posix() for p in spec.PREFIX.rglob('*') if p.is_file()}
    assert actual==set(payload)
    for name,want in payload.items():
        path=spec.PREFIX/c.relative(name)
        assert not path.is_symlink() and path.resolve().is_relative_to(spec.PREFIX.resolve())
        assert c.digest(path.read_bytes())==c.sha(want),name
    natives=inventory['current_bundled_stdlib_native_files'];assert len(natives)==42
    home=Path(sys.executable).resolve().parent
    assert len({str(Path(name).resolve()).casefold() for name in natives})==42
    for name,want in natives.items():
        path=Path(name)
        assert path.is_absolute() and not path.is_symlink() and path.resolve().is_relative_to(home)
        assert c.digest(path.read_bytes())==c.sha(want),name
    receipt=c.decode(_bound(spec.PROFILE_RECEIPT,spec.PROFILE_RECEIPT_SHA))
    child_name='results/generalization_cdrive_numeric_profile_20261025/toy_child.json'
    child_raw=_bound(child_name,receipt['child_completion_sha256'])
    certificate=c.decode(_bound(spec.PROFILE_CERTIFICATE,spec.PROFILE_CERTIFICATE_SHA))
    return _software_contract(inventory,receipt,c.decode(child_raw),certificate)


def require_real_owned_fit_context(*args,**kwargs):
    """Intentionally no declaration/Boolean can grant scientific authority."""
    raise PendingCurrentContext('No implemented reviewed current owned-Job/controller or fresh manual FIT authorization')
