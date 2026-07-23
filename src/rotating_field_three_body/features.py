#!/usr/bin/env python3
"""
Exact permutation-invariant feature construction used by the v2 Delta3
surrogate.

The feature order intentionally matches
make_delta3_surrogate_parity_v2.py in feature_mode="invariant".
The evaluator verifies the feature names stored in the joblib model before
making predictions.
"""

from __future__ import annotations

from itertools import combinations

import numpy as np


def _append(features, names, values, name):
    values = np.asarray(values, dtype=float)
    if values.ndim != 1:
        raise ValueError(
            f"Feature {name!r} must be one-dimensional, got {values.shape}."
        )
    features.append(values)
    names.append(name)


def _sum_pair_products(values):
    out = np.zeros(values.shape[0], dtype=float)
    for i, j in combinations(range(3), 2):
        out += values[:, i] * values[:, j]
    return out


def _sum_cross_pair_products(a, b):
    out = np.zeros(a.shape[0], dtype=float)
    for i, j in combinations(range(3), 2):
        out += a[:, i] * b[:, j] + a[:, j] * b[:, i]
    return out


def build_invariant_features(edge_r_over_d, edge_beta_deg):
    """
    Parameters
    ----------
    edge_r_over_d : array, shape (n_samples, 3)
        Edge lengths for edges 12, 13 and 23 in units of particle diameter.
    edge_beta_deg : array, shape (n_samples, 3)
        Inclination of each edge relative to the field-rotation plane.

    Returns
    -------
    X : array, shape (n_samples, 120)
    names : list[str]
    metadata : dict[str, array]
    """
    R = np.asarray(edge_r_over_d, dtype=float)
    beta_deg = np.asarray(edge_beta_deg, dtype=float)

    if R.ndim != 2 or R.shape[1] != 3:
        raise ValueError(f"edge_r_over_d must have shape (N, 3), got {R.shape}.")
    if beta_deg.shape != R.shape:
        raise ValueError(
            f"edge_beta_deg must have shape {R.shape}, got {beta_deg.shape}."
        )
    if not np.all(np.isfinite(R)) or not np.all(np.isfinite(beta_deg)):
        raise ValueError("Features contain NaN or infinite values.")
    if np.any(R <= 0.0):
        raise ValueError("All edge distances must be positive.")

    beta = np.deg2rad(beta_deg)
    rho = 1.0 / R

    # beta is measured from the xy field-rotation plane.
    G = 1.0 - 1.5 * np.cos(beta) ** 2
    z2 = np.sin(beta) ** 2

    features = []
    names = []

    # Canonically sorted edges. Orientation factors remain paired with edges.
    sort_idx = np.argsort(R, axis=1)
    Rsort = np.take_along_axis(R, sort_idx, axis=1)
    rhosort = 1.0 / Rsort
    Gsort = np.take_along_axis(G, sort_idx, axis=1)
    z2sort = np.take_along_axis(z2, sort_idx, axis=1)

    for edge_id, label in enumerate(("min", "mid", "max")):
        _append(features, names, Rsort[:, edge_id], f"R_{label}")
        _append(features, names, rhosort[:, edge_id], f"rho_{label}")
        _append(features, names, Gsort[:, edge_id], f"G_{label}")
        _append(features, names, z2sort[:, edge_id], f"z2_{label}")
        _append(
            features,
            names,
            Gsort[:, edge_id] * rhosort[:, edge_id] ** 3,
            f"G_rho3_{label}",
        )
        _append(
            features,
            names,
            Gsort[:, edge_id] * rhosort[:, edge_id] ** 6,
            f"G_rho6_{label}",
        )

    Rmin, Rmid, Rmax = Rsort[:, 0], Rsort[:, 1], Rsort[:, 2]
    perimeter = np.sum(R, axis=1)
    aspect = Rmax / Rmin
    asymmetry = (Rmax - Rmin) / np.maximum(Rmid, 1e-12)

    a, b, c = R[:, 0], R[:, 1], R[:, 2]
    semiperimeter = 0.5 * (a + b + c)
    area = np.sqrt(
        np.maximum(
            semiperimeter
            * (semiperimeter - a)
            * (semiperimeter - b)
            * (semiperimeter - c),
            0.0,
        )
    )
    area_norm = area / np.maximum(perimeter**2, 1e-12)
    compactness = 4.0 * np.sqrt(3.0) * area / np.maximum(
        a * a + b * b + c * c, 1e-12
    )

    for values, label in [
        (perimeter, "perimeter"),
        (aspect, "aspect"),
        (asymmetry, "asymmetry"),
        (area, "area"),
        (area_norm, "area_norm"),
        (compactness, "triangle_compactness"),
    ]:
        _append(features, names, values, label)

    powers = [1, 2, 3, 4, 5, 6, 7, 8, 10, 12]
    for p in powers:
        rp = rho**p
        grp = G * rp
        zrp = z2 * rp

        _append(features, names, np.sum(rp, axis=1), f"sum_rho_{p}")
        _append(features, names, np.sum(grp, axis=1), f"sum_G_rho_{p}")
        _append(features, names, np.sum(G**2 * rp, axis=1), f"sum_G2_rho_{p}")
        _append(features, names, np.sum(zrp, axis=1), f"sum_z2_rho_{p}")
        _append(features, names, _sum_pair_products(rp), f"pair_rho_{p}")
        _append(features, names, _sum_pair_products(grp), f"pair_Grho_{p}")
        _append(features, names, np.prod(rp, axis=1), f"triple_rho_{p}")

    for p, q in [(2, 3), (3, 4), (3, 6), (4, 6), (4, 8), (6, 8)]:
        rp = rho**p
        rq = rho**q
        _append(
            features,
            names,
            _sum_cross_pair_products(rp, rq),
            f"pair_cross_rho_{p}_{q}",
        )
        _append(
            features,
            names,
            _sum_cross_pair_products(G * rp, G * rq),
            f"pair_cross_Grho_{p}_{q}",
        )
        _append(
            features,
            names,
            _sum_cross_pair_products(G * rp, rq),
            f"pair_cross_mix_{p}_{q}",
        )

    for angular_values, label in [(G, "G"), (z2, "z2")]:
        _append(features, names, np.sum(angular_values, axis=1), f"sum_{label}")
        _append(
            features,
            names,
            np.sum(angular_values**2, axis=1),
            f"sum_{label}2",
        )
        _append(
            features,
            names,
            _sum_pair_products(angular_values),
            f"pair_{label}",
        )
        _append(
            features,
            names,
            np.prod(angular_values, axis=1),
            f"triple_{label}",
        )

    X = np.column_stack(features)
    if X.shape[1] != 120:
        raise RuntimeError(
            f"Expected 120 invariant features, constructed {X.shape[1]}."
        )

    metadata = {
        "Rmin": Rmin,
        "Rmid": Rmid,
        "Rmax": Rmax,
    }
    return X, names, metadata
