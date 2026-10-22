import pathlib,types,unittest
from . import worker
class CallbackTests(unittest.TestCase):
 def test_restore_after_exception(self):
  oldguard=lambda:3*2**30;oldsave=lambda p,x:x;m=types.SimpleNamespace(fresh_guard=oldguard,save=oldsave)
  with self.assertRaisesRegex(RuntimeError,'invented'):
   with worker.scoped_callbacks(m,'production','fixed'):
    self.assertIs(m.fresh_guard,worker.resource_guard);raise RuntimeError('invented')
  self.assertIs(m.fresh_guard,oldguard);self.assertIs(m.save,oldsave)
 def test_numerical_payload_unchanged(self):
  capture=[];m=types.SimpleNamespace(fresh_guard=lambda:0,save=lambda p,x:capture.append(x))
  original={'point_delta_logZ':{'released_csv':1.234},'source_ID':'invented'}
  with worker.scoped_callbacks(m,'production','fixed'):m.save(pathlib.Path('invented_background.json'),original)
  self.assertIs(capture[0],original)
 def test_receipt_truthfully_discloses_override(self):
  capture=[];m=types.SimpleNamespace(fresh_guard=lambda:0,save=lambda p,x:capture.append(x))
  original={'all_existing_model_feature_floors_unchanged':True,'numerical_field':17}
  with worker.scoped_callbacks(m,'production','fixed'):m.save(worker.RECEIPTS['production'],original)
  self.assertTrue(original['all_existing_model_feature_floors_unchanged'])
  self.assertFalse(capture[0]['all_existing_model_feature_floors_unchanged']);self.assertEqual(capture[0]['numerical_field'],17)
if __name__=='__main__':unittest.main()
