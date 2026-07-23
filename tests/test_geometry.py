import numpy as np

from rotating_field_three_body.geometry import edge_info, triangle_centers


def test_triangle_centers_preserve_shape():
    centers = triangle_centers(
        r12=1.3,
        r13=1.7,
        gamma_deg=72.0,
        psi_deg=31.0,
        alpha_deg=27.0,
    )
    info = edge_info(centers)
    assert np.isclose(info["distances"][0], 1.3, atol=1e-12)
    assert np.isclose(info["distances"][1], 1.7, atol=1e-12)
    v12 = centers[1] - centers[0]
    v13 = centers[2] - centers[0]
    angle = np.degrees(
        np.arccos(
            np.clip(np.dot(v12, v13) / np.linalg.norm(v12) / np.linalg.norm(v13), -1, 1)
        )
    )
    assert np.isclose(angle, 72.0, atol=1e-10)


def test_edge_info_translation_invariant():
    centers = triangle_centers(1.2, 1.6, 80, psi_deg=25, alpha_deg=15)
    shift = np.array([4.0, -3.0, 2.0])
    before = edge_info(centers)
    after = edge_info(centers + shift)
    np.testing.assert_allclose(before["distances"], after["distances"])
    np.testing.assert_allclose(before["beta_deg"], after["beta_deg"])
