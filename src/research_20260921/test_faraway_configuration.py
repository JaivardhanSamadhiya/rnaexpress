from .common import ROOT
import unittest,io,zipfile,tempfile
from pathlib import Path
import numpy as np
from .faraway_configuration import read_values,center,matrix,require_confirmation
from .faraway_design import panel


class FarawayTests(unittest.TestCase):
    def test_closed_outcome_never_parsed(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'toy.xlsx'
            xml='<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="2"><c r="E2"><v>2</v></c><c r="F2"><v>4</v></c><c r="G2"><v>2</v></c></row><row r="3"><c r="E3"><v>DO_NOT_PARSE</v></c></row></sheetData></worksheet>'
            with zipfile.ZipFile(p,'w') as z:z.writestr('xl/worksheets/sheet2.xml',xml)
            values,access=read_values(p,{2})
            self.assertEqual(values,{2:1.});self.assertEqual(len(access),3)

    def test_panel_holds_linked_changes_fixed(self):
        a='00000000'+'00000000';b='00000000'+'10000000'
        self.assertNotEqual(panel(a),panel(b))
        a='11111111'+'00000000';b='11111111'+'10000000'
        self.assertEqual(panel(a),panel(b))

    def test_center_removes_only_panel_intercept(self):
        x=np.array([1.,3.,10.,14.]);g=np.array(['a','a','b','b'])
        np.testing.assert_array_equal(center(x,g),[-1,1,-2,2])

    def test_cross_features_distinguish_GA_but_global_pattern_does_not(self):
        g=['0000000010101010','1111111110101010']
        np.testing.assert_array_equal(matrix(g,'pattern')[0],matrix(g,'pattern')[1])
        self.assertFalse(np.array_equal(matrix(g,'interaction')[0],matrix(g,'interaction')[1]))

    def test_failed_gate_cannot_open_confirmation(self):
        with self.assertRaises(PermissionError):require_confirmation({'passed':False})
