"""Hand-defined invented menus and masks; no existing project builders called."""
import ast
import copy
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
import time
import unittest
from . import verify as v
from .spec import *

ROOT=Path(__file__).resolve().parents[2]
SMALL={'all_rows':17,'CAD_rows':8,'Neuro-2a_rows':9,'components':3,
    'paired_menus':3,'paired_rows':12,'paired_contexts':6,'paired_directional_decisions':12,
    'unmatched_contexts':2,'unmatched_rows':5}


def fixture():
    rows=[]
    for fold in range(3):
        for cell,short in (('CAD','C'),('Neuro-2a','N')):
            for letter in ('A','B'):
                rows.append({'intervention_id':f'r{fold}{short}{letter}','dataset':'mikl_gse173098',
                    'cell_type':cell,'endpoint_class':'projection','parent_context_id':f'p{fold}{short}',
                    'biological_component':f'g{fold}','gene_transcript':f'gene{fold}',
                    'held_parent_fold':fold,'parent_sequence':f'P{fold}','mutant_sequence':f'M{fold}{letter}'})
    for cell,fold,letters,context in (('CAD',0,('A','B'),'unmatchedC'),('Neuro-2a',1,('A','B','C'),'unmatchedN')):
        for letter in letters:
            rows.append({'intervention_id':context+letter,'dataset':'mikl_gse173098','cell_type':cell,
                'endpoint_class':'projection','parent_context_id':context,'biological_component':f'g{fold}',
                'gene_transcript':f'gene{fold}','held_parent_fold':fold,'parent_sequence':'U'+str(fold),
                'mutant_sequence':context+letter})
    # Literal global-index rosters, independently specified rather than generated
    # by the implementation being tested.
    splits=[
        {'outer_fold':0,'training_indices':[4,5,6,7,8,9,10,11,14,15,16],'target_indices':[0,1,2,3,12,13],
         'inner':[{'validation_fold':1,'training_indices':[8,9,10,11],'validation_indices':[4,5,6,7,14,15,16]},
                  {'validation_fold':2,'training_indices':[4,5,6,7,14,15,16],'validation_indices':[8,9,10,11]}]},
        {'outer_fold':1,'training_indices':[0,1,2,3,8,9,10,11,12,13],'target_indices':[4,5,6,7,14,15,16],
         'inner':[{'validation_fold':0,'training_indices':[8,9,10,11],'validation_indices':[0,1,2,3,12,13]},
                  {'validation_fold':2,'training_indices':[0,1,2,3,12,13],'validation_indices':[8,9,10,11]}]},
        {'outer_fold':2,'training_indices':[0,1,2,3,4,5,6,7,12,13,14,15,16],'target_indices':[8,9,10,11],
         'inner':[{'validation_fold':0,'training_indices':[4,5,6,7,14,15,16],'validation_indices':[0,1,2,3,12,13]},
                  {'validation_fold':1,'training_indices':[0,1,2,3,12,13],'validation_indices':[4,5,6,7,14,15,16]}]},
    ]
    pairs=[{'biological_component':f'g{fold}','parent_sequence':f'P{fold}','mutant_sequences':[f'M{fold}A',f'M{fold}B'],
            'gene_fold':fold,'contexts':{'CAD':f'p{fold}C','Neuro-2a':f'p{fold}N'}} for fold in range(3)]
    identity=hashlib.sha256('|'.join(row['intervention_id'] for row in rows).encode()).hexdigest()
    projected=[[row[column] for column in COLUMNS] for row in rows]
    metadata_sha=hashlib.sha256(json.dumps(projected,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()
    expected={'row_ids_sha256':identity,'metadata_sha256':metadata_sha,'splits':splits,'pairs':pairs,
              'unmatched_contexts':['unmatchedC','unmatchedN']}
    parsed={'rows':rows,'original_core_rows':list(range(0,34,2)),'all_core_rows':ALL_CORE_ROWS,
        'all_core_ids_sha256':'a'*64,'row_ids_sha256':identity,'metadata_sha256':metadata_sha,
        'one_csv_record_per_physical_line':True,'logical_metadata_fields':list(COLUMNS),
        'whole_file_raw_bytes_traversed':True,'unused_csv_fields_tokenized':True,
        'numeric_outcome_columns_parsed':False,'outcome_values_returned':False}
    return {'status':'PASS_GUARDED_MIKL_METADATA_NO_LABEL_OR_ARRAY_ADMISSION',
        'numeric_outcome_rows_admitted':0,'actual_feature_reads':0,'models_fitted':0,
        'metadata_admission_sha256':METADATA_ADMISSION_SHA,'core_sha256':CORE_SHA,
        'declared_simple102_sha256_not_loaded':NPZ_SHA,'metadata':parsed,'contract':expected,
        'every_payload_open_fresh_original_resource_gated':False,
        'resource_calibration':{'original_resource_guards_unchanged':False}}


def check(bundle):return v._check_supplied(bundle,SMALL,fixture()['metadata']['row_ids_sha256'])


class Cases(unittest.TestCase):
    def test_manual_outer_inner_rosters_and_exact_primary_unmatched_counts(self):
        bundle=fixture();before=copy.deepcopy(bundle);result=check(bundle)
        self.assertEqual(bundle,before)
        self.assertEqual(result['counts'],SMALL)
        self.assertEqual(result['reconstructed_contract'],bundle['contract'])
        self.assertEqual(result['outer_masks_rebuilt'],3);self.assertEqual(result['inner_masks_rebuilt'],6)
        self.assertEqual(result['reconstructed_contract']['splits'][0]['target_indices'],[0,1,2,3,12,13])
        self.assertTrue(result['source_and_target_full_menus_preserved'])

    def test_bytes_and_dictionary_reconstruct_identically_but_raw_hash_only_for_bytes(self):
        bundle=fixture();raw=json.dumps(bundle,indent=2).encode();from_bytes=check(raw);from_dict=check(bundle)
        self.assertEqual(from_bytes['canonical_contract_sha256'],from_dict['canonical_contract_sha256'])
        self.assertEqual(from_bytes['supplied_bytes_sha256'],hashlib.sha256(raw).hexdigest())
        self.assertIsNone(from_dict['supplied_bytes_sha256'])
        self.assertFalse(from_bytes['source_CSV_metadata_derivation_independently_verified'])
        self.assertFalse(from_bytes['author_biological_lineage_independently_verified'])
        self.assertFalse(from_bytes['original_core_position_alignment_independently_verified'])

    def test_public_signature_has_no_count_override_and_rejects_small_fixture(self):
        import inspect
        self.assertEqual(tuple(inspect.signature(v.verify_bundle).parameters),('value',))
        with self.assertRaisesRegex(AssertionError,'full-project'):v.verify_bundle(fixture())

    def test_changed_ID_order_even_after_local_hash_updates_rejected_by_external_pin(self):
        bundle=fixture();rows=bundle['metadata']['rows'];rows[0],rows[1]=rows[1],rows[0]
        rebuilt,_=v._rebuild(rows);bundle['contract']=rebuilt
        bundle['metadata']['row_ids_sha256']=rebuilt['row_ids_sha256'];bundle['metadata']['metadata_sha256']=rebuilt['metadata_sha256']
        with self.assertRaisesRegex(AssertionError,'fixed ID/order'):check(bundle)

    def test_duplicate_ID_empty_field_fold_bool_or_extra_outcome_field_rejected(self):
        for mutation in ('ID','empty','bool','outcome'):
            bundle=fixture();rows=bundle['metadata']['rows']
            if mutation=='ID':rows[1]['intervention_id']=rows[0]['intervention_id']
            elif mutation=='empty':rows[0]['parent_sequence']=' '
            elif mutation=='bool':rows[0]['held_parent_fold']=False
            else:rows[0]['measured_delta']='not permitted'
            with self.subTest(mutation=mutation),self.assertRaises(AssertionError):check(bundle)

    def test_component_fold_contradiction_stops_without_extra_purge(self):
        bundle=fixture();bundle['metadata']['rows'][0]['held_parent_fold']=1
        with self.assertRaisesRegex(AssertionError,'Component spans'):check(bundle)

    def test_case_normalized_gene_contradiction_stops_without_repair(self):
        bundle=fixture()
        for row in bundle['metadata']['rows']:
            if row['biological_component']=='g2':row['gene_transcript']='  GENE0  '
        with self.assertRaisesRegex(AssertionError,'Gene contradiction'):check(bundle)

    def test_exact_parent_or_mutant_overlap_across_folds_stops(self):
        for column in ('parent_sequence','mutant_sequence'):
            bundle=fixture();rows=bundle['metadata']['rows']
            if column=='parent_sequence':
                for row in rows:
                    if row['biological_component']=='g2' and row['parent_context_id'].startswith('p2'):row[column]='P0'
            else:rows[8][column]='P0'
            with self.subTest(column=column),self.assertRaisesRegex(AssertionError,'Allele contradiction'):check(bundle)

    def test_duplicate_candidate_and_ambiguous_context_rejected(self):
        for mutation in ('candidate','parent'):
            bundle=fixture();rows=bundle['metadata']['rows']
            if mutation=='candidate':rows[1]['mutant_sequence']=rows[0]['mutant_sequence']
            else:rows[1]['parent_sequence']='other'
            with self.assertRaises(AssertionError):check(bundle)

    def test_pairing_requires_entire_exact_menu_not_intersection(self):
        bundle=fixture();bundle['metadata']['rows'][2]['mutant_sequence']='different_original_candidate'
        rows=bundle['metadata']['rows'];groups,_=v._validate_rows(rows);pairs,unmatched=v._menus(rows,groups)
        self.assertEqual(len(pairs),2);self.assertEqual(len(unmatched),4)
        self.assertIn('p0C',unmatched);self.assertIn('p0N',unmatched)
        with self.assertRaises(AssertionError):check(bundle)

    def test_unmatched_context_is_retained_in_outer_and_inner_source_rosters(self):
        bundle=fixture();result=check(bundle);splits=result['reconstructed_contract']['splits']
        self.assertEqual(result['counts']['unmatched_rows'],5)
        self.assertEqual(splits[0]['inner'][0]['validation_indices'][-3:],[14,15,16])
        self.assertEqual(splits[2]['target_indices'],[8,9,10,11])
        self.assertTrue({12,13,14,15,16}.issubset(splits[2]['training_indices']))

    def test_changed_saved_outer_inner_mask_and_pair_roster_rejected(self):
        for mutation in ('outer','inner','pair','unmatched','metadata_hash'):
            bundle=fixture();contract=bundle['contract']
            if mutation=='outer':contract['splits'][0]['target_indices'].pop()
            elif mutation=='inner':contract['splits'][0]['inner'][0]['training_indices'].append(14)
            elif mutation=='pair':contract['pairs'][0]['contexts']['CAD']='unmatchedC'
            elif mutation=='unmatched':contract['unmatched_contexts'].pop()
            else:contract['metadata_sha256']='0'*64
            with self.subTest(mutation=mutation),self.assertRaisesRegex(AssertionError,'Saved metadata'):check(bundle)

    def test_source_positions_are_only_structurally_checked_and_invalid_order_rejected(self):
        bundle=fixture();bundle['metadata']['original_core_rows']=list(range(100,117))
        self.assertFalse(check(bundle)['original_core_position_alignment_independently_verified'])
        for positions in ([0]*17,list(reversed(range(17))),list(range(16))+[ALL_CORE_ROWS],list(range(16))+[True]):
            bundle=fixture();bundle['metadata']['original_core_rows']=positions
            with self.assertRaises(AssertionError):check(bundle)

    def test_semantic_io_flags_and_declared_source_pins_required(self):
        for mutation in ('labels','whole_file','core','admission','counter'):
            bundle=fixture()
            if mutation=='labels':bundle['metadata']['numeric_outcome_columns_parsed']=True
            elif mutation=='whole_file':bundle['metadata']['whole_file_raw_bytes_traversed']=False
            elif mutation=='core':bundle['core_sha256']='0'*64
            elif mutation=='admission':bundle['metadata_admission_sha256']='0'*64
            else:bundle['numeric_outcome_rows_admitted']=False
            with self.subTest(mutation=mutation),self.assertRaises(AssertionError):check(bundle)

    def test_calibrated_resource_annotations_do_not_change_scientific_contract(self):
        bundle=fixture();before=check(bundle)
        bundle['resource_calibration']={'actual_policy':'invented test only','fresh_calls':123}
        bundle['every_payload_open_fresh_original_resource_gated']=False
        after=check(bundle)
        self.assertEqual(before['canonical_contract_sha256'],after['canonical_contract_sha256'])
        self.assertNotEqual(before['supplied_canonical_bundle_sha256'],after['supplied_canonical_bundle_sha256'])

    def test_duplicate_nonfinite_and_nondictionary_supplied_JSON_rejected(self):
        for raw in (b'{"x":1,"x":2}',b'{"x":NaN}',b'[]'):
            with self.subTest(raw=raw),self.assertRaises(AssertionError):v.verify_bundle(raw)
        class PathLike:
            def __fspath__(self):raise RuntimeError('must never resolve a path')
        with self.assertRaisesRegex(AssertionError,'never a path'):v.verify_bundle(PathLike())

    def test_production_verifier_has_no_project_builder_import_or_IO_operations(self):
        text=(ROOT/'src'/NS/'verify.py').read_text(encoding='utf-8');tree=ast.parse(text)
        forbidden={'pathlib','os','io','csv','subprocess','ctypes','numpy','pandas','scipy','importlib'}
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):self.assertFalse(any(alias.name.split('.')[0] in forbidden for alias in node.names))
            if isinstance(node,ast.ImportFrom):self.assertFalse((node.module or '').startswith('src.'))
            if isinstance(node,ast.Call):
                if isinstance(node.func,ast.Name):self.assertNotIn(node.func.id,('open','eval','exec','compile'))
                if isinstance(node.func,ast.Attribute):self.assertNotIn(node.func.attr,('open','read','read_bytes','read_text','write','write_bytes','write_text'))
        self.assertNotIn('full_metadata_contract(',text)
        self.assertNotIn('if __name__',text)


def run():
    before=set(sys.modules);start=time.perf_counter()
    from .tests_source import SourceCases
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(Cases),
                             unittest.defaultTestLoader.loadTestsFromTestCase(SourceCases)])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.wasSuccessful()
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch','openvino','sklearn') for name in sys.modules)
    assert not any(name.startswith(('src.generalization_knowncell_joint_loader_',
        'src.generalization_knowncell_joint_implementation_')) for name in set(sys.modules)-before)
    source=ROOT/'src'/NS;sources=sorted(source.glob('*.py'))
    receipt={'status':'PASS_INVENTED_PURE_INDEPENDENT_METADATA_TESTS_NOT_ACTUAL_ADMISSION',
        'UTC':datetime.now(timezone.utc).isoformat(),'tests':result.testsRun,'elapsed_seconds':time.perf_counter()-start,
        'sources':{path.relative_to(ROOT).as_posix():hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
        'project_payloads_read':0,'actual_metadata_verifications':0,'actual_workers':0,'actual_resource_probes':0,
        'actual_provider_calls':0,'scientific_imports':False,'reference_builders_or_parsers_called':False,
        'model_fits':0,'public_fullsize_positive_case_run':False,'small_counts_private_test_helper_only':True,
        'approval_or_execution_admission_created':False}
    out=ROOT/'results'/NS/'synthetic_tests_receipt.json'
    with out.open('xb') as stream:stream.write((json.dumps(receipt,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())


if __name__=='__main__':run()
