"""
scm3d_geometry.py

Geometry utilities for orientation-dependent SCM maps.

Coordinate conventions
----------------------
The external electric field rotates in the xy plane. The normal to this plane is
z. Therefore the orientation of any pair edge is characterized by

    beta = asin(|e_ij · e_z|),

where e_ij is the unit vector along the pair edge. beta=0 means the edge lies in
xy; beta=90 deg means the edge is parallel to z.

Triangle parameters
-------------------
A general central-particle triangle is defined by:

    r1 = (0, 0, 0),
    r2 = r12 (cos alpha, sin alpha, 0),
    r3 = r13 (cos(alpha + gamma), sin(alpha + gamma), 0),

followed by a rotation of the whole triangle plane around the x axis by psi.

Here:
    gamma = opening angle between particles 2 and 3 as seen from particle 1,
    psi   = tilt of the triangle plane relative to the field-rotation plane,
    alpha = azimuthal orientation of the triangle within its own initial plane.
"""

from __future__ import annotations

import math
from typing import Dict, Tuple

import numpy as np


def rotation_matrix_x(angle_deg: float) -> np.ndarray:
    a = math.radians(float(angle_deg))
    c = math.cos(a)
    s = math.sin(a)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]], dtype=float)


def pair_orientation_vector(beta_deg: float) -> np.ndarray:
    """Unit vector making beta angle with the xy plane."""
    b = math.radians(float(beta_deg))
    return np.array([math.cos(b), 0.0, math.sin(b)], dtype=float)


def pair_oriented_centers(distance: float, beta_deg: float) -> np.ndarray:
    """Two sphere centers with edge length distance and orientation beta."""
    n = pair_orientation_vector(beta_deg)
    r = float(distance)
    return np.array([-0.5 * r * n, +0.5 * r * n], dtype=float)


def triangle_centers(
    r12: float,
    r13: float,
    gamma_deg: float,
    psi_deg: float = 0.0,
    alpha_deg: float = 0.0,
) -> np.ndarray:
    """General central-particle triangle centers."""
    r12 = float(r12)
    r13 = float(r13)
    gamma = math.radians(float(gamma_deg))
    alpha = math.radians(float(alpha_deg))

    c2 = np.array([r12 * math.cos(alpha), r12 * math.sin(alpha), 0.0], dtype=float)
    c3 = np.array([r13 * math.cos(alpha + gamma), r13 * math.sin(alpha + gamma), 0.0], dtype=float)
    centers0 = np.array([[0.0, 0.0, 0.0], c2, c3], dtype=float)

    R = rotation_matrix_x(psi_deg)
    return centers0 @ R.T


def edge_info(centers: np.ndarray) -> Dict[str, np.ndarray]:
    """Return pair distances and beta angles for edges 12, 13, 23.

    Output keys:
        pairs      : string labels ['12', '13', '23']
        distances  : physical distances in the same units as centers
        beta_deg   : edge angles relative to the xy plane
    """
    centers = np.asarray(centers, dtype=float)
    pairs = [(0, 1, "12"), (0, 2, "13"), (1, 2, "23")]
    distances = []
    betas = []
    labels = []

    ez = np.array([0.0, 0.0, 1.0], dtype=float)
    for i, j, label in pairs:
        v = centers[j] - centers[i]
        dist = float(np.linalg.norm(v))
        if dist <= 0.0:
            raise ValueError(f"Degenerate edge {label}: zero distance.")
        e = v / dist
        beta = math.degrees(math.asin(min(1.0, abs(float(np.dot(e, ez))))))
        distances.append(dist)
        betas.append(beta)
        labels.append(label)

    return {
        "pairs": np.array(labels, dtype="U2"),
        "distances": np.array(distances, dtype=float),
        "beta_deg": np.array(betas, dtype=float),
    }


def r23_from_r12_r13_gamma(r12: float, r13: float, gamma_deg: float) -> float:
    gamma = math.radians(float(gamma_deg))
    return math.sqrt(float(r12) ** 2 + float(r13) ** 2 - 2.0 * float(r12) * float(r13) * math.cos(gamma))


def min_surface_gap_over_d(centers: np.ndarray, d: float) -> float:
    """Minimum center-to-center separation divided by particle diameter d."""
    info = edge_info(centers)
    return float(np.min(info["distances"]) / float(d))
