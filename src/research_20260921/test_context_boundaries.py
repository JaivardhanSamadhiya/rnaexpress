"""Check failed-gate access and training-label isolation without new data."""
import unittest
from unittest.mock import patch
from .context_calibration import run,fit_predict
from .context_regularization_audit import choose_alpha
import numpy as np

class BoundaryTests(unittest.TestCase):
    def test_failed_gate_stops_before_any_outcome_loader(self):
        with patch('src.research_20260921.context_calibration.verify'), \
             patch('pathlib.Path.read_text',return_value='{"discovery_pass": false}'), \
             patch('src.research_20260921.context_calibration.read_outcomes') as loader:
            with self.assertRaises(PermissionError): run('confirmation')
            loader.assert_not_called()

    def test_unused_labels_cannot_change_fitted_predictions(self):
        rng=np.random.default_rng(124)
        x=rng.normal(size=(50,8));y=x[:,0]+rng.normal(size=50)
        train=np.arange(50)<20; predict=~train
        first=fit_predict(x,y,train,predict)
        changed=y.copy();changed[predict]=1e12
        second=fit_predict(x,changed,train,predict)
        np.testing.assert_array_equal(first,second)

    def test_hyperparameter_choice_ignores_noncalibration_labels(self):
        rng=np.random.default_rng(14);x=rng.normal(size=(60,7));y=x[:,0]+rng.normal(size=60)
        cal=np.arange(60)<32;groups=np.array([str(i//4) for i in range(60)])
        first=choose_alpha(x,y,cal,groups)
        y[~cal]=1e12
        self.assertEqual(first,choose_alpha(x,y,cal,groups))

if __name__=='__main__':unittest.main()
