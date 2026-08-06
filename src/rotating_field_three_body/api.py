"""High-level public API built from the validated project routines.

The functions in this module are new convenience wrappers. They do not replace
or alter the numerical definitions implemented in :mod:`.scm`, :mod:`.pair_map`,
and :mod:`.surrogate`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping

import numpy as np

from .config import DEFAULT_LMAX, DEFAULT_PARAMS, ENERGY_UNIT_J
from .geometry import edge_info
from .pair_map import load_pair_map, pairwise_energy_from_edges
from .scm import (
    MatrixSCMSystem,
    SCMParams,
    fibonacci_sphere_points,
    rotating_field_k,
)
from .surrogate import (
    DEFAULT_DOMAIN,
    enumerate_cluster_triplets,
    load_surrogate,
    pair_edges_from_centers,
    predict_cluster_triplet_sum_J,
    predict_triplets_J,
    predict_triplets_scaled,
    triplet_edges_batch,
)


def _centers_array(centers: np.ndarray, *, n_particles: int | None = None) -> np.ndarray:
    array = np.asarray(centers, dtype=float)
    if array.ndim != 2 or array.shape[1] != 3:
        raise ValueError(f"centers must have shape (N, 3), got {array.shape}.")
    if n_particles is not None and len(array) != n_particles:
        raise ValueError(
            f"Expected {n_particles} particles, received {len(array)}."
        )
    if not np.all(np.isfinite(array)):
        raise ValueError("centers contain NaN or infinite values.")
    return array


def _pair_map_payload(pair_map: Mapping[str, Any] | Path | str) -> Dict[str, Any]:
    if isinstance(pair_map, (str, Path)):
        return dict(load_pair_map(pair_map))
    return dict(pair_map)


def _model_payload(model: Mapping[str, Any] | Path | str) -> Dict[str, Any]:
    if isinstance(model, (str, Path)):
        return load_surrogate(model)
    return dict(model)


def triplet_domain_report(
    edge_r_over_d: np.ndarray,
    domain: Mapping[str, float] | None = None,
) -> Dict[str, Any]:
    """Return a non-raising report for the surrogate training domain.

    The domain follows the existing runtime convention: after sorting the three
    edges, ``Rmin >= rmin_min``, ``Rmid <= rmid_max`` and
    ``Rmax <= rmax_max``.
    """
    limits = dict(DEFAULT_DOMAIN if domain is None else domain)
    edges = np.asarray(edge_r_over_d, dtype=float)
    if edges.ndim == 1:
        edges = edges[None, :]
    if edges.ndim != 2 or edges.shape[1] != 3:
        raise ValueError(f"edge_r_over_d must have shape (B, 3), got {edges.shape}.")
    sorted_r = np.sort(edges, axis=1)
    reasons: list[list[str]] = []
    valid = np.ones(len(sorted_r), dtype=bool)
    for index, row in enumerate(sorted_r):
        row_reasons: list[str] = []
        if row[0] < limits["rmin_min"] - 1e-10:
            row_reasons.append(
                f"Rmin={row[0]:.8g} < {limits['rmin_min']:.8g}"
            )
        if row[1] > limits["rmid_max"] + 1e-10:
            row_reasons.append(
                f"Rmid={row[1]:.8g} > {limits['rmid_max']:.8g}"
            )
        if row[2] > limits["rmax_max"] + 1e-10:
            row_reasons.append(
                f"Rmax={row[2]:.8g} > {limits['rmax_max']:.8g}"
            )
        if row_reasons:
            valid[index] = False
        reasons.append(row_reasons)
    return {
        "valid_mask": valid,
        "all_valid": bool(np.all(valid)),
        "sorted_edges_over_d": sorted_r,
        "reasons": reasons,
        "domain": limits,
    }


def predict_triplet_delta3(
    centers: np.ndarray,
    *,
    diameter: float,
    model: Mapping[str, Any] | Path | str,
    check_domain: bool = True,
    energy_unit_J: float = ENERGY_UNIT_J,
) -> Dict[str, Any]:
    """Predict the irreducible three-body energy for one triplet.

    Parameters
    ----------
    centers:
        Cartesian coordinates with shape ``(3, 3)``. Any consistent length
        unit is accepted if ``diameter`` uses the same unit.
    diameter:
        Particle diameter in the same unit as ``centers``.
    model:
        Loaded model payload or path to the released joblib file.
    """
    xyz = _centers_array(centers, n_particles=3)
    if diameter <= 0:
        raise ValueError("diameter must be positive.")
    payload = _model_payload(model)
    edges, betas = triplet_edges_batch(xyz, float(diameter))
    report = triplet_domain_report(edges)
    values_J, info = predict_triplets_J(
        xyz,
        float(diameter),
        payload,
        check_domain=check_domain,
    )
    value_J = float(values_J[0])
    return {
        "delta3_J": value_J,
        "delta3_Estar": value_J / float(energy_unit_J),
        "edge_r_over_d": info["edge_r_over_d"][0],
        "edge_beta_deg": info["edge_beta_deg"][0],
        "inside_training_domain": bool(report["valid_mask"][0]),
        "domain_warnings": report["reasons"][0],
        "compact_branch": bool(
            info["Rmin"][0] <= float(payload["compact_cutoff"])
        ),
        "model_training_version": payload.get("training_version"),
        "target_scale": float(payload.get("target_scale", 1e21)),
    }


def predict_triplets_delta3(
    centers_batch: np.ndarray,
    *,
    diameter: float,
    model: Mapping[str, Any] | Path | str,
    check_domain: bool = True,
    energy_unit_J: float = ENERGY_UNIT_J,
) -> Dict[str, Any]:
    """Vectorized prediction for a batch with shape ``(B, 3, 3)``."""
    payload = _model_payload(model)
    values_scaled, info = predict_triplets_scaled(
        centers_batch,
        float(diameter),
        payload,
        check_domain=check_domain,
    )
    target_scale = float(payload.get("target_scale", 1e21))
    values_J = values_scaled / target_scale
    report = triplet_domain_report(info["edge_r_over_d"])
    return {
        "delta3_J": values_J,
        "delta3_Estar": values_J / float(energy_unit_J),
        "edge_r_over_d": info["edge_r_over_d"],
        "edge_beta_deg": info["edge_beta_deg"],
        "inside_training_domain": report["valid_mask"],
        "domain_warnings": report["reasons"],
        "compact_branch": info["Rmin"] <= float(payload["compact_cutoff"]),
        "model_training_version": payload.get("training_version"),
    }


def predict_cluster_energy(
    centers: np.ndarray,
    *,
    diameter: float,
    pair_map: Mapping[str, Any] | Path | str,
    model: Mapping[str, Any] | Path | str,
    check_domain: bool = True,
    energy_unit_J: float = ENERGY_UNIT_J,
) -> Dict[str, Any]:
    """Compute pair-only and pair-plus-ML3B energies for a cluster.

    The result is a truncated pair-plus-triplet expansion. It is not a direct
    full-cluster SCM energy and does not include irreducible terms of order four
    and above.
    """
    xyz = _centers_array(centers)
    if len(xyz) < 3:
        raise ValueError("At least three particles are required.")
    if diameter <= 0:
        raise ValueError("diameter must be positive.")
    pair_payload = _pair_map_payload(pair_map)
    model_payload = _model_payload(model)

    pair_indices, distances, betas = pair_edges_from_centers(xyz)
    pair_energy_J = pairwise_energy_from_edges(
        distances / float(diameter),
        betas,
        pair_payload,
        input_is_over_d=True,
        method="physical",
    )

    triplet_indices, triplets = enumerate_cluster_triplets(xyz)
    triplet_edges, _ = triplet_edges_batch(triplets, float(diameter))
    report = triplet_domain_report(triplet_edges)
    prediction = predict_cluster_triplet_sum_J(
        xyz,
        float(diameter),
        model_payload,
        check_domain=check_domain,
    )
    triplet_energy_J = float(prediction["delta3_sum_J"])
    total_J = pair_energy_J + triplet_energy_J

    return {
        "n_particles": int(len(xyz)),
        "n_pairs": int(len(pair_indices)),
        "n_triplets": int(len(triplet_indices)),
        "pair_indices": pair_indices,
        "pair_distances": distances,
        "pair_beta_deg": betas,
        "pair_energy_J": pair_energy_J,
        "triplet_indices": prediction["triplet_indices"],
        "delta3_triplet_J": prediction["delta3_triplet_J"],
        "triplet_energy_J": triplet_energy_J,
        "pair_plus_ml3b_J": total_J,
        "pair_energy_Estar": pair_energy_J / float(energy_unit_J),
        "triplet_energy_Estar": triplet_energy_J / float(energy_unit_J),
        "pair_plus_ml3b_Estar": total_J / float(energy_unit_J),
        "triplet_domain_valid_mask": report["valid_mask"],
        "triplet_domain_coverage": float(np.mean(report["valid_mask"])),
        "domain_warnings": report["reasons"],
        "scope": (
            "pair-plus-ML3B truncated expansion; irreducible N>=4 terms are omitted"
        ),
    }


def compute_triplet_delta3_scm(
    centers: np.ndarray,
    *,
    pair_map: Mapping[str, Any] | Path | str,
    params: SCMParams = DEFAULT_PARAMS,
    lmax: int = DEFAULT_LMAX,
    n_quad: int | None = None,
    energy_unit_J: float = ENERGY_UNIT_J,
) -> Dict[str, Any]:
    """Compute one triplet by the validated matrix-SCM definition.

    The returned quantity follows the project convention

    ``Phi3 = mean_k[U3(k) - 3 U1(k)]`` and
    ``Delta3 = Phi3 - sum_ij phi_pair(r_ij, beta_ij)``.

    A full publication calculation should use the article settings, notably
    ``lmax=6`` and ``n_quad=8000``. Smaller values are useful only for smoke
    tests and must not replace reported numerical results.
    """
    xyz = _centers_array(centers, n_particles=3)
    normals_count = int(params.n_quad if n_quad is None else n_quad)
    if normals_count <= 0:
        raise ValueError("n_quad must be positive.")
    normals = fibonacci_sphere_points(normals_count)

    single_system = MatrixSCMSystem(
        centers=np.zeros((1, 3), dtype=float),
        lmax=int(lmax),
        normals=normals,
        params=params,
    )
    triplet_system = MatrixSCMSystem(
        centers=xyz,
        lmax=int(lmax),
        normals=normals,
        params=params,
    )

    single_k = np.empty(params.n_orient, dtype=float)
    triplet_k = np.empty(params.n_orient, dtype=float)
    for k in range(params.n_orient):
        field = rotating_field_k(k, params)
        single_k[k], _ = single_system.energy_parts(field)
        triplet_k[k], _ = triplet_system.energy_parts(field)

    excess_k = triplet_k - 3.0 * single_k
    phi3_J = float(np.mean(excess_k))

    geometry = edge_info(xyz)
    pair_payload = _pair_map_payload(pair_map)
    pair_sum_J = pairwise_energy_from_edges(
        geometry["distances"] / float(params.d),
        geometry["beta_deg"],
        pair_payload,
        input_is_over_d=True,
        method="physical",
    )
    delta3_J = phi3_J - pair_sum_J

    return {
        "single_energy_k_J": single_k,
        "triplet_total_energy_k_J": triplet_k,
        "triplet_excess_energy_k_J": excess_k,
        "phi3_J": phi3_J,
        "pair_sum_J": pair_sum_J,
        "delta3_J": delta3_J,
        "phi3_Estar": phi3_J / float(energy_unit_J),
        "pair_sum_Estar": pair_sum_J / float(energy_unit_J),
        "delta3_Estar": delta3_J / float(energy_unit_J),
        "edge_distances": geometry["distances"],
        "edge_r_over_d": geometry["distances"] / float(params.d),
        "edge_beta_deg": geometry["beta_deg"],
        "parameters": {
            "eps1_r": params.eps1_r,
            "eps2_r": params.eps2_r,
            "a_m": params.a,
            "d_m": params.d,
            "E0_V_per_m": params.E0,
            "n_orient": params.n_orient,
            "lmax": int(lmax),
            "n_quad": normals_count,
        },
        "classification": {
            "definition": "physically defined within the stated SCM model",
            "value": "numerical result for the supplied geometry and settings",
        },
    }
