from .common import ROOT
from .faraway_8h_replication import read_target, target_metadata
from .faraway_opened_audit import directional
import tempfile, zipfile, unittest
from pathlib import Path
import numpy as np


class Faraway8hScopeTests(unittest.TestCase):
    def test_invalid_scope_rejected_before_file_access(self):
        with self.assertRaises(PermissionError): read_target('does-not-exist.xlsx', {1})

    def test_only_whitelisted_numeric_cells_parsed(self):
        row = int(target_metadata().excel_row.iloc[0])
        xml = '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
        xml += f'<row r="{row}"><c r="F{row}"><v>2</v></c><c r="G{row}"><v>8</v></c><c r="H{row}"><v>4</v></c><c r="K{row}"><v>DO_NOT_PARSE</v></c></row>'
        xml += '<row r="1"><c r="F1"><v>DO_NOT_PARSE</v></c></row></sheetData></worksheet>'
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)/'scope.xlsx'
            with zipfile.ZipFile(p, 'w') as z:
                z.writestr('xl/worksheets/sheet3.xml', xml)
                z.writestr('xl/worksheets/sheet2.xml', 'DO_NOT_OPEN')
            self.assertEqual(read_target(p, {row}), {row: 2.})

    def test_direction_metric_handles_ties_and_orientation(self):
        y = np.array([0., 1., 2., 3., 4.]); p = np.array([0., 0., 0., 1., 1.])
        r, gain = directional(y, p, 1)
        self.assertEqual(r, .125); self.assertEqual(gain, 1.5)
        r, gain = directional(y, p, -1)
        self.assertEqual(r, .25); self.assertEqual(gain, 1.)


if __name__ == '__main__': unittest.main()
