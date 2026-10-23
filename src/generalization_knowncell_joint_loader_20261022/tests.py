"""Invented CSVs/mocks only. No actual admission, native probe or scientific import."""
import ast
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch
from src.generalization_knowncell_joint_implementation_20261022.contracts import exact_pairs
from src.generalization_knowncell_joint_implementation_20261022.tests import rows_fixture
from . import guard, loader, parsers, prepare
from .spec import *


def invented_csv(*, bom=False, duplicate_id=False, multiline=False):
    rows = rows_fixture()
    other = dict(rows[0]); other['dataset'] = 'invented_other_study'; other['intervention_id'] = 'OTHER_CLOSED_TOKEN'
    all_rows = [other] + rows[:4] + [dict(other, intervention_id='OTHER_2')] + rows[4:]
    if duplicate_id: all_rows[-1]['intervention_id'] = all_rows[0]['intervention_id']
    if multiline: all_rows[1]['parent_context_id'] += '\nsecond_line'
    out = io.StringIO(newline=''); fields = list(METADATA_COLUMNS) + ['measured_delta','unadmitted_replica']
    writer = csv.writer(out, lineterminator='\n'); writer.writerow(fields)
    for row in all_rows:
        effect = 'DO_NOT_PARSE_OTHER_STUDY' if row['dataset'] != 'mikl_gse173098' else ('-0.12345678901234567' if row['intervention_id'].endswith(':0') else '0.23456789012345678')
        writer.writerow([row[key] for key in METADATA_COLUMNS] + [effect,'DO_NOT_PARSE_REPLICATE'])
    text = out.getvalue()
    return ('\ufeff' + text if bom else text).encode('utf-8'), all_rows


class FakeSeries(list):
    def to_numpy(self, dtype):
        assert dtype is float
        return [float(value) for value in self]


class FakePandas:
    """Mock ONLY; not a certificate of pandas bitwise parser compatibility."""
    def __init__(self): self.calls = []; self.parsed_tokens = []
    def read_csv(self, stream, **kwargs):
        assert set(kwargs) == {'usecols','low_memory','skiprows'}
        assert kwargs['usecols'] == ['intervention_id','measured_delta'] and kwargs['low_memory'] is False
        self.calls.append(kwargs)
        records = list(csv.reader(io.StringIO(stream.read().decode('utf-8-sig'))))
        indices = parsers.header_indices(records[0], ('intervention_id','measured_delta'))
        ids, effects = FakeSeries(), FakeSeries()
        for number, values in enumerate(records[1:], 1):
            if kwargs['skiprows'](number): continue
            ids.append(values[indices['intervention_id']]); effects.append(values[indices['measured_delta']])
            self.parsed_tokens.append(values[indices['measured_delta']])
        return types.SimpleNamespace(intervention_id=ids, measured_delta=effects)


class ParserTests(unittest.TestCase):
    def test_metadata_keeps_exact_fields_original_order_and_offsets(self):
        raw, original = invented_csv(); parsed = parsers.metadata_csv(io.StringIO(raw.decode()))
        expected = [row for row in original if row['dataset']=='mikl_gse173098']
        self.assertEqual(parsed['rows'], expected)
        self.assertEqual(parsed['original_core_rows'],[i for i,row in enumerate(original) if row['dataset']=='mikl_gse173098'])
        self.assertEqual(parsed['all_core_rows'],len(original))
        self.assertTrue(all(set(row)==set(METADATA_COLUMNS) for row in parsed['rows']))
        self.assertFalse(parsed['numeric_outcome_columns_parsed'])
        self.assertTrue(parsed['unused_csv_fields_tokenized'])

    def test_invalid_unused_effect_tokens_not_converted(self):
        raw,_=invented_csv(); text=raw.decode().replace('-0.12345678901234567','NOT_A_NUMERIC_EFFECT')
        parsed=parsers.metadata_csv(io.StringIO(text))
        self.assertEqual(len(parsed['rows']),12)

    def test_duplicate_id_anywhere_in_core_fails(self):
        raw,_=invented_csv(duplicate_id=True)
        with self.assertRaises(AssertionError): parsers.metadata_csv(io.StringIO(raw.decode()))

    def test_duplicate_missing_headers_and_malformed_width_fail(self):
        raw,_=invented_csv(); lines=raw.decode().splitlines()
        with self.assertRaises(AssertionError): parsers.metadata_csv(io.StringIO(lines[0]+',intervention_id\n'+lines[1]+',x\n'))
        with self.assertRaises(AssertionError): parsers.metadata_csv(io.StringIO('dataset\nx\n'))
        with self.assertRaises(AssertionError): parsers.metadata_csv(io.StringIO(lines[0]+'\nx,y\n'))

    def test_multiline_record_fails_original_skiprows_contract(self):
        raw,_=invented_csv(multiline=True)
        with self.assertRaises(AssertionError): parsers.metadata_csv(io.StringIO(raw.decode()))

    def test_fold_conversion_is_exact_finite_integer(self):
        for value,expected in (('0',0),('1.0',1),('2e0',2)): self.assertEqual(parsers.fold_value(value),expected)
        for value in ('NaN','Infinity','1.2','3','', 'x'):
            with self.assertRaises(AssertionError): parsers.fold_value(value)

    def test_deferred_original_parser_options_and_selected_rows_only(self):
        raw,_=invented_csv(); metadata=parsers.metadata_csv(io.StringIO(raw.decode())); pd=FakePandas()
        result=parsers.pandas_effects(io.BytesIO(raw),pd,metadata)
        self.assertEqual(result['intervention_ids'],[row['intervention_id'] for row in metadata['rows']])
        self.assertEqual(len(pd.calls),1); self.assertEqual(len(pd.parsed_tokens),12)
        self.assertNotIn('DO_NOT_PARSE_OTHER_STUDY',pd.parsed_tokens)
        self.assertTrue(result['pinned_pandas_currentPython_and_invented_original_parser_test_certificate_required'])
        self.assertIs(result['old_interpreter_bitwise_parity_established'],False)
        self.assertFalse(pd.calls[0]['skiprows'](0))
        self.assertTrue(pd.calls[0]['skiprows'](1))

    def test_label_wrong_id_order_missing_rows_and_nonfinite_fail(self):
        raw,_=invented_csv(); metadata=parsers.metadata_csv(io.StringIO(raw.decode()))
        bad=dict(metadata); bad['rows']=list(reversed(metadata['rows']))
        with self.assertRaises(AssertionError): parsers.pandas_effects(io.BytesIO(raw),FakePandas(),bad)
        changed=raw.replace(b'-0.12345678901234567',b'nan')
        with self.assertRaises(AssertionError): parsers.pandas_effects(io.BytesIO(changed),FakePandas(),metadata)

    def test_exact_pair_inventory_and_unmatched_roster_not_intersections(self):
        rows=rows_fixture(unmatched=True); pairs,unmatched=exact_pairs(rows); contexts={}
        for row in rows: contexts.setdefault(row['parent_context_id'],[]).append(row)
        saved=[]
        for pair in pairs:
            saved.append({'biological_component':pair['biological_component'],'gene_fold':str(pair['gene_fold']),
                'CAD_context':pair['contexts']['CAD'],'N2A_context':pair['contexts']['Neuro-2a'],
                'candidates':str(len(pair['mutant_sequences'])),'lexical_allele_order_matches':'True'})
        exclusions=[{'cell':contexts[key][0]['cell_type'],'parent_context_id':key,'rows':str(len(contexts[key]))} for key in unmatched]
        self.assertTrue(parsers.inventory_contract(rows,pairs,unmatched,saved,exclusions))
        with self.assertRaises(AssertionError): parsers.inventory_contract(rows,pairs,unmatched,saved[:-1],exclusions)
        with self.assertRaises(AssertionError): parsers.inventory_contract(rows,pairs,unmatched,saved,[])
        saved[0]['candidates']='1'
        with self.assertRaises(AssertionError): parsers.inventory_contract(rows,pairs,unmatched,saved,exclusions)


class GuardTests(unittest.TestCase):
    def setUp(self): self.environment={key:'1' for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}
    def probe(self): return {'physical_available':3*2**30,'disk_available':2**30,'PUM_resource_exception_applied':False}

    def test_hashed_exact_metadata_stream_and_BOM(self):
        raw,_=invented_csv(bom=True)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'invented.csv'; path.write_bytes(raw)
            result,proof=guard.guarded_payload(path,hashlib.sha256(raw).hexdigest(),parsers.metadata_csv,
                                              text=True,resource_probe=self.probe,environment=self.environment)
        self.assertEqual(len(result['rows']),12); self.assertEqual(proof['raw_bytes_traversed'],len(raw))

    def test_fresh_resource_gate_for_each_actual_open(self):
        raw,_=invented_csv(); events=[]
        def probe():
            events.append('probe')
            return {'physical_available':3*2**30-(len(events)>1),'disk_available':2**30}
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'invented.csv'; path.write_bytes(raw)
            guard.guarded_payload(path,hashlib.sha256(raw).hexdigest(),parsers.metadata_csv,text=True,resource_probe=probe,environment=self.environment)
            with patch.object(Path,'open',side_effect=AssertionError('MUST NOT OPEN')) as opened:
                with self.assertRaisesRegex(AssertionError,'three-GiB'):
                    guard.guarded_payload(path,hashlib.sha256(raw).hexdigest(),parsers.metadata_csv,text=True,resource_probe=probe,environment=self.environment)
                opened.assert_not_called()
        self.assertEqual(events,['probe','probe'])

    def test_low_disk_PUM_exception_and_multithread_fail_before_open(self):
        cases=[{'physical_available':3*2**30,'disk_available':2**30-1},
               {'physical_available':3*2**30,'disk_available':2**30,'PUM_resource_exception_applied':True}]
        for snapshot in cases:
            with patch.object(Path,'open',side_effect=AssertionError('MUST NOT OPEN')) as opened:
                with self.assertRaises(AssertionError): guard.guarded_bytes('invented',resource_probe=lambda:snapshot,environment=self.environment)
                opened.assert_not_called()
        environment=dict(self.environment,OMP_NUM_THREADS='2')
        with self.assertRaises(AssertionError): guard.fresh_gate(self.probe,environment)

    def test_wrong_actual_hash_and_partial_large_read_stop(self):
        raw,_=invented_csv()
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'invented.csv'; path.write_bytes(raw)
            with self.assertRaisesRegex(AssertionError,'immutable admission'):
                guard.guarded_payload(path,'0'*64,parsers.metadata_csv,text=True,resource_probe=self.probe,environment=self.environment)
            long=b'x'*100000; path.write_bytes(long)
            with self.assertRaisesRegex(AssertionError,'entire pinned payload'):
                guard.guarded_payload(path,hashlib.sha256(long).hexdigest(),lambda handle:handle.read(1),resource_probe=self.probe,environment=self.environment)


class AdmissionTests(unittest.TestCase):
    def test_reviewed_pandas_certificate_scope_and_version(self):
        record={'status':PANDAS_STATUS,'pandas_version':'2.2.3','original_pandas_version':'2.2.3',
                'original_pandas_package_and_native_bytes_unchanged':True,
                'invented_original_parser_options_and_results':PANDAS_TEST_STATUS,
                'old_interpreter_bitwise_parity_established':False,'biological_rows_read':0,'model_fits':0}
        self.assertTrue(loader.pandas_certificate_contract(record))
        for field,value in (('pandas_version','2.2.4'),('original_pandas_version','2.2.2'),
                            ('original_pandas_package_and_native_bytes_unchanged',False),
                            ('invented_original_parser_options_and_results','MOCK_ONLY'),
                            ('old_interpreter_bitwise_parity_established',True),('biological_rows_read',1)):
            changed=dict(record); changed[field]=value
            with self.assertRaises(AssertionError): loader.pandas_certificate_contract(changed)
        changed=dict(record); del changed['old_interpreter_bitwise_parity_established']
        with self.assertRaises(KeyError): loader.pandas_certificate_contract(changed)

    def test_no_root_start_no_project_or_manifest_read(self):
        with patch.object(loader,'_small',side_effect=AssertionError('NO READ')) as read:
            with self.assertRaisesRegex(AssertionError,'root-start'): loader.load_metadata()
            with self.assertRaisesRegex(AssertionError,'root-start'): loader.load_fit_labels(lambda:None)
            read.assert_not_called()

    def test_metadata_admission_cannot_enable_labels(self):
        manifest={'namespace':NS,'mode':'metadata','status':METADATA_STATUS,'label_access_authorized':True}
        with patch.object(loader,'_small',return_value=loader.canonical_bytes(manifest)),patch.object(loader,'_committed'):
            with self.assertRaises(AssertionError): loader._admission('metadata',True)

    def test_canonical_JSON_contract_handles_tuple_list_serialization(self):
        one={'pairs':[{'alleles':('A','C')}]}; two=json.loads(json.dumps(one))
        self.assertNotEqual(one,two)
        self.assertEqual(loader.canonical_bytes(one),loader.canonical_bytes(two))

    def test_NumPy_only_certificate_cannot_start_pandas_provider(self):
        raw,_=invented_csv(); metadata=parsers.metadata_csv(io.StringIO(raw.decode()))
        core_sha='a'*64; feature_sha='b'*64; contract={'invented':'only'}
        bundle={'status':'PASS_GUARDED_MIKL_METADATA_NO_LABEL_OR_ARRAY_ADMISSION','core_sha256':core_sha,
                'metadata':metadata,'contract':contract}
        bundle_raw=loader.canonical_bytes(bundle)
        array={'status':ARRAY_STATUS,'actual_npz_sha256':feature_sha,'metadata_bundle_sha256':loader.digest(bundle_raw),
               'rows':COUNTS['all_rows'],'columns':102,'same_allele_feature_bytes_equal':True}
        array_raw=loader.canonical_bytes(array)
        pandas_raw=loader.canonical_bytes({'status':'PASS_NUMPY_ONLY'})
        manifest={'metadata_bundle_sha256':loader.digest(bundle_raw),'array_admission_sha256':loader.digest(array_raw),
                  'pandas_admission_sha256':loader.digest(pandas_raw)}
        ready={'declared_data_pins':{ALIASES['core']:core_sha,ALIASES['feature']:feature_sha},
               'expected_mikl_row_ids_sha256':metadata['row_ids_sha256']}
        objects={METADATA_BUNDLE:bundle_raw,ARRAY_ADMISSION:array_raw,PANDAS_ADMISSION:pandas_raw}
        with patch.object(loader,'_admission',return_value=(manifest,ready,'c'*64)),\
             patch.object(loader,'_small',side_effect=lambda rel:objects[rel]),\
             patch.object(loader,'_committed'),patch.object(loader,'full_metadata_contract',return_value=contract),\
             patch.object(loader,'_python_before_pandas') as python_check:
            provider=unittest.mock.Mock()
            with self.assertRaises(AssertionError): loader.load_fit_labels(provider,root_start=True)
            provider.assert_not_called(); python_check.assert_not_called()

    def test_declared_data_pins_must_match_old_freezes(self):
        core,feature=ALIASES['core'],ALIASES['feature']
        declared={core:{'declared_sha256':'a'*64,'actual_bytes_rehashed':False},
                  feature:{'declared_sha256':'b'*64,'actual_bytes_rehashed':False}}
        design={'status':'FROZEN_STATIC_JOINT_KNOWNCELL_DESIGN_NOT_PROJECT_ADMISSION','declared_future_inputs_not_opened':declared}
        source={'files':{core:'a'*64,feature:'b'*64}}
        known={'status':'FROZEN_EVALUATION_KNOWN_CELL','files':{core:'a'*64,feature:'b'*64,
               ALIASES['paired_menu_inventory']:'c'*64,ALIASES['unmatched_inventory']:'d'*64}}
        self.assertEqual(len(prepare.declared_pins(design,source,known)),4)
        known['files'][feature]='0'*64
        with self.assertRaises(AssertionError): prepare.declared_pins(design,source,known)


def run():
    forbidden=('numpy','pandas','scipy','torch','openvino','sklearn')
    assert not any(name in sys.modules for name in forbidden)
    started=time.monotonic()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    assert result.wasSuccessful() and not any(name in sys.modules for name in forbidden)
    paths=sorted(SRC.glob('*.py'))
    for path in paths: ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    payload={'status':'PASS_INVENTED_STDLIB_SELECTIVE_LOADER_CHECKS','tests':result.testsRun,
             'elapsed_seconds':time.monotonic()-started,'generated_utc':datetime.now(timezone.utc).isoformat(),
             'python_executable':sys.executable,'python_version':sys.version,'scientific_runtimes_imported':False,
             'project_dataset_reads':0,'project_feature_reads':0,'project_outcome_reads':0,'models_fitted':0,
             'actual_native_resource_probes':0,'actual_pandas_parser_calls':0,'actual_project_admissions':0,
             'pandas_currentPython_origins_and_actual_parser_tests_NOT_certified':True,
             'old_interpreter_bitwise_parity_established':False,
             'source_files':{path.relative_to(ROOT).as_posix():hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}}
    target=OUT/'synthetic_tests_receipt_reviewed.json'
    with target.open('xb') as handle: handle.write((json.dumps(payload,indent=2,sort_keys=True,allow_nan=False)+'\n').encode())
    print('INVENTED_SELECTIVE_LOADER_TESTS_PASS',result.testsRun,hashlib.sha256(target.read_bytes()).hexdigest(),flush=True)


if __name__=='__main__': run()
