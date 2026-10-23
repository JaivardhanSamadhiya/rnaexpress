"""Additional strict single-member ZIP envelope; partial inspector stays unchanged."""
import struct
from .inspect_bytes import _extra_fields, inspect_npz
from .spec import MAX_NPZ_BYTES, MAX_NPY_BYTES, NPZ_MEMBER, SHAPE


def envelope_contract(raw):
    assert isinstance(raw, bytes) and 22 <= len(raw) <= MAX_NPZ_BYTES
    signature, disk, central_disk, disk_entries, entries, central_size, central_start, comment_size = struct.unpack_from('<4s4H2LH', raw, len(raw)-22)
    assert signature == b'PK\x05\x06' and comment_size == 0, 'No trailing bytes or ZIP archive comment'
    assert disk == central_disk == 0 and disk_entries == entries == 1, 'Exactly one local single-disk member'
    assert central_start + central_size == len(raw)-22 and central_size >= 46, 'Exact bounded central directory'
    assert central_start >= 30 and central_start + 46 <= len(raw)-22
    values = struct.unpack_from('<4s6H3L5H2L', raw, central_start)
    assert values[0] == b'PK\x01\x02'
    flags, method, compressed, expanded = values[3], values[4], values[8], values[9]
    name_size, extra_size, entry_comment, member_disk, local_offset = values[10], values[11], values[12], values[13], values[16]
    assert flags & ~0x0800 == 0 and method in (0, 8)
    assert 0 <= compressed <= MAX_NPZ_BYTES and 0 <= expanded <= MAX_NPY_BYTES
    assert local_offset == member_disk == entry_comment == 0
    assert 46 + name_size + extra_size == central_size
    name_start = central_start+46; extra_start = name_start+name_size
    assert raw[name_start:extra_start] == NPZ_MEMBER.encode('ascii')
    _extra_fields(raw[extra_start:extra_start+extra_size])
    return {'single_member_single_disk': True, 'trailing_bytes': 0,
            'central_directory_bytes': central_size}


def inspect_supplied_npz(raw, expected_sha256, expected_shape=SHAPE):
    envelope = envelope_contract(raw)
    inspection = inspect_npz(raw, expected_sha256, expected_shape)
    inspection['zip_envelope'] = envelope
    return inspection
