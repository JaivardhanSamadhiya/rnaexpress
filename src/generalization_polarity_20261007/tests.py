"""Scoped synthetic invariants; no biological outcomes or model fits."""
import unittest
import hashlib
from .common import np, pd
from .routes import (
    CONFIGS, ENDPOINT_SIGNS, endpoint_sign, build_features, module, predict_model,
)
from .bootstrap import shared_bootstrap
from src.cross_assay_20260927.models import pair_indices, purge
from src.generalization_20261007.route_scaling import pair_rms


def toy_frame():
    records = []
    for endpoint, study, sign in [('projection','toy_P',1.),('nuclear_cytoplasmic','toy_N',-1.)]:
        for i in range(4):
            records.append({'intervention_id':study+str(i),'dataset':study,
                'biological_component':study,'parent_context_id':study+'_parent',
                'endpoint_class':endpoint,'measured_delta':sign*i,
                'parent_sequence':study+'_reference','mutant_sequence':study+'_variant'+str(i),
                'untouched_metadata':'sentinel'})
    frame = pd.DataFrame(records)
    base = np.zeros((len(frame),246))
    base[:,0] = np.tile(np.arange(4),2)
    base[:,1] = 3.
    return frame, build_features(frame,base)


class PolarityTests(unittest.TestCase):
    def test_endpoint_comes_only_from_supported_metadata(self):
        frame, matrix = toy_frame()
        altered = frame.copy()
        altered['dataset'] = 'same_source_for_both_endpoints'
        altered['measured_delta'] = np.nan
        np.testing.assert_array_equal(endpoint_sign(frame),endpoint_sign(altered))
        np.testing.assert_array_equal(build_features(altered,matrix[:,:246]),matrix)
        altered.loc[0,'endpoint_class'] = 'unverified_compartment'
        with self.assertRaises(ValueError): endpoint_sign(altered)
        with self.assertRaises(ValueError): endpoint_sign(frame.drop(columns='endpoint_class'))

    def test_no_mixed_endpoint_candidate_context(self):
        frame, _ = toy_frame()
        frame['parent_context_id'] = 'shared_invalid_context'
        with self.assertRaises(AssertionError): endpoint_sign(frame)

    def test_pair_roster_weights_and_rms_do_not_change(self):
        frame, matrix = toy_frame()
        altered = frame.copy()
        altered['measured_delta'] *= endpoint_sign(frame)
        a, b = pair_indices(frame), pair_indices(altered)
        for index in (0,1,3,4): np.testing.assert_array_equal(a[index],b[index])
        np.testing.assert_array_equal(b[2],a[2]*endpoint_sign(frame)[a[0]])
        np.testing.assert_array_equal(pair_rms(matrix[:,:246],a[0],a[1],a[3]),
                                      pair_rms(matrix[:,:246],b[0],b[1],b[3]))

    def test_fit_transforms_labels_without_mutating_metadata(self):
        frame, matrix = toy_frame()
        before, before_x = frame.copy(deep=True), matrix.copy()
        model = module('polarity').fit_model(frame,matrix,CONFIGS[1])
        pd.testing.assert_frame_equal(frame,before)
        np.testing.assert_array_equal(matrix,before_x)
        self.assertEqual(len(model['beta']),246)
        self.assertFalse(model['metadata_sign_is_learned_feature'])
        self.assertEqual(model['training_original_effect_sha256'],
            hashlib.sha256(frame.measured_delta.to_numpy(float).tobytes()).hexdigest())
        self.assertEqual(model['training_used_effect_sha256'],
            hashlib.sha256((frame.measured_delta.to_numpy(float)*endpoint_sign(frame)).tobytes()).hexdigest())
        self.assertFalse(model['active'][1])
        score = predict_model(model,matrix)
        self.assertTrue((np.diff(score[:4])>0).all())
        self.assertTrue((np.diff(score[4:])<0).all())

    def test_uniform_negative_orientation_is_score_equivalent(self):
        frame, matrix = toy_frame()
        frame = frame.iloc[4:].reset_index(drop=True)
        matrix = matrix[4:]
        a = module('unflipped').fit_model(frame,matrix,CONFIGS[1])
        b = module('polarity').fit_model(frame,matrix,CONFIGS[1])
        np.testing.assert_allclose(a['beta'],-np.array(b['beta']),atol=1e-12,rtol=0)
        np.testing.assert_array_equal(a['scale'],b['scale'])
        np.testing.assert_allclose(predict_model(a,matrix),predict_model(b,matrix),atol=1e-12,rtol=0)

    def test_projection_training_identical_known_nuclear_inference_negative(self):
        frame, matrix = toy_frame()
        training, train_x = frame.iloc[:4].reset_index(drop=True),matrix[:4]
        a = module('unflipped').fit_model(training,train_x,CONFIGS[1])
        b = module('polarity').fit_model(training,train_x,CONFIGS[1])
        np.testing.assert_array_equal(a['beta'],b['beta'])
        np.testing.assert_array_equal(predict_model(a,matrix[:4]),predict_model(b,matrix[:4]))
        np.testing.assert_array_equal(predict_model(a,matrix[4:]),-predict_model(b,matrix[4:]))

    def test_original_allele_component_purge(self):
        frame = pd.DataFrame({'biological_component':['shared','shared','unrelated'],
            'parent_sequence':['AAAA','AAAA','CCCC'],
            'mutant_sequence':['AAAT','AATA','CCCG']})
        selected = purge(frame,np.array([False,True,True]),np.array([True,False,False]))
        np.testing.assert_array_equal(selected,[False,False,True])

    def test_global_component_bootstrap_draw_shared_across_sources(self):
        a = pd.Series([1.,-1.],index=['component_A','component_B'])
        b = pd.Series([-1.,1.],index=['component_A','component_B'])
        result = shared_bootstrap({'first':a,'second':b},64,13)
        np.testing.assert_allclose(result,0.,atol=1e-15,rtol=0)


if __name__ == '__main__': unittest.main()
