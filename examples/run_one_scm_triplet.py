#!/usr/bin/env python3
"""Run one direct SCM triplet calculation.

The defaults in this example are deliberately reduced for a quick smoke test.
Use lmax=6 and n_quad=8000 for the article settings.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rotating_field_three_body import SCMParams, compute_triplet_delta3_scm
from rotating_field_three_body.io import json_safe, read_centers


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--coordinates", type=Path, default=Path("data/triplet_example.json")
    )
    parser.add_argument(
        "--pair-map",
        type=Path,
        default=Path("data/scm_pair_orientation_map_lmax6_beta2p5.npz"),
    )
    parser.add_argument("--lmax", type=int, default=1)
    parser.add_argument("--n-quad", type=int, default=80)
    args = parser.parse_args()

    params = SCMParams(n_quad=args.n_quad)
    result = compute_triplet_delta3_scm(
        read_centers(args.coordinates),
        pair_map=args.pair_map,
        params=params,
        lmax=args.lmax,
        n_quad=args.n_quad,
    )
    print(json.dumps(json_safe(result), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
