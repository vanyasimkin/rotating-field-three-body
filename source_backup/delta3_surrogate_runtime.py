#!/usr/bin/env python3
"""
Runtime helpers for the permutation-invariant Delta3 surrogate.

The saved model predicts Delta3 in units of 1e-21 J. Public functions can
return either scaled values or SI joules. All end-to-end prediction functions
start from Cartesian particle coordinates.
"""

from __future__ import annotations

from itertools import combinations
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import joblib
import numpy as np

from delta3_invariant_features import build_invariant_features


DEFAULT_DOMAIN = {
    "rmin_min": 1.10,
    "rmid_max": 5.00,
    "rmax_max": 10.00,
}


def pair_edges_from_centers(
    centers: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Return pair indices, distances and inclinations beta for arbitrary N.

    beta is the angle between an edge and the xy field-rotation plane.
    """
    centers = np.asarray(centers, dtype=float)
    if centers.ndim != 2 or centers.shape[1] != 3:
        raise ValueError(f"centers must have shape (N, 3), got {centers.shape}.")
    if len(centers) < 2:
        raise ValueError("At least two particles are required.")

    pairs: List[Tuple[int, int]] = []
    distances: List[float] = []
    betas: List[float] = []

    for i, j in combinations(range(len(centers)), 2):
        vector = centers[j] - centers[i]
        distance = float(np.linalg.norm(vector))
        if distance <= 0.0:
            raise ValueError(f"Particles {i} and {j} have zero separation.")
        unit = vector / distance
        beta = float(
            np.degrees(np.arcsin(np.clip(abs(unit[2]), 0.0, 1.0)))
        )
        pairs.append((i, j))
        distances.append(distance)
        betas.append(beta)

    return (
        np.asarray(pairs, dtype=int),
        np.asarray(distances, dtype=float),
        np.asarray(betas, dtype=float),
    )


def triplet_edges_batch(
    centers_batch: np.ndarray,
    d: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Convert Cartesian triplets into three edge lengths and beta angles.

    Parameters
    ----------
    centers_batch
        Shape (B, 3, 3), in SI length units.
    d
        Particle diameter in the same units.
    """
    centers_batch = np.asarray(centers_batch, dtype=float)
    if centers_batch.ndim == 2:
        centers_batch = centers_batch[None, ...]
    if centers_batch.ndim != 3 or centers_batch.shape[1:] != (3, 3):
        raise ValueError(
            "centers_batch must have shape (B, 3, 3), "
            f"got {centers_batch.shape}."
        )

    vectors = np.stack(
        [
            centers_batch[:, 1] - centers_batch[:, 0],
            centers_batch[:, 2] - centers_batch[:, 0],
            centers_batch[:, 2] - centers_batch[:, 1],
        ],
        axis=1,
    )
    distances = np.linalg.norm(vectors, axis=2)
    if np.any(distances <= 0.0):
        raise ValueError("At least one triplet contains a zero-length edge.")
    unit = vectors / distances[:, :, None]
    beta_deg = np.degrees(
        np.arcsin(np.clip(np.abs(unit[:, :, 2]), 0.0, 1.0))
    )
    return distances / float(d), beta_deg


def load_surrogate(model_path: Path | str) -> Dict[str, Any]:
    payload = joblib.load(Path(model_path))
    if payload.get("feature_mode") != "invariant":
        raise ValueError(
            "The model is not permutation invariant. Retrain with "
            "--feature-mode invariant."
        )
    required = ["global_model", "compact_model", "compact_cutoff"]
    missing = [key for key in required if key not in payload]
    if missing:
        raise KeyError(f"Saved model is missing fields: {missing}")
    return payload


def validate_triplet_domain(
    edge_r_over_d: np.ndarray,
    domain: Dict[str, float] | None = None,
) -> None:
    domain = dict(DEFAULT_DOMAIN if domain is None else domain)
    sorted_r = np.sort(np.asarray(edge_r_over_d, dtype=float), axis=1)
    bad = (
        (sorted_r[:, 0] < domain["rmin_min"] - 1e-10)
        | (sorted_r[:, 1] > domain["rmid_max"] + 1e-10)
        | (sorted_r[:, 2] > domain["rmax_max"] + 1e-10)
    )
    if np.any(bad):
        first = int(np.flatnonzero(bad)[0])
        raise ValueError(
            "Triplet lies outside the trained domain. "
            f"Sorted edges for first invalid point: {sorted_r[first]}; "
            f"domain={domain}."
        )


def predict_from_features_scaled(
    X: np.ndarray,
    rmin_over_d: np.ndarray,
    payload: Dict[str, Any],
) -> np.ndarray:
    X = np.asarray(X, dtype=float)
    rmin_over_d = np.asarray(rmin_over_d, dtype=float)
    prediction = np.asarray(payload["global_model"].predict(X), dtype=float)
    compact = rmin_over_d <= float(payload["compact_cutoff"])
    if np.any(compact):
        prediction[compact] = payload["compact_model"].predict(X[compact])
    return prediction


def predict_triplets_scaled(
    centers_batch: np.ndarray,
    d: float,
    payload: Dict[str, Any],
    *,
    check_domain: bool = True,
) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
    """
    End-to-end triplet inference from coordinates.

    Returns Delta3 in units of 1e-21 J.
    """
    edge_r, edge_beta = triplet_edges_batch(centers_batch, d)
    if check_domain:
        validate_triplet_domain(edge_r)

    X, feature_names, metadata = build_invariant_features(edge_r, edge_beta)
    saved_names = list(payload.get("feature_names", []))
    if saved_names and saved_names != feature_names:
        raise ValueError(
            "Feature order does not match the saved model. "
            "Use the same delta3_invariant_features.py as during training."
        )

    prediction = predict_from_features_scaled(X, metadata["Rmin"], payload)
    info = {
        "edge_r_over_d": edge_r,
        "edge_beta_deg": edge_beta,
        "Rmin": metadata["Rmin"],
        "features": X,
    }
    return prediction, info


def predict_triplets_J(
    centers_batch: np.ndarray,
    d: float,
    payload: Dict[str, Any],
    *,
    check_domain: bool = True,
) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
    scaled, info = predict_triplets_scaled(
        centers_batch, d, payload, check_domain=check_domain
    )
    target_scale = float(payload.get("target_scale", 1e21))
    return scaled / target_scale, info


def enumerate_cluster_triplets(
    centers: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    centers = np.asarray(centers, dtype=float)
    indices = np.asarray(list(combinations(range(len(centers)), 3)), dtype=int)
    triplets = centers[indices]
    return indices, triplets


def predict_cluster_triplet_sum_J(
    centers: np.ndarray,
    d: float,
    payload: Dict[str, Any],
    *,
    check_domain: bool = True,
) -> Dict[str, Any]:
    indices, triplets = enumerate_cluster_triplets(centers)
    values_J, info = predict_triplets_J(
        triplets, d, payload, check_domain=check_domain
    )
    return {
        "triplet_indices": indices,
        "delta3_triplet_J": values_J,
        "delta3_sum_J": float(np.sum(values_J)),
        "edge_r_over_d": info["edge_r_over_d"],
        "edge_beta_deg": info["edge_beta_deg"],
    }
