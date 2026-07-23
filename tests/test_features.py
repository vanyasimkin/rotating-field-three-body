import numpy as np

from rotating_field_three_body.features import build_invariant_features


def test_feature_count_and_permutation_invariance():
    r = np.array([[1.2, 1.7, 2.1], [1.4, 1.6, 2.3]])
    beta = np.array([[10.0, 30.0, 55.0], [5.0, 70.0, 25.0]])
    x1, names1, _ = build_invariant_features(r, beta)
    permutation = [2, 0, 1]
    x2, names2, _ = build_invariant_features(r[:, permutation], beta[:, permutation])
    assert x1.shape == (2, 120)
    assert names1 == names2
    np.testing.assert_allclose(x1, x2, rtol=0, atol=1e-12)
