"""Synthetic tests that restricted readers exclude unrelated numeric fields."""
import tempfile
import unittest
import zipfile
from pathlib import Path
from .author_lineage_audit import selected_csv, scoped_sheet


class AuthorScopeTests(unittest.TestCase):
    def test_csv_rows_and_columns_restricted_and_multiline_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.csv"
            path.write_text("id,effect,stability\na,DO_NOT_PARSE,DO_NOT_PARSE\nb,2.5,DO_NOT_PARSE\nc,DO_NOT_PARSE,DO_NOT_PARSE\n")
            result = selected_csv(path, ["id", "effect"], [1], 3)
            self.assertEqual(result.index.tolist(), [1])
            self.assertEqual(list(result), ["id", "effect"])
            self.assertEqual(float(result.loc[1, "effect"]), 2.5)
            path.write_text('id,effect\n"a\nb",1\n')
            with self.assertRaises(AssertionError):
                selected_csv(path, ["effect"], [0], 1)

    def test_xlsx_only_selected_row_and_localization_column(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.xlsx"
            workbook = '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="localization" sheetId="1" r:id="rId1"/></sheets></workbook>'
            relationships = '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml" Type="worksheet"/></Relationships>'
            sheet = '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
            for row_number, values in [(1, ["element", "effect", "stability"]),
                                       (2, ["excluded", "DO_NOT_PARSE", "DO_NOT_PARSE"]),
                                       (3, ["admitted", "3.75", "DO_NOT_PARSE"])]:
                sheet += '<row r="' + str(row_number) + '">'
                for column, value in zip("ABC", values):
                    sheet += '<c r="' + column + str(row_number) + '" t="inlineStr"><is><t>' + value + '</t></is></c>'
                sheet += '</row>'
            sheet += '</sheetData></worksheet>'
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("xl/workbook.xml", workbook)
                archive.writestr("xl/_rels/workbook.xml.rels", relationships)
                archive.writestr("xl/worksheets/sheet1.xml", sheet)
                archive.writestr("xl/worksheets/protected.xml", "DO_NOT_OPEN")
            result = scoped_sheet(path, "localization", "element", {"admitted"}, ["element", "effect"])
            self.assertEqual(result.index.tolist(), ["admitted"])
            self.assertEqual(list(result), ["excel_row", "effect"])
            self.assertEqual(float(result.loc["admitted", "effect"]), 3.75)
            self.assertEqual(result.loc["admitted", "excel_row"], 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
