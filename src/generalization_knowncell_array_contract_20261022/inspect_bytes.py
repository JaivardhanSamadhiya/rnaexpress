"""Bounded NPZ/NPY parsing using supplied bytes and standard library only."""
import ast
import hashlib
import io
import math
import struct
import sys
import zipfile
import zlib
from .spec import MAX_NPZ_BYTES, MAX_NPY_BYTES, MAX_HEADER_BYTES, NPZ_MEMBER, SHAPE


def checked_sha(raw, expected):
    assert isinstance(raw, bytes)
    assert isinstance(expected, str) and len(expected) == 64 and all(c in '0123456789abcdef' for c in expected)
    actual = hashlib.sha256(raw).hexdigest()
    assert actual == expected, 'Supplied bytes differ from explicit immutable expected SHA'
    return actual


def _extra_fields(extra):
    values = {}; offset = 0
    while offset < len(extra):
        assert offset + 4 <= len(extra), 'Truncated ZIP extra header'
        tag, size = struct.unpack_from('<HH', extra, offset); offset += 4
        assert tag not in values and offset + size <= len(extra), 'Duplicate/truncated ZIP extra field'
        values[tag] = extra[offset:offset+size]; offset += size
    return values


def _expanded_member(raw, info):
    """Check local/central agreement and one COMPLETE bounded deflate stream."""
    assert info.header_offset == 0, 'No leading/prefix ZIP payload'
    assert len(raw) >= 30
    signature, version, flags, method, mtime, mdate, crc, compressed, expanded, name_size, extra_size = struct.unpack_from('<4s5H3L2H', raw)
    assert signature == b'PK\x03\x04'
    assert flags == info.flag_bits and flags & ~0x0800 == 0, 'Encrypted/data-descriptor/unsupported ZIP flags'
    assert method == info.compress_type and method in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
    start = 30 + name_size + extra_size
    assert start <= len(raw) and raw[30:30+name_size] == NPZ_MEMBER.encode('ascii')
    extras = _extra_fields(raw[30+name_size:start])
    offset = 0; zip64 = extras.get(1, b'')
    if expanded == 0xffffffff:
        assert len(zip64) >= offset + 8; expanded = struct.unpack_from('<Q', zip64, offset)[0]; offset += 8
    if compressed == 0xffffffff:
        assert len(zip64) >= offset + 8; compressed = struct.unpack_from('<Q', zip64, offset)[0]; offset += 8
    assert crc == info.CRC and compressed == info.compress_size and expanded == info.file_size
    assert 0 <= expanded <= MAX_NPY_BYTES and 0 <= compressed <= MAX_NPZ_BYTES
    end = start + compressed; assert end <= len(raw)
    compressed_bytes = memoryview(raw)[start:end]
    if method == zipfile.ZIP_STORED:
        assert compressed == expanded
        result = bytes(compressed_bytes)
    else:
        decoder = zlib.decompressobj(-15)
        result = decoder.decompress(compressed_bytes, MAX_NPY_BYTES + 1)
        assert len(result) <= MAX_NPY_BYTES, 'Expanded ZIP payload exceeds fixed cap'
        assert decoder.eof and not decoder.unconsumed_tail and not decoder.unused_data, 'Incomplete/extra deflate payload'
    assert len(result) == expanded
    assert zlib.crc32(result) & 0xffffffff == info.CRC, 'ZIP CRC mismatch'
    return result, end


def inspect_npy(raw, expected_shape=SHAPE):
    """Strict scalar-float64 header/shape/length contract, no NumPy import."""
    assert isinstance(raw, bytes) and len(raw) <= MAX_NPY_BYTES
    assert len(raw) >= 10 and raw[:6] == b'\x93NUMPY', 'Bad/truncated NPY magic'
    version = tuple(raw[6:8]); assert version in ((1, 0), (2, 0)), 'Unsupported NPY version'
    prefix = 10 if version == (1, 0) else 12
    assert len(raw) >= prefix
    header_size = struct.unpack_from('<H' if prefix == 10 else '<I', raw, 8)[0]
    assert 0 < header_size <= MAX_HEADER_BYTES and prefix + header_size <= len(raw), 'Truncated/oversized NPY header'
    header_raw = raw[prefix:prefix+header_size]
    assert header_raw.endswith(b'\n')
    try: text = header_raw.decode('ascii')
    except UnicodeDecodeError as error: raise AssertionError('Non-ASCII simple-array header') from error
    try: tree = ast.parse(text.strip(), mode='eval').body
    except (SyntaxError, ValueError) as error: raise AssertionError('Malformed NPY literal header') from error
    assert isinstance(tree, ast.Dict) and len(tree.keys) == 3
    assert all(isinstance(key, ast.Constant) and isinstance(key.value, str) for key in tree.keys)
    keys = [key.value for key in tree.keys]
    assert len(set(keys)) == 3 and set(keys) == {'descr', 'fortran_order', 'shape'}
    try: header = ast.literal_eval(tree)
    except (ValueError, TypeError) as error: raise AssertionError('Nonliteral NPY header') from error
    assert isinstance(header['descr'], str) and header['descr'] in ('<f8', '>f8', '=f8'), 'Only scalar non-object float64'
    assert type(header['fortran_order']) is bool
    assert isinstance(header['shape'], tuple) and len(header['shape']) == 2
    assert all(type(value) is int and value > 0 for value in header['shape'])
    assert header['shape'] == tuple(expected_shape), 'Exact fixed array shape required'
    count = header['shape'][0] * header['shape'][1]
    assert count <= MAX_NPY_BYTES // 8
    data_offset = prefix + header_size
    assert len(raw) == data_offset + count * 8, 'Truncated/extra/overflow NPY data'
    endian = header['descr'][0]
    if endian == '=': endian = '<' if sys.byteorder == 'little' else '>'
    data = memoryview(raw)[data_offset:]
    for (value,) in struct.iter_unpack(endian + 'd', data): assert math.isfinite(value), 'Nonfinite feature'
    return {'shape': header['shape'], 'descr': header['descr'], 'fortran_order': header['fortran_order'],
            'version': version, 'data_offset': data_offset, 'data_bytes': len(data),
            'all_scalar_features_finite': True, 'npy_sha256': hashlib.sha256(raw).hexdigest()}


def inspect_npz(raw, expected_sha256, expected_shape=SHAPE):
    assert isinstance(raw, bytes) and 0 < len(raw) <= MAX_NPZ_BYTES, 'Compressed byte cap'
    actual_sha = checked_sha(raw, expected_sha256)
    with zipfile.ZipFile(io.BytesIO(raw), 'r') as archive:
        infos = archive.infolist()
        assert len(infos) == 1 and infos[0].filename == NPZ_MEMBER, 'Exactly sole features.npy required'
        info = infos[0]
        assert not info.is_dir() and not info.flag_bits & 1, 'No directory/encrypted member'
        assert archive.comment == b'' and info.comment == b''
        assert info.file_size <= MAX_NPY_BYTES and info.compress_size <= MAX_NPZ_BYTES
        expanded, local_end = _expanded_member(raw, info)
        # In a seekable single-member NumPy archive the central directory starts
        # immediately after that member. No hidden local payload/gaps admitted.
        assert local_end == archive.start_dir
    header = inspect_npy(expanded, expected_shape)
    return {'raw_npz_sha256': actual_sha, 'compressed_bytes': len(raw), 'expanded_bytes': len(expanded),
            'member': NPZ_MEMBER, 'npy': header, 'npy_bytes': expanded,
            'structural_validation_only_not_project_admission': True}


def source_row_bytes(npy_bytes, header):
    """Yield exact stored float64 bit patterns in logical row/column order."""
    rows, columns = header['shape']; offset = header['data_offset']; data = memoryview(npy_bytes)[offset:]
    if not header['fortran_order']:
        for row in range(rows): yield bytes(data[row*columns*8:(row+1)*columns*8])
    else:
        for row in range(rows):
            yield b''.join(bytes(data[(column*rows+row)*8:(column*rows+row+1)*8]) for column in range(columns))
