"""Tiny invented2x3 NPY/ZIP tests; no NumPy/scientific imports or payload reads."""
import ast
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import struct
import sys
import time
import types
import unittest
import warnings
import zipfile
from .envelope import inspect_supplied_npz
from .inspect_bytes import inspect_npy, source_row_bytes
from . import validate as v
from .spec import NS, SRC, OUT, ROOT, SHAPE, MAX_NPZ_BYTES, MAX_NPY_BYTES, STATUS

TINY = (2, 3)
VALUES = ((1., -0., 2.), (1., -0., 2.))
ENV = {key: '1' for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}


def sha(raw): return hashlib.sha256(raw).hexdigest()


def make_npy(values=VALUES, *, shape=TINY, descr='<f8', fortran=False, version=(1,0), header_text=None):
    prefix = 10 if version == (1,0) else 12
    if header_text is None: header_text = repr({'descr':descr,'fortran_order':fortran,'shape':shape})
    header = header_text.encode('ascii'); padding = 64 - ((prefix + len(header)) % 64)
    header += b' ' * (padding-1) + b'\n'
    size = struct.pack('<H' if prefix == 10 else '<I', len(header))
    flat = [values[i][j] for j in range(TINY[1]) for i in range(TINY[0])] if fortran else [x for row in values for x in row]
    endian = descr[0] if descr[0] in ('<','>') else ('<' if sys.byteorder=='little' else '>')
    body = b''.join(struct.pack(endian+'d',value) for value in flat)
    return b'\x93NUMPY'+bytes(version)+size+header+body


def make_zip(npy=None, *, name='features.npy', compression=zipfile.ZIP_DEFLATED, duplicate=False, zip64=False):
    if npy is None: npy=make_npy()
    buffer=io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',UserWarning)
        with zipfile.ZipFile(buffer,'w',compression=compression) as archive:
            if zip64:
                with archive.open(name,'w',force_zip64=True) as member: member.write(npy)
            else: archive.writestr(name,npy)
            if duplicate: archive.writestr(name,npy)
    return buffer.getvalue()


def central_offset(raw): return struct.unpack_from('<4s4H2LH',raw,len(raw)-22)[6]


def tiny_rows():
    base={'dataset':'mikl_gse173098','endpoint_class':'projection','biological_component':'invented_g',
          'parent_sequence':'INVENTED_PARENT','mutant_sequence':'INVENTED_MUTANT','gene_transcript':'invented_gene','held_parent_fold':0}
    return [dict(base,intervention_id='a',cell_type='CAD',parent_context_id='invented_CAD'),
            dict(base,intervention_id='b',cell_type='Neuro-2a',parent_context_id='invented_N2A')]


def tiny_receipts(rows=None):
    if rows is None: rows=tiny_rows()
    identity=v.ids_sha(rows)
    creation={'status':'PASS','rows':2,'widths':{'simple':3},'row_ids_sha256':identity,
              'outcome_columns_read':False,'new_features_or_outcomes_generated':False,'project_fits_run':False}
    metadata={'status':'PASS','rows':2,'components':1,'row_ids_sha256':identity,
              'outcome_columns_read':False,'original_alleles_retained':True,'project_fits_run':False}
    return json.dumps(creation,sort_keys=True).encode(),json.dumps(metadata,sort_keys=True).encode(),identity


def probe(): return {'physical_available':3*2**30,'disk_available':2**30,'PUM_resource_exception_applied':False}


class FakeMatrix:
    def __init__(self,values=VALUES,events=None):
        self.values=values; self.shape=TINY; self.events=[] if events is None else events
        self.dtype=types.SimpleNamespace(kind='f',itemsize=8,hasobject=False,isnative=True)
    def astype(self,dtype):
        assert dtype is float; self.events.append('astype_float'); return self
    def tobytes(self,*,order):
        assert order=='C'; endian='<' if sys.byteorder=='little' else '>'
        return b''.join(struct.pack(endian+'d',value) for row in self.values for value in row)


class FakeArchive:
    files=['features']
    def __init__(self,matrix): self.matrix=matrix
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def __getitem__(self,key): assert key=='features'; return self.matrix


class FakeNumpy:
    __name__='numpy'
    def __init__(self,raw,values=VALUES): self.raw=raw; self.events=[]; self.matrix=FakeMatrix(values,self.events)
    def load(self,buffer,**kwargs):
        assert isinstance(buffer,io.BytesIO) and buffer.read()==self.raw and kwargs=={'allow_pickle':False}
        self.events.append('load_allow_pickle_False'); return FakeArchive(self.matrix)
    def isfinite(self,matrix):
        self.events.append('isfinite'); return types.SimpleNamespace(all=lambda:all(math.isfinite(x) for row in matrix.values for x in row))


class ContainerTests(unittest.TestCase):
    def test_valid_tiny_deflated_stored_and_local_ZIP64(self):
        for options in ({},{'compression':zipfile.ZIP_STORED},{'zip64':True}):
            raw=make_zip(**options); result=inspect_supplied_npz(raw,sha(raw),TINY)
            self.assertEqual(result['npy']['shape'],TINY)
            self.assertEqual(result['member'],'features.npy')
            self.assertTrue(result['structural_validation_only_not_project_admission'])

    def test_wrong_SHA_rejected(self):
        raw=make_zip()
        with self.assertRaisesRegex(AssertionError,'expected SHA'): inspect_supplied_npz(raw,'0'*64,TINY)

    def test_unexpected_or_duplicate_member_rejected(self):
        for raw in (make_zip(name='other.npy'),make_zip(duplicate=True),make_zip(name='../features.npy')):
            with self.assertRaises(AssertionError): inspect_supplied_npz(raw,sha(raw),TINY)

    def test_encrypted_flags_rejected_before_loading(self):
        raw=bytearray(make_zip()); central=central_offset(raw)
        struct.pack_into('<H',raw,6,1); struct.pack_into('<H',raw,central+8,1); raw=bytes(raw)
        with self.assertRaises(AssertionError): inspect_supplied_npz(raw,sha(raw),TINY)

    def test_trailing_prefix_and_comment_payloads_rejected(self):
        original=make_zip()
        for raw in (original+b'x',b'x'+original,original[:-2]+b'\x01\x00'+b'x'):
            with self.assertRaises((AssertionError,zipfile.BadZipFile)): inspect_supplied_npz(raw,sha(raw),TINY)

    def test_declared_expanded_and_compressed_caps(self):
        original=make_zip(); central=central_offset(original)
        for offset,value in ((central+24,MAX_NPY_BYTES+1),(central+20,MAX_NPZ_BYTES+1)):
            raw=bytearray(original); struct.pack_into('<L',raw,offset,value); raw=bytes(raw)
            with self.assertRaises(AssertionError): inspect_supplied_npz(raw,sha(raw),TINY)

    def test_crc_and_local_header_disagreement_rejected(self):
        original=make_zip(); raw=bytearray(original)
        struct.pack_into('<L',raw,14,0); raw=bytes(raw)
        with self.assertRaises(AssertionError): inspect_supplied_npz(raw,sha(raw),TINY)

    def test_truncated_ZIP_and_NPY_bodies(self):
        raw=make_zip()
        for bad in (raw[:-22],raw[:20]):
            with self.assertRaises((AssertionError,zipfile.BadZipFile)): inspect_supplied_npz(bad,sha(bad),TINY)
        for npy in (make_npy()[:-1],make_npy()[:9],make_npy()+b'\0'):
            raw=make_zip(npy)
            with self.assertRaises(AssertionError): inspect_supplied_npz(raw,sha(raw),TINY)

    def test_object_structured_float32_and_wrong_shape_rejected(self):
        for descr in ('|O','<f4',"[('x','<f8')]"):
            raw=make_zip(make_npy(descr=descr))
            with self.assertRaises(AssertionError): inspect_supplied_npz(raw,sha(raw),TINY)
        raw=make_zip(make_npy(shape=(3,2)))
        with self.assertRaisesRegex(AssertionError,'fixed array shape'): inspect_supplied_npz(raw,sha(raw),TINY)

    def test_duplicate_header_keys_and_executable_AST_rejected(self):
        for header in ("{'descr':'<f8','descr':'<f8','shape':(2,3)}",
                       "{'descr':[('x','<f8')],'fortran_order':False,'shape':(2,3)}",
                       "{'descr':__import__('os'),'fortran_order':False,'shape':(2,3)}",
                       "{'descr':'<f8','fortran_order':False,'shape':(True,3)}"):
            with self.assertRaises(AssertionError): inspect_npy(make_npy(header_text=header),TINY)

    def test_NPY_versions_endian_and_Fortran_rows(self):
        expected=[b''.join(struct.pack('<d',x) for x in row) for row in VALUES]
        for version in ((1,0),(2,0)):
            for fortran in (False,True):
                npy=make_npy(version=version,fortran=fortran); header=inspect_npy(npy,TINY)
                self.assertEqual(list(source_row_bytes(npy,header)),expected)
        raw=make_zip(make_npy(descr='>f8',fortran=True)); inspection=inspect_supplied_npz(raw,sha(raw),TINY)
        np=FakeNumpy(raw); matrix,actual=v._materialize_supplied(raw,inspection,np,resource_probe=probe,environment=ENV)
        self.assertEqual(actual,b''.join(expected))

    def test_oversized_header_and_nonfinite_scalar_rejected(self):
        npy=bytearray(make_npy()); struct.pack_into('<H',npy,8,5000)
        with self.assertRaises(AssertionError): inspect_npy(bytes(npy),TINY)
        for value in (float('nan'),float('inf'),float('-inf')):
            with self.assertRaisesRegex(AssertionError,'Nonfinite'): inspect_npy(make_npy(values=((value,0.,0.),(1.,2.,3.))),TINY)


class IdentityTests(unittest.TestCase):
    def test_creation_receipt_and_independent_metadata_ID_order(self):
        rows=tiny_rows(); creation,metadata,rowsha=tiny_receipts(rows)
        result=v.creation_order_contract(rows,creation,metadata,expected_creation_sha256=sha(creation),
            expected_metadata_sha256=sha(metadata),expected_row_ids_sha256=rowsha,expected_shape=TINY)
        self.assertTrue(result['creation_order_matches_supplied_metadata'])
        with self.assertRaises(AssertionError): v.creation_order_contract(list(reversed(rows)),creation,metadata,
            expected_creation_sha256=sha(creation),expected_metadata_sha256=sha(metadata),expected_row_ids_sha256=rowsha,expected_shape=TINY)

    def test_wrong_creation_pin_width_count_and_duplicate_JSON_fail(self):
        rows=tiny_rows(); creation,metadata,rowsha=tiny_receipts(rows)
        with self.assertRaises(AssertionError): v.creation_order_contract(rows,creation,metadata,
            expected_creation_sha256='0'*64,expected_metadata_sha256=sha(metadata),expected_row_ids_sha256=rowsha,expected_shape=TINY)
        for change in ({'rows':3},{'widths':{'simple':4}},{'row_ids_sha256':'f'*64}):
            altered=json.loads(creation); altered.update(change); bad=json.dumps(altered).encode()
            with self.assertRaises(AssertionError): v.creation_order_contract(rows,bad,metadata,
                expected_creation_sha256=sha(bad),expected_metadata_sha256=sha(metadata),expected_row_ids_sha256=rowsha,expected_shape=TINY)
        bad=b'{"x":1,"x":2}'
        with self.assertRaises(AssertionError): v.supplied_json(bad,sha(bad))

    def test_crosscell_exact_allele_feature_bytes(self):
        rows=tiny_rows(); data=[b''.join(struct.pack('<d',x) for x in row) for row in VALUES]
        report=v.crosscell_allele_bytes(rows,data,3)
        self.assertEqual(report['crosscell_allele_groups'],1); self.assertEqual(report['crosscell_rows_checked'],2)
        changed=list(data); changed[1]=data[1][:-1]+bytes([data[1][-1]^1])
        with self.assertRaisesRegex(AssertionError,'BYTES differ'): v.crosscell_allele_bytes(rows,changed,3)

    def test_signed_zero_and_ulp_are_not_tolerated(self):
        rows=tiny_rows(); first=struct.pack('<3d',1.,0.,2.)
        for second in (struct.pack('<3d',1.,-0.,2.),struct.pack('<3d',math.nextafter(1.,2.),0.,2.)):
            with self.assertRaises(AssertionError): v.crosscell_allele_bytes(rows,[first,second],3)

    def test_missing_extra_feature_rows_and_one_cell_groups(self):
        rows=tiny_rows(); blob=struct.pack('<3d',1.,0.,2.)
        for rowbytes in ([blob],[blob,blob,blob]):
            with self.assertRaises(AssertionError): v.crosscell_allele_bytes(rows,rowbytes,3)
        rows[1]['mutant_sequence']='OTHER_INVENTED_ALLELE'
        self.assertEqual(v.crosscell_allele_bytes(rows,[blob,blob],3)['crosscell_allele_groups'],0)


class DeferredRuntimeTests(unittest.TestCase):
    def test_allow_pickle_False_and_original_astype_after_fresh_gate(self):
        raw=make_zip(); inspection=inspect_supplied_npz(raw,sha(raw),TINY); np=FakeNumpy(raw)
        def checked_probe(): np.events.append('fresh_gate'); return probe()
        matrix,actual=v._materialize_supplied(raw,inspection,np,resource_probe=checked_probe,environment=ENV)
        self.assertEqual(np.events,['fresh_gate','load_allow_pickle_False','astype_float','isfinite'])
        self.assertEqual(matrix.shape,TINY); self.assertEqual(len(actual),48)

    def test_low_RAM_disk_PUM_or_threads_stop_before_np_load(self):
        raw=make_zip(); inspection=inspect_supplied_npz(raw,sha(raw),TINY)
        snapshots=[dict(probe(),physical_available=3*2**30-1),dict(probe(),disk_available=2**30-1),
                   dict(probe(),PUM_resource_exception_applied=True)]
        for snapshot in snapshots:
            np=FakeNumpy(raw)
            with self.assertRaises(AssertionError): v._materialize_supplied(raw,inspection,np,resource_probe=lambda:snapshot,environment=ENV)
            self.assertEqual(np.events,[])
        np=FakeNumpy(raw)
        with self.assertRaises(AssertionError): v._materialize_supplied(raw,inspection,np,resource_probe=probe,environment=dict(ENV,OMP_NUM_THREADS='2'))
        self.assertEqual(np.events,[])

    def test_changed_mock_load_or_cast_bits_rejected(self):
        raw=make_zip(); inspection=inspect_supplied_npz(raw,sha(raw),TINY)
        np=FakeNumpy(raw,((math.nextafter(1.,2.),-0.,2.),VALUES[1]))
        with self.assertRaisesRegex(AssertionError,'altered scalar feature bits'):
            v._materialize_supplied(raw,inspection,np,resource_probe=probe,environment=ENV)

    def test_real_entrypoint_rejects_tiny_shape_and_unaccepted_runtime(self):
        rows=tiny_rows(); creation,metadata,rowsha=tiny_receipts(rows); raw=make_zip(); np=FakeNumpy(raw)
        args=dict(expected_npz_sha256=sha(raw),expected_creation_sha256=sha(creation),expected_metadata_sha256=sha(metadata),
                  expected_row_ids_sha256=rowsha,np=np,external_runtime_accepted=False,
                  external_runtime_receipt_sha256='a'*64,resource_probe=probe,environment=ENV)
        with self.assertRaises(AssertionError): v.validate_supplied_array(raw,rows,creation,metadata,**args)
        args['external_runtime_accepted']=True
        with self.assertRaisesRegex(AssertionError,'fixed array shape'): v.validate_supplied_array(raw,rows,creation,metadata,**args)
        self.assertEqual(np.events,[]); self.assertEqual(STATUS,'VALIDATED_SUPPLIED_ARRAY_BYTES_NOT_PROJECT_ADMISSION')
        self.assertEqual(SHAPE,(13781,102))


def run():
    forbidden=('numpy','pandas','scipy','torch','openvino','sklearn')
    assert not any(name in sys.modules for name in forbidden)
    start=time.monotonic()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    assert result.wasSuccessful() and not any(name in sys.modules for name in forbidden)
    sources=sorted(SRC.glob('*.py'))
    for path in sources: ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    payload={'status':'PASS_INVENTED_STDLIB_SUPPLIED_ARRAY_CONTRACT_TESTS','tests':result.testsRun,
             'generated_utc':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':time.monotonic()-start,
             'python_executable':sys.executable,'python_version':sys.version,
             'scientific_runtimes_imported':False,'actual_NumPy_calls':0,'actual_native_resource_probes':0,
             'project_array_reads':0,'project_metadata_reads':0,'project_outcome_reads':0,'models_fitted':0,
             'fixture_shape':[2,3],'actual_full_shape_validator_positive_run':False,
             'public_result_status':STATUS,'project_admission_granted':False,
             'source_files':{path.relative_to(ROOT).as_posix():sha(path.read_bytes()) for path in sources}}
    target=OUT/'synthetic_tests_receipt.json'
    with target.open('xb') as handle: handle.write((json.dumps(payload,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())
    print('INVENTED_SUPPLIED_ARRAY_CONTRACT_PASS',result.testsRun,sha(target.read_bytes()),flush=True)


if __name__=='__main__': run()
