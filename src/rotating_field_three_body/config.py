"""Canonical physical constants and lightweight package configuration."""

from __future__ import annotations

from .scm import SCMParams

ENERGY_UNIT_J = 1.0e-21
DEFAULT_LMAX = 6
DEFAULT_PARAMS = SCMParams(
    eps1_r=3.9,
    eps2_r=81.0,
    a=1.0e-6,
    E0=1.0e5,
    eps0=8.854187817e-12,
    n_orient=8,
    n_quad=8000,
)
