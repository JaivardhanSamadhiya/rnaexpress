"""Meaningful outcome-free distance, ownership, connectivity and split tests."""
from .common import *
from .graph import reference_distance,distance_matrix,build_graph,runtime_binding,Levenshtein
from .splits import attach_groups,outer_masks,inner_masks
from .prepare import source_hashes
import unittest,itertools

def fixture():
    sequences={'A':'A'*150,'B':'A'*120+'C'*30,'C':'A'*90+'C'*60,'D':'G'*150,'E':'T'*150,'F':'CG'*75}
    folds={'A':0,'B':1,'C':2,'D':1,'E':2,'F':0};rows=[]
    for gene,sequence in sequences.items():
        for cell in ('CAD','Neuro-2a'):
            rows.append({'intervention_id':gene+'_'+cell,'dataset':'mikl_gse173098','cell_type':cell,
                         'endpoint_class':'projection','parent_context_id':gene+'_'+cell,
                         'biological_component':gene,'gene_transcript':gene,'held_parent_fold':folds[gene],
                         'parent_sequence':sequence,'mutant_sequence':sequence})
    return pd.DataFrame(rows)

class Tests(unittest.TestCase):
    def test_exact_scalar_matrix_cutoff_and_symmetry(self):
        strings=['','A','AC','CA','AAC','ACC','CACA','ACGT']
        for cutoff in (0,1,2,30):
            matrix=distance_matrix(strings,strings,cutoff)
            for i,a in enumerate(strings):
                for j,b in enumerate(strings):
                    truth=reference_distance(a,b)
                    self.assertEqual(int(matrix[i,j]),min(truth,cutoff+1))
                    self.assertEqual(int(matrix[i,j]),int(matrix[j,i]))
        rng=np.random.default_rng(17)
        for _ in range(30):
            a=''.join(rng.choice(list('ACGT'),int(rng.integers(1,30))))
            b=''.join(rng.choice(list('ACGT'),int(rng.integers(1,30))))
            self.assertEqual(Levenshtein.distance(a,b,weights=(1,1,1)),reference_distance(a,b))

    def test_long_boundaries_indels_not_hamming(self):
        left='A'*150
        matrix=distance_matrix([left],[left,'A'*120+'C'*30,'A'*119+'C'*31])
        self.assertEqual(matrix.tolist(),[[0,30,31]])
        a='ACGT'*37+'AC';b=a[1:]+a[0]
        self.assertEqual(reference_distance(a,b),2)
        self.assertEqual(int(distance_matrix([a],[b])[0,0]),2)
        self.assertEqual(sum(x!=y for x,y in zip(a,b)),150)

    def test_transitive_global_component_not_direct_identity(self):
        frame=fixture();before=frame.copy(deep=True)
        roster,groups,edges,receipt=build_graph(frame)
        mapping=groups.set_index('biological_component').similarity_component
        self.assertEqual(mapping['A'],mapping['B']);self.assertEqual(mapping['B'],mapping['C'])
        self.assertNotEqual(mapping['A'],mapping['D'])
        self.assertEqual(set(map(tuple,edges[['component_a','component_b']].to_numpy())),{('A','B'),('B','C')})
        self.assertEqual(receipt['unordered_nonidentical_allele_pairs_exhaustively_checked'],15)
        self.assertEqual(receipt['largest_family'],3)
        pd.testing.assert_frame_equal(frame,before)

    def test_ownership_exact_dedup_and_outcome_rejection(self):
        frame=fixture();frame.loc[frame.gene_transcript.eq('B'),['parent_sequence','mutant_sequence']]='A'*150
        roster,groups,edges,receipt=build_graph(frame)
        self.assertEqual(len(roster),5);self.assertEqual(receipt['cross_gene_exact_shared_alleles'],1)
        edge=edges[(edges.component_a=='A')&(edges.component_b=='B')].iloc[0]
        self.assertEqual(edge.distance,0);self.assertEqual(edge.cross_gene_allele_pairs,1)
        bad=frame.assign(measured_delta=0)
        with self.assertRaises(AssertionError):build_graph(bad)

    def test_outer_inner_purge_global_closure_preserves_targets(self):
        frame=fixture();_,groups,_,_=build_graph(frame);grouped=attach_groups(frame,groups)
        train,test=outer_masks(grouped,'CAD_to_N2A',0)
        self.assertEqual(set(grouped.loc[train,'gene_transcript']),{'D','E'})
        self.assertEqual(set(grouped.loc[test,'gene_transcript']),{'A','F'})
        source=grouped[(grouped.cell_type=='CAD')&grouped.gene_transcript.isin(['B','C','D'])].reset_index(drop=True)
        train,validation=inner_masks(source,1)
        self.assertEqual(set(source.loc[validation,'gene_transcript']),{'B','D'})
        self.assertFalse(train.any()) # Whole global closure can remove the sole remaining source gene.

    def test_runtime_native_and_fixed_primary(self):
        binding=runtime_binding()
        self.assertEqual(CUTOFF,30);self.assertEqual(WORKERS,1)
        self.assertEqual(binding['version'],'3.14.1')
        self.assertTrue(any(path.endswith('.pyd') and 'process' in path for path in binding['files']))
        self.assertTrue(any(path.endswith('.pyd') and 'metrics' in path for path in binding['files']))

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    assert result.wasSuccessful()
    jsave(OUT/'synthetic_tests_receipt.json',{'status':'PASS','tests':result.testsRun,'source_hashes':source_hashes(),'runtime':runtime_binding(),'project_fits':0,'outcome_columns_read':0})
