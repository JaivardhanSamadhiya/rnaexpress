"""Meaningful synthetic checks for reserved-row access and selection scoring."""
import io, unittest, zipfile
from .context_calibration import read_outcomes,decision_regret,features
import numpy as np

class ContextTests(unittest.TestCase):
    def test_reserved_numeric_cells_are_never_parsed(self):
        buffer=io.BytesIO()
        ns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
        with zipfile.ZipFile(buffer,'w') as z:
            z.writestr('xl/workbook.xml',f'<workbook xmlns="{ns}"><sheets><sheet name="finalTab_230221"/></sheets></workbook>')
            z.writestr('xl/worksheets/sheet1.xml',f'<worksheet xmlns="{ns}"><sheetData>'
                       '<row r="2"><c r="I2"><v>1.25</v></c><c r="M2"><v>FORBIDDEN</v></c></row>'
                       '<row r="3"><c r="I3"><v>RESERVED_MUST_NOT_PARSE</v></c></row>'
                       '</sheetData></worksheet>')
        buffer.seek(0)
        values,accessed=read_outcomes(buffer,[2])
        self.assertEqual(values[2][0],1.25)
        self.assertEqual(accessed,['I2'])
        self.assertEqual(set(values),{2})

    def test_two_direction_regret_and_ties(self):
        y=np.arange(10,dtype=float); ids=np.array([str(i) for i in range(10)])
        self.assertEqual(decision_regret(y,y,ids),0)
        self.assertEqual(decision_regret(y,-y,ids),1)
        self.assertEqual(decision_regret(y,np.zeros(10),ids),.5)
        with self.assertRaises(ValueError): decision_regret(y[:2],y[:2],ids[:2])

    def test_feature_normalization(self):
        x=features(['AAAA','ACGTACGT'])
        np.testing.assert_allclose(x[:,0:4].sum(1),1)
        np.testing.assert_allclose(x[:,4:20].sum(1),1)
        np.testing.assert_allclose(x[:,20:].sum(1),1)

if __name__=='__main__': unittest.main()
