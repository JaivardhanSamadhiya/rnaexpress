from .faraway_processed_correspondence import read_scoped_tsv
import tempfile,unittest
from pathlib import Path


class ProcessedScopeTests(unittest.TestCase):
    def test_closed_numeric_cells_never_converted(self):
        header='bc_number\tn_introns\tn_opt\treplicate\ttime\tcytoplasm\tnucleus\tnc_ratio\tstructure\tint_pattern\n'
        s='-'.join(['Opt']*8);i='-'.join(['NoInt']*8)
        body=header+f'1\t0\t8\t1\t8 hr\t2\t4\t2\t{s}\t{i}\n'
        body+=f'1\t0\t8\t1\t16 hr\tDO_NOT_PARSE\tDO_NOT_PARSE\tDO_NOT_PARSE\t{s}\t{i}\n'
        body+=f'2\t0\t8\t1\t8 hr\tDO_NOT_PARSE\tDO_NOT_PARSE\tDO_NOT_PARSE\t{s}\t{i}\n'
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'scope.tsv';p.write_text(body)
            result,metadata=read_scoped_tsv(p,{('1',1,'8 hr'):'1111111100000000'},True)
            self.assertEqual(result,{('1',1,'8 hr'):1.});self.assertEqual(len(metadata),3)


if __name__=='__main__':unittest.main()
