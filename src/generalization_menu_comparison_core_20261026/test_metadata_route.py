"""Invented CSV streams; never opens archives, CORE or actual project rows."""
import csv
import io
import unittest
from . import metadata_route as route
from .tests import fixture


def streams(change=None):
    rows=fixture(); index=io.StringIO();archive=io.StringIO()
    writer=csv.DictWriter(index,fieldnames=route.INDEX_FIELDS,lineterminator='\n');writer.writeheader()
    header=list(route.ARCHIVE_FIELDS)+['measured_localization_value','unrelated_outcome']
    other=csv.DictWriter(archive,fieldnames=header,lineterminator='\n');other.writeheader()
    for i,row in enumerate(rows):
        writer.writerow({key:row[key] for key in route.INDEX_FIELDS})
        for slot,rep in enumerate(route.REPLICATE_IDS[row['dataset']]):
            values={'candidate_id':row['intervention_id'],
                    **{key:row[key] for key in route.FIELDS if key!='intervention_id'},
                    'feature_row':str(i),'replicate_slot':str(slot),'replicate_id':str(rep),
                    'measured_localization_value':'NOT_A_NUMBER_AND_MUST_NOT_BE_PARSED',
                    'unrelated_outcome':'a quoted, unused\nmultiline field'}
            if change:change(i,slot,values)
            other.writerow(values)
    index.seek(0);archive.seek(0)
    return rows,index,archive


class MetadataRouteTests(unittest.TestCase):
    def test_complete_four_assay_metadata_without_parsing_outcomes(self):
        rows,index,archive=streams();result=route.parse_streams(index,archive,expected_rows=36)
        self.assertEqual(result['rows'],tuple(rows))
        self.assertEqual(set(result['study_counts'].values()),{9})
        self.assertEqual(result['archive_records_tokenized'],9*(14+3+4+2))
        self.assertFalse(result['numeric_outcome_columns_parsed'])
        self.assertFalse(result['numeric_outcomes_returned'])
        self.assertTrue(all(set(row)==route.FIELDS for row in result['rows']))

    def test_metadata_mismatch_rejected(self):
        def change(i,slot,row):
            if i==0 and slot==0:row['candidate_id']='changed'
        _,index,archive=streams(change)
        with self.assertRaisesRegex(ValueError,'archive/index'):route.parse_streams(index,archive,expected_rows=36)

    def test_repeated_candidate_sequence_mismatch_rejected(self):
        def change(i,slot,row):
            if i==0 and slot==1:row['mutant_sequence']='A'*10
        _,index,archive=streams(change)
        with self.assertRaisesRegex(ValueError,'repeated candidate'):route.parse_streams(index,archive,expected_rows=36)

    def test_unexpected_or_reserved_replicate_alias_rejected(self):
        def change(i,slot,row):
            if i==27 and slot==1:row['replicate_id']='3'
        _,index,archive=streams(change)
        with self.assertRaisesRegex(ValueError,'replicate alias'):route.parse_streams(index,archive,expected_rows=36)

    def test_missing_and_duplicated_replicate_records_rejected(self):
        _,index,archive=streams();lines=archive.getvalue().splitlines(keepends=True)
        # Use CSV parsing/writing here because an unused fixture field is multiline.
        values=list(csv.reader(io.StringIO(''.join(lines))))
        for bad in (values[:-1],values+[values[-1]]):
            text=io.StringIO();csv.writer(text,lineterminator='\n').writerows(bad);text.seek(0);index.seek(0)
            with self.assertRaises(ValueError):route.parse_streams(index,text,expected_rows=36)

    def test_invalid_feature_indices_rejected(self):
        for invalid in ('-1','36','1.0','999999999999999999999999'):
            def change(i,slot,row):
                if i==0 and slot==0:row['feature_row']=invalid
            _,index,archive=streams(change)
            with self.assertRaises(ValueError):route.parse_streams(index,archive,expected_rows=36)

    def test_bad_or_duplicate_headers_and_row_count_rejected(self):
        _,index,archive=streams()
        with self.assertRaises(ValueError):route.parse_streams(index,archive,expected_rows=35)
        _,index,archive=streams();raw=index.getvalue().replace('dataset','intervention_id',1)
        with self.assertRaisesRegex(ValueError,'duplicate CSV header'):
            route.parse_streams(io.StringIO(raw),archive,expected_rows=36)

    def test_row_index_cannot_smuggle_an_outcome_column(self):
        _,index,archive=streams();rows=list(csv.reader(index));rows[0].append('measured_delta')
        for row in rows[1:]:row.append('1.0')
        text=io.StringIO();csv.writer(text).writerows(rows);text.seek(0)
        with self.assertRaisesRegex(ValueError,'only four metadata fields'):
            route.parse_streams(text,archive,expected_rows=36)


if __name__=='__main__':unittest.main()
