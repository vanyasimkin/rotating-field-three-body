#!/usr/bin/env python3
"""Compute pair-only and pair-plus-ML3B energies for a small cluster."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rotating_field_three_body import predict_cluster_energy
from rotating_field_three_body.io import json_safe, read_centers


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument(
        "--pair-map",
        type=Path,
        default=Path("data/scm_pair_orientation_map_lmax6_beta2p5.npz"),
    )
    parser.add_argument(
        "--coordinates", type=Path, default=Path("data/cluster_example.json")
    )
    parser.add_argument("--diameter", type=float, default=2.0e-6)
    args = parser.parse_args()

    result = predict_cluster_energy(
        read_centers(args.coordinates),
        diameter=args.diameter,
        pair_map=args.pair_map,
        model=args.model,
    )
    print(json.dumps(json_safe(result), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
