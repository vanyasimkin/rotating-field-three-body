"""Rotating-field three-body polarization calculations and ML3B inference."""

from .api import (
    compute_triplet_delta3_scm,
    predict_cluster_energy,
    predict_triplet_delta3,
    predict_triplets_delta3,
    triplet_domain_report,
)
from .config import DEFAULT_LMAX, DEFAULT_PARAMS, ENERGY_UNIT_J
from .geometry import edge_info, pair_oriented_centers, triangle_centers
from .pair_map import (
    interpolate_pair_phi,
    interpolate_pair_phi_array,
    load_pair_map,
    pairwise_energy_from_edges,
)
from .scm import MatrixSCMSystem, SCMParams
from .surrogate import load_surrogate

__all__ = [
    "DEFAULT_LMAX",
    "DEFAULT_PARAMS",
    "ENERGY_UNIT_J",
    "MatrixSCMSystem",
    "SCMParams",
    "compute_triplet_delta3_scm",
    "edge_info",
    "interpolate_pair_phi",
    "interpolate_pair_phi_array",
    "load_pair_map",
    "load_surrogate",
    "pair_oriented_centers",
    "pairwise_energy_from_edges",
    "predict_cluster_energy",
    "predict_triplet_delta3",
    "predict_triplets_delta3",
    "triangle_centers",
    "triplet_domain_report",
]

__version__ = "0.1.0"
