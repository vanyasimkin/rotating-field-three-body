import numpy as np

from rotating_field_three_body.pair_map import (
    interpolate_pair_phi,
    interpolate_pair_phi_array,
)


def synthetic_map():
    r = np.array([1.0, 2.0, 4.0])
    beta = np.array([0.0, 45.0, 90.0])
    q = np.sin(np.deg2rad(beta)) ** 2
    amplitude = 2.0 + 3.0 * q
    phi = amplitude[None, :] / r[:, None] ** 3
    return {
        "r_over_d": r,
        "beta_deg": beta,
        "phi_pair_avg_rb": phi,
        "d": 2.0,
    }


def test_physical_interpolator_exact_at_nodes():
    pair_map = synthetic_map()
    for i, r in enumerate(pair_map["r_over_d"]):
        for j, beta in enumerate(pair_map["beta_deg"]):
            value = interpolate_pair_phi(
                r, beta, pair_map, input_is_over_d=True, method="physical"
            )
            assert np.isclose(value, pair_map["phi_pair_avg_rb"][i, j])


def test_physical_interpolator_broadcasts():
    pair_map = synthetic_map()
    values = interpolate_pair_phi_array(
        np.array([1.5, 3.0]),
        np.array([10.0, 70.0]),
        pair_map,
        input_is_over_d=True,
    )
    assert values.shape == (2,)
    assert np.all(np.isfinite(values))
