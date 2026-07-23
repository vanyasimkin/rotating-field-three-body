#!/usr/bin/env python3
"""Deterministic N=4--6 cluster geometries for SCM transfer tests."""

from __future__ import annotations

import math
from typing import Dict, List

import numpy as np


def rotation_matrix_xyz(rx_deg=0.0, ry_deg=0.0, rz_deg=0.0):
    rx, ry, rz = np.deg2rad([rx_deg, ry_deg, rz_deg])
    cx, sx = np.cos(rx), np.sin(rx)
    cy, sy = np.cos(ry), np.sin(ry)
    cz, sz = np.cos(rz), np.sin(rz)

    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]], float)
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], float)
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]], float)
    return Rz @ Ry @ Rx


def center_and_rotate(points, rotation):
    points = np.asarray(points, float)
    points = points - np.mean(points, axis=0, keepdims=True)
    return points @ rotation.T


def chain(n, spacing):
    x = spacing * (np.arange(n) - 0.5 * (n - 1))
    points = np.column_stack([x, np.zeros(n), np.zeros(n)])
    return center_and_rotate(points, rotation_matrix_xyz(25, 20, 15))


def square(side):
    h = 0.5 * side
    points = np.array(
        [[-h, -h, 0], [h, -h, 0], [h, h, 0], [-h, h, 0]], float
    )
    return center_and_rotate(points, rotation_matrix_xyz(38, 17, 12))


def tetrahedron(side):
    points = np.array(
        [
            [0, 0, 0],
            [1, 0, 0],
            [0.5, math.sqrt(3) / 2, 0],
            [0.5, math.sqrt(3) / 6, math.sqrt(2 / 3)],
        ],
        float,
    )
    return center_and_rotate(side * points, rotation_matrix_xyz(20, 30, 10))


def trigonal_bipyramid(side):
    radius = side / math.sqrt(3)
    height = side * math.sqrt(2 / 3)
    base = np.array(
        [
            [radius, 0, 0],
            [-0.5 * radius, math.sqrt(3) * radius / 2, 0],
            [-0.5 * radius, -math.sqrt(3) * radius / 2, 0],
        ]
    )
    points = np.vstack([base, [0, 0, height], [0, 0, -height]])
    return center_and_rotate(points, rotation_matrix_xyz(22, 31, 9))


def square_pyramid(side):
    h = 0.5 * side
    apex_height = side / math.sqrt(2)
    points = np.array(
        [
            [-h, -h, 0],
            [h, -h, 0],
            [h, h, 0],
            [-h, h, 0],
            [0, 0, apex_height],
        ],
        float,
    )
    return center_and_rotate(points, rotation_matrix_xyz(28, 16, 21))


def planar_hexagon(side):
    angles = np.arange(6) * np.pi / 3
    points = np.column_stack(
        [side * np.cos(angles), side * np.sin(angles), np.zeros(6)]
    )
    return center_and_rotate(points, rotation_matrix_xyz(42, 13, 8))


def octahedron(side):
    radius = side / math.sqrt(2)
    points = radius * np.array(
        [
            [1, 0, 0],
            [-1, 0, 0],
            [0, 1, 0],
            [0, -1, 0],
            [0, 0, 1],
            [0, 0, -1],
        ],
        float,
    )
    return center_and_rotate(points, rotation_matrix_xyz(17, 29, 11))


def random_compact(n, d, seed, min_sep=1.14, radius=2.2):
    rng = np.random.default_rng(seed)
    points = [np.zeros(3)]
    attempts = 0
    while len(points) < n and attempts < 200000:
        attempts += 1
        candidate = rng.uniform(-radius * d, radius * d, size=3)
        if np.linalg.norm(candidate) > radius * d:
            continue
        if all(np.linalg.norm(candidate - p) >= min_sep * d for p in points):
            points.append(candidate)
    if len(points) != n:
        raise RuntimeError(f"Failed to generate random compact N={n}.")
    return center_and_rotate(
        np.asarray(points), rotation_matrix_xyz(13, 23, 7)
    )


def build_cluster_motifs(d, side_over_d=1.25):
    side = side_over_d * d
    spacing = 1.20 * d
    motifs = [
        {"name": "N4_tetrahedron", "family": "tetrahedron", "centers": tetrahedron(side)},
        {"name": "N4_tilted_square", "family": "square", "centers": square(side)},
        {"name": "N4_tilted_chain", "family": "chain", "centers": chain(4, spacing)},
        {"name": "N4_random_compact", "family": "random", "centers": random_compact(4, d, 401)},
        {"name": "N5_trigonal_bipyramid", "family": "trigonal_bipyramid", "centers": trigonal_bipyramid(side)},
        {"name": "N5_square_pyramid", "family": "square_pyramid", "centers": square_pyramid(side)},
        {"name": "N5_tilted_chain", "family": "chain", "centers": chain(5, spacing)},
        {"name": "N5_random_compact", "family": "random", "centers": random_compact(5, d, 501)},
        {"name": "N6_octahedron", "family": "octahedron", "centers": octahedron(side)},
        {"name": "N6_tilted_hexagon", "family": "hexagon", "centers": planar_hexagon(side)},
        {"name": "N6_tilted_chain", "family": "chain", "centers": chain(6, spacing)},
        {"name": "N6_random_compact", "family": "random", "centers": random_compact(6, d, 601)},
    ]
    for item in motifs:
        item["n_particles"] = len(item["centers"])
    return motifs
