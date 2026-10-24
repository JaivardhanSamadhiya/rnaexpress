"""Invented supplied CSV records only; no actual CORE path or builder calls."""
import ast
import copy
import csv
import hashlib
import io
from pathlib import Path
import unittest
from . import source_verify as s
from .tests import fixture,SMALL
from .spec import *


def core_fixture():
    bundle=fixture();records=[];header=[*COLUMNS,'measured_delta','another_unused_outcome']
    for index,row in enumerate(bundle['metadata']['rows']):
        selected=dict(row);selected['held_parent_fold']=str(selected['held_parent_fold'])+'.0'
        selected.update(measured_delta='not_a_numeric_effect',another_unused_outcome='NaN');records.append(selected)
        other={column:'not_read_as_Mikl_metadata' for column in COLUMNS}
        other.update(intervention_id=f'nonMikl{index}',dataset='other_endpoint',
            held_parent_fold='intentionally_not_numeric',measured_delta='Infinity',another_unused_outcome='1,234')
        records.append(other)
    bundle['metadata']['all_core_rows']=34
    bundle['metadata']['all_core_ids_sha256']=hashlib.sha256('|'.join(record['intervention_id'] for record in records).encode()).hexdigest()
    return bundle,header,records


def csv_text(header,records):
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,header,lineterminator='\n')
    writer.writeheader();writer.writerows(records);return stream.getvalue()


def verify(bundle,text):return s._verify_core(bundle,text,SMALL,fixture()['metadata']['row_ids_sha256'],34)


class SourceCases(unittest.TestCase):
    def test_exact_source_fields_positions_allIDs_and_all_masks(self):
        bundle,header,records=core_fixture();before=copy.deepcopy(bundle);result=verify(bundle,csv_text(header,records))
        self.assertEqual(bundle,before);self.assertEqual(result['reconstructed_contract'],bundle['contract'])
        for key in ('source_CSV_metadata_derivation_independently_verified','original_core_position_alignment_independently_verified',
                    'nonMikl_full_core_ID_roster_independently_verified'):self.assertTrue(result[key])
        self.assertEqual(result['all_core_rows_independently_parsed'],34)
        self.assertFalse(result['author_biological_lineage_independently_verified']);self.assertFalse(result['raw_CORE_byte_SHA_proven_here'])

    def test_stream_is_consumed_without_closing(self):
        bundle,header,records=core_fixture();stream=io.StringIO(csv_text(header,records))
        verify(bundle,stream);self.assertFalse(stream.closed);self.assertEqual(stream.read(),'')

    def test_unused_outcomes_and_nonMikl_invalid_fold_not_converted(self):
        bundle,header,records=core_fixture()
        for record in records:record['measured_delta']='not_float:+-NaN arbitrary text'
        result=verify(bundle,csv_text(header,records));self.assertFalse(result['unused_outcome_fields_numerically_converted'])
        self.assertEqual(result['parsed_outcome_values'],0)

    def test_selected_gene_sequence_position_and_full_ID_mismatch(self):
        for change in ('gene','sequence','position','allids'):
            bundle,header,records=core_fixture()
            if change=='gene':records[0]['gene_transcript']='different_gene'
            elif change=='sequence':records[0]['parent_sequence']='different_parent'
            elif change=='position':records[0],records[1]=records[1],records[0]
            else:records[1]['intervention_id']='changed_nonMikl_ID'
            with self.subTest(change=change),self.assertRaisesRegex(AssertionError,'Independent full CORE'):verify(bundle,csv_text(header,records))

    def test_duplicate_header_missing_column_and_short_or_long_record(self):
        bundle,header,records=core_fixture();text=csv_text(header,records);lines=text.splitlines()
        broken=[text.replace(',measured_delta,',',dataset,',1),text.replace('intervention_id,','unneeded_name,',1),
            '\n'.join([lines[0],','.join(lines[1].split(',')[:-1]),*lines[2:]])+'\n',
            '\n'.join([lines[0],lines[1]+',extra',*lines[2:]])+'\n']
        for value in broken:
            with self.assertRaises(AssertionError):verify(bundle,value)

    def test_duplicate_nonMikl_ID_not_hidden_by_selected_cohort(self):
        bundle,header,records=core_fixture();records[3]['intervention_id']=records[1]['intervention_id']
        with self.assertRaisesRegex(AssertionError,'Unique nonempty full CORE'):verify(bundle,csv_text(header,records))

    def test_multiline_and_blank_physical_records_rejected(self):
        bundle,header,records=core_fixture();records[0]['another_unused_outcome']='first\nsecond'
        with self.assertRaisesRegex(AssertionError,'physical record'):verify(bundle,csv_text(header,records))
        bundle,header,records=core_fixture();text=csv_text(header,records)
        with self.assertRaisesRegex(AssertionError,'physical record'):verify(bundle,text.replace('\n','\n\n',1))
        with self.assertRaisesRegex(AssertionError,'physical CORE'):verify(bundle,text+'\n')

    def test_missing_and_extra_core_records_rejected(self):
        bundle,header,records=core_fixture()
        for modified in (records[:-1],records+[dict(records[-1],intervention_id='extra')]):
            with self.assertRaises(AssertionError):verify(bundle,csv_text(header,modified))

    def test_invalid_selected_fold_and_valid_bounded_decimal_forms(self):
        for token in ('NaN','Infinity','0.5','3','','1'*33):
            bundle,header,records=core_fixture();records[0]['held_parent_fold']=token
            with self.subTest(token=token),self.assertRaises(AssertionError):verify(bundle,csv_text(header,records))
        self.assertEqual(s._fold('1e0'),1);self.assertEqual(s._fold('-0.0'),0)

    def test_public_core_API_has_fixedcounts(self):
        import inspect
        self.assertEqual(tuple(inspect.signature(s.verify_bundle_and_core).parameters),('value','core_text_or_text_stream'))
        bundle,header,records=core_fixture()
        with self.assertRaises(AssertionError):s.verify_bundle_and_core(bundle,csv_text(header,records))

    def test_source_parser_no_project_import_or_file_opener(self):
        root=Path(__file__).resolve().parents[2];tree=ast.parse((root/'src'/NS/'source_verify.py').read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):self.assertFalse((node.module or '').startswith('src.'))
            if isinstance(node,ast.Import):self.assertFalse(any(item.name.split('.')[0] in ('os','pathlib','ctypes','subprocess','numpy','pandas','scipy') for item in node.names))
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):self.assertNotIn(node.func.id,('open','eval','exec','compile'))
