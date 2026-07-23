import numpy as np

from rotating_field_three_body.api import triplet_domain_report
from rotating_field_three_body.surrogate import (
    predict_triplets_J,
    triplet_edges_batch,
)


class ConstantModel:
    def __init__(self, value):
        self.value = float(value)

    def predict(self, x):
        return np.full(len(x), self.value)


def payload():
    return {
        "feature_mode": "invariant",
        "global_model": ConstantModel(2.0),
        "compact_model": ConstantModel(3.0),
        "compact_cutoff": 1.8,
        "target_scale": 1e21,
        "feature_names": [],
    }


def test_batch_prediction_uses_compact_branch():
    d = 2.0
    centers = np.array(
        [
            [[0, 0, 0], [1.4 * d, 0, 0], [0, 1.5 * d, 0]],
            [[0, 0, 0], [2.2 * d, 0, 0], [0, 2.3 * d, 0]],
        ],
        dtype=float,
    )
    values, _ = predict_triplets_J(centers, d, payload(), check_domain=True)
    np.testing.assert_allclose(values, np.array([3.0e-21, 2.0e-21]))


def test_domain_report_non_raising():
    report = triplet_domain_report(np.array([[1.2, 2.0, 3.0], [1.0, 2.0, 3.0]]))
    assert report["valid_mask"].tolist() == [True, False]
    assert report["reasons"][1]
