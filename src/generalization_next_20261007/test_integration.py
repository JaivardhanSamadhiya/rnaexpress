"""Independent synthetic check of correlated-component bootstrap arithmetic."""
from .common import np,pd,jsave,OUT,sha256,Path
from .bootstrap import shared_bootstrap
import unittest

class BootstrapTests(unittest.TestCase):
    def test_shared_component_uses_same_underlying_weight(self):
        gains={'a':pd.Series([1.,-1.],index=['shared','a_only']),
               'b':pd.Series([2.,0.],index=['shared','b_only'])}
        seed=53; draws=17
        weights=np.random.default_rng(seed).exponential(1,size=(draws,3))
        # Sorted union is a_only,b_only,shared. The shared column must be reused.
        expected=((weights[:,2]-weights[:,0])/(weights[:,2]+weights[:,0])
                  +2*weights[:,2]/(weights[:,2]+weights[:,1]))/2
        np.testing.assert_allclose(shared_bootstrap(gains,draws,seed),expected,atol=1e-15,rtol=0)

    def test_equal_assay_weight_for_single_component_assays(self):
        gains={'a':pd.Series([.2],index=['shared']),'b':pd.Series([-.1],index=['shared'])}
        np.testing.assert_allclose(shared_bootstrap(gains,19,11),.05,atol=1e-16,rtol=0)

def run():
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(BootstrapTests))
    assert result.wasSuccessful()
    jsave(OUT/'integration_tests_receipt.json',{'status':'PASS','tests':result.testsRun,
        'code_sha256':sha256(Path(__file__)),'research_outcomes_used':False,'unfiltered_pytest':False})

if __name__=='__main__':run()
