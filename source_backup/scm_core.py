"""
scm_core.py

Validated matrix-SCM implementation for dielectric spheres in a rotating electric field.

This module contains only reusable numerical routines. Run scripts are separated into:
    run_00_pair_cache.py
    run_01_triplet_linear.py
    run_02_triplet_equilateral.py
    run_03_triplet_angle.py
    analyze_triplet_results.py

Physical model
--------------
The induced multipole amplitudes B are found from

    (I - R U) B = R A0,

where:
    A0  = regular multipole coefficients of the external potential on each sphere,
    U   = transfer matrix from outgoing multipoles of other spheres to regular
          multipoles on the target sphere,
    R   = diagonal response operator for a dielectric sphere.

The code uses a numerical projection on a Fibonacci sphere. This is the same matrix
form of the previously validated collocation SCM, but the transfer matrix U is built
once per geometry and l_max and then reused for all field orientations.

Conventions
-----------
- Spheres have radius a and diameter d=2a.
- External field rotates in the xy plane:

      E_k = E0 (cos theta_k, sin theta_k, 0),
      theta_k = 2*pi*k/n_orient.

- All distances are SI in the core functions.
- Energies are SI Joules.
- l=0 is included in the numerical basis for stability/completeness, but response_beta_l(0)=0.

Important caution
-----------------
The decomposition into particle-local energies U_i is a useful diagnostic, because the
implemented energy integral is accumulated over each particle surface. The physically
strict quantities for conclusions are the total excess energy and the non-pairwise
three-body contribution:

    Phi3   = U3 - 3 U1,
    Delta3 = Phi3 - sum_{i<j} phi_pair(r_ij).
"""

from __future__ import annotations

import json
import math
import os
import time
from dataclasses import asdict, dataclass
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np
from scipy.linalg import lstsq

try:
    from scipy.special import sph_harm_y

    def sph_harm_compat(m, l, theta_azimuth, phi_polar):
        """
        Compatibility wrapper.

        Old scipy.special.sph_harm:
            sph_harm_compat(m, l, theta, phi)
            theta = azimuth angle [0, 2pi]
            phi   = polar / colatitude angle [0, pi]

        New scipy.special.sph_harm_y:
            sph_harm_y(l, m, theta, phi)
            theta = polar / colatitude angle [0, pi]
            phi   = azimuth angle [0, 2pi]
        """
        return sph_harm_y(l, m, phi_polar, theta_azimuth)

except ImportError:
    from scipy.special import sph_harm

    def sph_harm_compat(m, l, theta_azimuth, phi_polar):
        return sph_harm(m, l, theta_azimuth, phi_polar)


@dataclass(frozen=True)
class SCMParams:
    """Physical and numerical parameters for SCM calculations."""

    eps1_r: float = 3.9
    eps2_r: float = 81.0
    a: float = 1.0e-6
    E0: float = 1.0e5
    eps0: float = 8.854187817e-12
    n_orient: int = 8
    n_quad: int = 8000

    @property
    def d(self) -> float:
        return 2.0 * self.a

    def to_json(self) -> str:
        data = asdict(self)
        data["d"] = self.d
        return json.dumps(data, ensure_ascii=False, indent=2)


def timestamp() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def rotating_field_k(k: int, params: SCMParams) -> np.ndarray:
    theta = 2.0 * np.pi * k / params.n_orient
    return np.array(
        [params.E0 * np.cos(theta), params.E0 * np.sin(theta), 0.0],
        dtype=float,
    )


def fibonacci_sphere_points(n_points: int) -> np.ndarray:
    """Approximately uniform points on a unit sphere."""
    points = np.zeros((n_points, 3), dtype=float)
    golden_angle = np.pi * (3.0 - np.sqrt(5.0))

    for k in range(n_points):
        z = 1.0 - 2.0 * (k + 0.5) / n_points
        rho = np.sqrt(max(0.0, 1.0 - z * z))
        phi = golden_angle * k
        points[k, 0] = rho * np.cos(phi)
        points[k, 1] = rho * np.sin(phi)
        points[k, 2] = z

    return points


def cart_to_angles(vecs: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Convert Cartesian vectors to scipy spherical angles theta=azimuth, phi=polar."""
    vecs = np.asarray(vecs, dtype=float)
    x = vecs[:, 0]
    y = vecs[:, 1]
    z = vecs[:, 2]

    theta = np.mod(np.arctan2(y, x), 2.0 * np.pi)
    r = np.linalg.norm(vecs, axis=1)
    if np.any(r == 0.0):
        raise ValueError("Zero vector encountered in cart_to_angles.")
    cos_phi = np.clip(z / r, -1.0, 1.0)
    phi = np.arccos(cos_phi)
    return theta, phi


def lm_list(lmax: int, include_l0: bool = True) -> List[Tuple[int, int]]:
    out: List[Tuple[int, int]] = []
    l_start = 0 if include_l0 else 1
    for l in range(l_start, int(lmax) + 1):
        for m in range(-l, l + 1):
            out.append((l, m))
    return out


def build_Y_matrix(normals: np.ndarray, lmax: int, include_l0: bool = True) -> Tuple[np.ndarray, List[Tuple[int, int]]]:
    theta, phi = cart_to_angles(normals)
    lms = lm_list(lmax, include_l0=include_l0)
    Y = np.zeros((normals.shape[0], len(lms)), dtype=complex)
    for col, (l, m) in enumerate(lms):
        Y[:, col] = sph_harm_compat(m, l, theta, phi)
    return Y, lms


def response_beta_l(l: int, params: SCMParams) -> complex:
    """
    Surface-amplitude response for a dielectric sphere:
        B_lm = beta_l A_lm.
    """
    if l == 0:
        return 0.0
    return (
        l * (params.eps2_r - params.eps1_r)
        / (l * params.eps1_r + (l + 1.0) * params.eps2_r)
    )


def build_response_diag(lms: Sequence[Tuple[int, int]], n_particles: int, params: SCMParams) -> np.ndarray:
    beta_one = np.array([response_beta_l(l, params) for l, _m in lms], dtype=complex)
    return np.tile(beta_one, n_particles)


def external_potential_at_points(points: np.ndarray, E_vec: np.ndarray) -> np.ndarray:
    return -points @ E_vec


def outgoing_basis_at_points(
    points: np.ndarray,
    center: np.ndarray,
    lms: Sequence[Tuple[int, int]],
    radius: float,
) -> np.ndarray:
    """
    Matrix G[p, q] such that
        phi_reac(points_p) = sum_q G[p,q] B_q.

    Stored B_q is the surface amplitude:
        phi_reac(R,Omega) = B_lm * (a/R)^(l+1) Y_lm(Omega).
    """
    Rvec = points - center[None, :]
    R = np.linalg.norm(Rvec, axis=1)
    if np.any(R <= 0.0):
        raise ValueError("Evaluation point coincides with a source center.")
    dirs = Rvec / R[:, None]
    theta, phi = cart_to_angles(dirs)

    G = np.zeros((points.shape[0], len(lms)), dtype=complex)
    for col, (l, m) in enumerate(lms):
        if l == 0:
            continue
        Ylm = sph_harm_compat(m, l, theta, phi)
        G[:, col] = (radius / R) ** (l + 1) * Ylm
    return G


def radial_derivatives_on_own_surface(
    A_coeffs: np.ndarray,
    B_coeffs: np.ndarray,
    Y_surface: np.ndarray,
    lms: Sequence[Tuple[int, int]],
    radius: float,
) -> Tuple[np.ndarray, np.ndarray]:
    q_out = np.zeros(Y_surface.shape[0], dtype=complex)
    q_in = np.zeros(Y_surface.shape[0], dtype=complex)

    for idx, (l, _m) in enumerate(lms):
        if l == 0:
            continue
        A_lm = A_coeffs[idx]
        B_lm = B_coeffs[idx]
        Y_lm = Y_surface[:, idx]
        q_out += ((l * A_lm - (l + 1.0) * B_lm) / radius) * Y_lm
        q_in += (l * (A_lm + B_lm) / radius) * Y_lm
    return q_in, q_out


def sigma_bound_from_q(q_in: np.ndarray, q_out: np.ndarray, params: SCMParams) -> np.ndarray:
    return -params.eps0 * ((params.eps1_r - 1.0) * q_in - (params.eps2_r - 1.0) * q_out)


def analytic_single_sphere_bem_like_energy(E_vec: np.ndarray, params: SCMParams) -> float:
    """Analytic single-sphere energy in the same convention used in the validated code."""
    E2 = float(np.dot(E_vec, E_vec))
    K = (params.eps1_r - params.eps2_r) / (params.eps1_r + 2.0 * params.eps2_r)
    gamma = 3.0 * params.eps0 * (params.eps1_r - params.eps2_r) / (params.eps1_r + 2.0 * params.eps2_r)
    return (2.0 * np.pi / 3.0) * gamma * K * params.a**3 * E2


class MatrixSCMSystem:
    """
    Preassembled SCM system for one geometry and one l_max.

    Geometry-dependent transfer matrix U is built once. For each field orientation,
    only A0, linear solve, and energy integration are performed.
    """

    def __init__(self, centers: np.ndarray, lmax: int, normals: np.ndarray, params: SCMParams):
        self.centers = np.asarray(centers, dtype=float)
        self.lmax = int(lmax)
        self.normals = np.asarray(normals, dtype=float)
        self.params = params
        self.radius = params.a
        self.n_particles = self.centers.shape[0]

        self.V_surface, self.lms = build_Y_matrix(self.normals, self.lmax, include_l0=True)
        self.Y_surface = self.V_surface
        self.M = len(self.lms)
        self.Ndof = self.n_particles * self.M
        self.beta = build_response_diag(self.lms, self.n_particles, self.params)
        self.U = self._build_transfer_matrix_U()
        self.LHS = np.eye(self.Ndof, dtype=complex) - self.beta[:, None] * self.U

    def _build_transfer_matrix_U(self) -> np.ndarray:
        U = np.zeros((self.Ndof, self.Ndof), dtype=complex)

        for i in range(self.n_particles):
            surf_i = self.centers[i][None, :] + self.radius * self.normals
            row = slice(i * self.M, (i + 1) * self.M)

            for j in range(self.n_particles):
                if i == j:
                    continue
                col = slice(j * self.M, (j + 1) * self.M)
                G_ij = outgoing_basis_at_points(
                    points=surf_i,
                    center=self.centers[j],
                    lms=self.lms,
                    radius=self.radius,
                )
                Aproj_ij, *_ = lstsq(self.V_surface, G_ij)
                U[row, col] = Aproj_ij
        return U

    def build_external_A0(self, E_vec: np.ndarray) -> np.ndarray:
        A0 = np.zeros(self.Ndof, dtype=complex)
        for i in range(self.n_particles):
            surf_i = self.centers[i][None, :] + self.radius * self.normals
            phi_ext_i = external_potential_at_points(surf_i, E_vec).astype(complex)
            A_i, *_ = lstsq(self.V_surface, phi_ext_i)
            A0[i * self.M : (i + 1) * self.M] = A_i
        return A0

    def solve_coefficients(self, E_vec: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        A0 = self.build_external_A0(E_vec)
        RHS = self.beta * A0
        B = np.linalg.solve(self.LHS, RHS)
        A = A0 + self.U @ B
        return A.reshape(self.n_particles, self.M), B.reshape(self.n_particles, self.M)

    def energy_parts(self, E_vec: np.ndarray) -> Tuple[float, np.ndarray]:
        A_all, B_all = self.solve_coefficients(E_vec)
        n_points = self.normals.shape[0]
        dS = 4.0 * np.pi * self.radius**2 / n_points
        U_parts = np.zeros(self.n_particles, dtype=float)

        for i in range(self.n_particles):
            surf_i = self.centers[i][None, :] + self.radius * self.normals
            q_in_i, q_out_i = radial_derivatives_on_own_surface(
                A_coeffs=A_all[i],
                B_coeffs=B_all[i],
                Y_surface=self.Y_surface,
                lms=self.lms,
                radius=self.radius,
            )
            sigma_i = sigma_bound_from_q(q_in_i, q_out_i, self.params)

            phi_reac_i = np.zeros(n_points, dtype=complex)
            for j in range(self.n_particles):
                G_ji_on_i = outgoing_basis_at_points(
                    points=surf_i,
                    center=self.centers[j],
                    lms=self.lms,
                    radius=self.radius,
                )
                phi_reac_i += G_ji_on_i @ B_all[j]

            U_i = 0.5 * np.sum(sigma_i * phi_reac_i) * dS
            U_parts[i] = float(np.real(U_i))

        return float(np.sum(U_parts)), U_parts


def centers_pair(distance: float) -> np.ndarray:
    r = float(distance)
    return np.array([[-0.5 * r, 0.0, 0.0], [+0.5 * r, 0.0, 0.0]], dtype=float)


def centers_linear_triplet(r_center_neighbor: float) -> np.ndarray:
    r = float(r_center_neighbor)
    return np.array([[-r, 0.0, 0.0], [0.0, 0.0, 0.0], [+r, 0.0, 0.0]], dtype=float)


def centers_equilateral(edge: float) -> np.ndarray:
    r = float(edge)
    return np.array(
        [
            [-0.5 * r, -np.sqrt(3.0) * r / 6.0, 0.0],
            [+0.5 * r, -np.sqrt(3.0) * r / 6.0, 0.0],
            [0.0, +np.sqrt(3.0) * r / 3.0, 0.0],
        ],
        dtype=float,
    )


def centers_angle_triplet(r_center_neighbor: float, gamma_deg: float) -> np.ndarray:
    r = float(r_center_neighbor)
    gamma = np.deg2rad(float(gamma_deg))
    return np.array(
        [
            [0.0, 0.0, 0.0],
            [r, 0.0, 0.0],
            [r * np.cos(gamma), r * np.sin(gamma), 0.0],
        ],
        dtype=float,
    )


def pair_distances(centers: np.ndarray) -> np.ndarray:
    centers = np.asarray(centers, dtype=float)
    out = []
    for i in range(centers.shape[0]):
        for j in range(i + 1, centers.shape[0]):
            out.append(float(np.linalg.norm(centers[i] - centers[j])))
    return np.array(out, dtype=float)


def unique_sorted(values: Iterable[float], ndigits: int = 12) -> np.ndarray:
    rounded = sorted({round(float(v), ndigits) for v in values})
    return np.array(rounded, dtype=float)


def lookup_pair_energy(distance: float, pair_distances_arr: np.ndarray, phi_pair_avg_lr: np.ndarray, il: int, tol: float = 1e-9) -> float:
    """Find cached pair energy for one lmax index and one physical distance."""
    distance = float(distance)
    idx = int(np.argmin(np.abs(pair_distances_arr - distance)))
    scale = max(1.0, abs(distance))
    if abs(pair_distances_arr[idx] - distance) > tol * scale:
        raise KeyError(
            f"Pair distance {distance:.16e} not found in cache. "
            f"Nearest is {pair_distances_arr[idx]:.16e}."
        )
    return float(phi_pair_avg_lr[il, idx])


def save_json(path: str, data: Dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def print_header(title: str) -> None:
    print("\n" + "=" * 88)
    print(title)
    print("=" * 88)
