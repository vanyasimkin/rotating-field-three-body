#!/usr/bin/env python3
"""Predict Delta3 for one coordinate file using the released joblib model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rotating_field_three_body import predict_triplet_delta3
from rotating_field_three_body.io import json_safe, read_centers


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument(
        "--coordinates", type=Path, default=Path("data/triplet_example.json")
    )
    parser.add_argument("--diameter", type=float, default=2.0e-6)
    args = parser.parse_args()

    result = predict_triplet_delta3(
        read_centers(args.coordinates),
        diameter=args.diameter,
        model=args.model,
    )
    print(json.dumps(json_safe(result), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
