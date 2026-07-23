"""Physically constrained interpolation for the SCM pair map.

The legacy implementation interpolated phi_pair linearly in (r, beta).
That is poorly conditioned for extracting the much smaller triplet residual
Delta3 = Phi3 - sum(phi_pair), especially in the far field.

This module instead interpolates

    g(s, q) = s**3 * phi_pair(s, beta),
    s = r/d,
    q = sin(beta)**2,

on the coordinates

    x = 1/s,  q = sin(beta)**2.

The transformation is motivated by the rotating-dipole far field:
phi_pair ~ A(beta) / s**3, while A(beta) is linear in sin(beta)**2.
No extrapolation is performed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable

import numpy as np

Array = np.ndarray


def _as_scalar(value, name: str) -> float:
    array = np.asarray(value, dtype=float)
    if array.size != 1:
        raise ValueError(f"{name} must be scalar; got shape {array.shape}.")
    return float(array.reshape(()))


def load_pair_map(path: Path | str) -> Dict[str, Array | float | str]:
    """Load a pair-map NPZ in a form accepted by this module."""
    path = Path(path)
    with np.load(path, allow_pickle=False) as data:
        required = {"r_over_d", "beta_deg", "phi_pair_avg_rb"}
        missing = required.difference(data.files)
        if missing:
            raise KeyError(f"Pair map {path} is missing keys: {sorted(missing)}")

        r_over_d = np.asarray(data["r_over_d"], dtype=float)
        beta_deg = np.asarray(data["beta_deg"], dtype=float)
        phi = np.asarray(data["phi_pair_avg_rb"], dtype=float)

        if phi.shape != (len(r_over_d), len(beta_deg)):
            raise ValueError(
                "phi_pair_avg_rb has shape "
                f"{phi.shape}, expected {(len(r_over_d), len(beta_deg))}."
            )
        if not np.all(np.diff(r_over_d) > 0):
            raise ValueError("r_over_d must be strictly increasing.")
        if not np.all(np.diff(beta_deg) > 0):
            raise ValueError("beta_deg must be strictly increasing.")
        if not np.all(np.isfinite(phi)):
            raise ValueError("Pair map contains unfinished/non-finite values.")

        if "d" in data.files:
            diameter_m = _as_scalar(data["d"], "d")
        elif "r" in data.files:
            r_m = np.asarray(data["r"], dtype=float)
            diameter_m = float(np.median(r_m / r_over_d))
        else:
            diameter_m = 1.0

        output: Dict[str, Array | float | str] = {
            "path": str(path),
            "r_over_d": r_over_d,
            "r": r_over_d * diameter_m,
            "beta_deg": beta_deg,
            "phi_pair_avg_rb": phi,
            "d": diameter_m,
        }
        if "U_single_k" in data.files:
            output["U_single_k"] = np.asarray(data["U_single_k"], dtype=float)
        return output


def _bilinear(
    axis0: Array,
    axis1: Array,
    values: Array,
    query0: Array,
    query1: Array,
) -> Array:
    """Vectorized bilinear interpolation on strictly increasing axes."""
    axis0 = np.asarray(axis0, dtype=float)
    axis1 = np.asarray(axis1, dtype=float)
    values = np.asarray(values, dtype=float)
    q0, q1 = np.broadcast_arrays(
        np.asarray(query0, dtype=float), np.asarray(query1, dtype=float)
    )
    shape = q0.shape
    q0f = q0.ravel()
    q1f = q1.ravel()

    tol0 = 1e-12 * max(1.0, abs(axis0[0]), abs(axis0[-1]))
    tol1 = 1e-12 * max(1.0, abs(axis1[0]), abs(axis1[-1]))
    if np.any(q0f < axis0[0] - tol0) or np.any(q0f > axis0[-1] + tol0):
        lo = float(np.min(q0f))
        hi = float(np.max(q0f))
        raise ValueError(
            f"First interpolation coordinate [{lo:.8g}, {hi:.8g}] is outside "
            f"[{axis0[0]:.8g}, {axis0[-1]:.8g}]."
        )
    if np.any(q1f < axis1[0] - tol1) or np.any(q1f > axis1[-1] + tol1):
        lo = float(np.min(q1f))
        hi = float(np.max(q1f))
        raise ValueError(
            f"Second interpolation coordinate [{lo:.8g}, {hi:.8g}] is outside "
            f"[{axis1[0]:.8g}, {axis1[-1]:.8g}]."
        )

    q0f = np.clip(q0f, axis0[0], axis0[-1])
    q1f = np.clip(q1f, axis1[0], axis1[-1])

    i1 = np.searchsorted(axis0, q0f, side="right")
    j1 = np.searchsorted(axis1, q1f, side="right")
    i1 = np.clip(i1, 1, len(axis0) - 1)
    j1 = np.clip(j1, 1, len(axis1) - 1)
    i0 = i1 - 1
    j0 = j1 - 1

    x0, x1 = axis0[i0], axis0[i1]
    y0, y1 = axis1[j0], axis1[j1]
    tx = np.divide(q0f - x0, x1 - x0, out=np.zeros_like(q0f), where=x1 != x0)
    ty = np.divide(q1f - y0, y1 - y0, out=np.zeros_like(q1f), where=y1 != y0)

    f00 = values[i0, j0]
    f10 = values[i1, j0]
    f01 = values[i0, j1]
    f11 = values[i1, j1]
    result = (
        (1.0 - tx) * (1.0 - ty) * f00
        + tx * (1.0 - ty) * f10
        + (1.0 - tx) * ty * f01
        + tx * ty * f11
    )
    return result.reshape(shape)


def interpolate_pair_phi_array(
    r: Array | float,
    beta_deg: Array | float,
    pair_map: Dict[str, Array | float | str],
    *,
    input_is_over_d: bool = False,
    method: str = "physical",
) -> Array:
    """Interpolate pair energies for broadcast-compatible arrays.

    Parameters
    ----------
    r:
        Physical distance in metres, unless ``input_is_over_d=True``.
    beta_deg:
        Edge inclination measured from the field-rotation plane.
    method:
        ``physical``: interpolate s^3 phi on (1/s, sin^2 beta).
        ``legacy``: reproduce bilinear interpolation on (s, beta).
    """
    rr, bb = np.broadcast_arrays(
        np.asarray(r, dtype=float), np.asarray(beta_deg, dtype=float)
    )
    if input_is_over_d:
        s = rr
    else:
        diameter = float(pair_map["d"])
        if diameter <= 0:
            raise ValueError("Pair-map diameter must be positive.")
        s = rr / diameter

    beta = np.abs(bb)
    if np.any(beta > 90.0 + 1e-10):
        raise ValueError("beta_deg must lie in [0, 90] degrees.")
    beta = np.clip(beta, 0.0, 90.0)

    r_grid = np.asarray(pair_map["r_over_d"], dtype=float)
    b_grid = np.asarray(pair_map["beta_deg"], dtype=float)
    phi = np.asarray(pair_map["phi_pair_avg_rb"], dtype=float)

    method = method.lower().strip()
    if method == "legacy":
        return _bilinear(r_grid, b_grid, phi, s, beta)
    if method != "physical":
        raise ValueError(f"Unknown interpolation method: {method!r}")

    # x increases after reversing the original increasing-r grid.
    x_grid = (1.0 / r_grid)[::-1]
    q_grid = np.sin(np.deg2rad(b_grid)) ** 2
    scaled = phi * r_grid[:, None] ** 3
    scaled = scaled[::-1, :]

    x = 1.0 / s
    q = np.sin(np.deg2rad(beta)) ** 2
    g = _bilinear(x_grid, q_grid, scaled, x, q)
    return g / s**3


def interpolate_pair_phi(
    r: float,
    beta_deg: float,
    pair_map: Dict[str, Array | float | str],
    *,
    input_is_over_d: bool = False,
    method: str = "physical",
) -> float:
    return float(
        np.asarray(
            interpolate_pair_phi_array(
                r,
                beta_deg,
                pair_map,
                input_is_over_d=input_is_over_d,
                method=method,
            )
        ).reshape(())
    )


def pairwise_energy_from_edges(
    edge_distances: Iterable[float] | Array,
    edge_betas_deg: Iterable[float] | Array,
    pair_map: Dict[str, Array | float | str],
    *,
    input_is_over_d: bool = False,
    method: str = "physical",
) -> float:
    distances = np.asarray(edge_distances, dtype=float)
    betas = np.asarray(edge_betas_deg, dtype=float)
    if distances.shape != betas.shape:
        raise ValueError(
            f"Distance and beta arrays must have equal shapes; got "
            f"{distances.shape} and {betas.shape}."
        )
    values = interpolate_pair_phi_array(
        distances,
        betas,
        pair_map,
        input_is_over_d=input_is_over_d,
        method=method,
    )
    return float(np.sum(values))
