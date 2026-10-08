"""Eight pure mock tests; never import numerical or model packages."""
import types, unittest
from .admission import make_saver, temporary_saver, TARGET

def specification():
    return {'status':'FROZEN_SPLICEBERT_FEATURE_PRODUCTION', 'files':{'old':'a'},
        'rows':26258, 'unique_alleles':18220, 'columns':256, 'threads':2, 'batch_size':2,
        'fresh_3GiB_RAM_and_5GiB_disk_required':True, 'root_start_required':True,
        'native_IR_synthetic_parity_required_and_passed':True, 'no_supervised_fit_authorized':True,
        'other_original_field':['keep']}

class Tests(unittest.TestCase):
    def writer(self, output, extra=None, exists=False):
        return make_saver(lambda p,v:output.append(v), extra or {'new':'b'}, {'bound':True},
                          hasher=lambda p:'a' if p.name=='old' else 'b', exists=lambda p:exists)
    def test_preserves_all_original_fields(self):
        out=[]; original=specification(); self.writer(out)(TARGET,original)
        for key,value in original.items():
            if key!='files': self.assertEqual(out[0][key],value)
        self.assertEqual(original['files'],{'old':'a'}); self.assertEqual(out[0]['files'],{'old':'a','new':'b'})
    def test_repeated_write_rejected(self):
        out=[]; w=self.writer(out); w(TARGET,specification())
        with self.assertRaises(AssertionError): w(TARGET,specification())
    def test_existing_output_rejected(self):
        with self.assertRaises(AssertionError): self.writer([],exists=True)(TARGET,specification())
    def test_unexpected_destination_rejected(self):
        with self.assertRaises(AssertionError): self.writer([])(TARGET.with_name('other'),specification())
    def test_changed_existing_digest_rejected(self):
        with self.assertRaises(AssertionError): self.writer([],{'old':'b'})(TARGET,specification())
    def test_guard_fields_retained(self):
        for field in ('fresh_3GiB_RAM_and_5GiB_disk_required','root_start_required','native_IR_synthetic_parity_required_and_passed','no_supervised_fit_authorized'):
            v=specification(); v[field]=False
            with self.assertRaises(AssertionError): self.writer([])(TARGET,v)
    def test_binding_restores_success(self):
        old=lambda p,v:None; m=types.SimpleNamespace(jsave=old); new=lambda p,v:None
        with temporary_saver(m,new): self.assertIs(m.jsave,new)
        self.assertIs(m.jsave,old)
    def test_binding_restores_failure(self):
        old=lambda p,v:None; m=types.SimpleNamespace(jsave=old)
        with self.assertRaises(ValueError):
            with temporary_saver(m,lambda p,v:None): raise ValueError('synthetic')
        self.assertIs(m.jsave,old)

if __name__ == '__main__': unittest.main()
