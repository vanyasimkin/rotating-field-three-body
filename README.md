# Rotating-Field Three-Body Polarization

Reusable matrix-SCM calculations and a permutation-invariant ML3B surrogate for dielectric colloids in an electric field rotating in the `xy` plane.

This repository starter separates two use cases:

- **model use:** predict the irreducible triplet contribution for one triplet, a batch, or all triplets in a cluster;
- **direct calculation:** compute one triplet with the validated matrix-SCM definition and subtract the refined pair-map reference.

## What is included

- matrix-SCM core;
- 3D triplet geometry convention;
- physically constrained pair-map interpolation;
- exact 120-feature permutation-invariant representation;
- surrogate runtime;
- deterministic `N=4--6` cluster motifs;
- high-level Python API and CLI;
- refined pair map used by the corrected pipeline;
- tests, examples, and GitHub Actions.

## What is not included yet

The canonical trained model is not stored in this starter. Its recorded file is:

```text
delta3_surrogate_corrected.joblib
size:   5,767,044,032 bytes
SHA256: 75f58bd77a49b4dce61ffcfe2591f5183bdfc709e9dd25a1f2a2f9d7d42eed68
```

Publish it in an immutable data/model archive, then fill `data/asset_manifest.json` from the provided template.

## Installation

```bash
git clone https://github.com/vanyasimkin/rotating-field-three-body.git
cd rotating-field-three-body

python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Linux/macOS:
# source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

The canonical joblib metadata records Python 3.13.3, NumPy 2.3.3, scikit-learn 1.7.2, and joblib 1.5.2. The package pins scikit-learn 1.7.2 because loading persisted scikit-learn estimators across versions is not guaranteed.

## Quick checks

```bash
python -m compileall -q src examples tests
python -m pytest -q
python -m rotating_field_three_body --help
```

## Predict one triplet

Coordinates and diameter must use the same length unit. The prediction is tied to the physical system and energy normalization used to train the archived model.

```bash
rf3b predict-triplet \
  --coordinates data/triplet_example.json \
  --diameter 2e-6 \
  --model data/external/delta3_surrogate_corrected.joblib \
  --output outputs/triplet_prediction.json
```

Python API:

```python
from rotating_field_three_body import predict_triplet_delta3
from rotating_field_three_body.io import read_centers

result = predict_triplet_delta3(
    read_centers("data/triplet_example.json"),
    diameter=2.0e-6,
    model="data/external/delta3_surrogate_corrected.joblib",
)
print(result["delta3_J"], result["inside_training_domain"])
```

## Predict a cluster

```bash
rf3b predict-cluster \
  --coordinates data/cluster_example.json \
  --diameter 2e-6 \
  --pair-map data/scm_pair_orientation_map_lmax6_beta2p5.npz \
  --model data/external/delta3_surrogate_corrected.joblib \
  --output outputs/cluster_prediction.json
```

The reported `pair_plus_ml3b` value is a **truncated pair-plus-triplet expansion**. It is not the direct full-cluster SCM energy and omits irreducible terms of order four and above.

## Direct SCM triplet

Fast smoke test:

```bash
python examples/run_one_scm_triplet.py --lmax 1 --n-quad 80
```

Article settings:

```bash
rf3b scm-triplet \
  --coordinates data/triplet_example.json \
  --pair-map data/scm_pair_orientation_map_lmax6_beta2p5.npz \
  --lmax 6 \
  --n-quad 8000 \
  --n-orient 8 \
  --output outputs/triplet_scm.json
```

The smoke-test output must not be used to replace article numbers.

## Coordinate convention

A reference triplet is defined by

```text
r1 = (0, 0, 0)
r2 = r12 (cos(alpha), sin(alpha), 0)
r3 = r13 (cos(alpha + gamma), sin(alpha + gamma), 0)
```

and then tilted around the laboratory `x` axis by `psi`.

- `gamma`: internal angle between `r12` and `r13`;
- `alpha`: azimuthal orientation before tilt;
- `psi`: tilt of the triangle plane relative to the field-rotation plane.

## Scientific status of outputs

- **Model definition:** the SCM equations, pair subtraction, and feature construction are defined by the source code and stated parameters.
- **Numerical observation:** every computed energy, accuracy metric, boundary location, and runtime is numerical and must be tied to an archived output.
- **Interpretation:** implications for motif selection or self-assembly are physical interpretations, not guarantees of the software.

See `docs/interpretation_scope.md`.

## Repository preparation

The files in `source_backup/` preserve the source modules from which the installable package was assembled. `reports/SOURCE_MANIFEST.json` records their SHA-256 hashes and identifies newly created wrapper files.

## Citation

Update `CITATION.cff` with the final author list, software DOI, data/model DOI, and paper citation before release `v1.0.0`.
