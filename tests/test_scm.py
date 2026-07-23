import numpy as np

from rotating_field_three_body.scm import (
    MatrixSCMSystem,
    SCMParams,
    analytic_single_sphere_bem_like_energy,
    fibonacci_sphere_points,
    rotating_field_k,
)


def test_single_sphere_scm_is_finite_and_close_to_analytic_at_smoke_resolution():
    params = SCMParams(n_orient=2, n_quad=120)
    normals = fibonacci_sphere_points(params.n_quad)
    system = MatrixSCMSystem(
        centers=np.zeros((1, 3)), lmax=1, normals=normals, params=params
    )
    field = rotating_field_k(0, params)
    numerical, _ = system.energy_parts(field)
    analytic = analytic_single_sphere_bem_like_energy(field, params)
    assert np.isfinite(numerical)
    assert np.isfinite(analytic)
    assert np.isclose(numerical, analytic, rtol=0.08)
