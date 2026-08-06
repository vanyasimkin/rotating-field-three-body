# ML3B surrogate model card

## Release

- Repository version: `0.1.0`
- Model file: `delta3_surrogate_corrected.joblib`
- Size: `5,767,044,032` bytes
- SHA-256: `75f58bd77a49b4dce61ffcfe2591f5183bdfc709e9dd25a1f2a2f9d7d42eed68`
- Archive DOI: `10.5281/zenodo.21512150`

## Purpose

The model predicts the irreducible three-body polarization energy, `U^(3)`, for a fixed triplet geometry of identical dielectric spheres in the rotating-field electrostatic model used by the accompanying study.

The model is intended for:

- energy prediction for individual triplets;
- batched fixed-geometry screening;
- pair-plus-three-body energy estimates for small clusters.

## Model structure

The serialized payload contains two `ExtraTreesRegressor` estimators:

- a global model;
- a compact-geometry model used when `R_min <= 1.8`.

Each estimator contains 800 trees. Input geometry is represented by 120 permutation-invariant features. The target scale is `1e21`, so the estimator output is converted to joules by division by `1e21`.

The exact estimator parameters and feature names are recorded in `data/delta3_surrogate_corrected_model_info.json`.

## Runtime domain guard

The public runtime sorts the three edge lengths in units of particle diameter and checks:

```text
R_min >= 1.10
R_mid <= 5.00
R_max <= 10.00
```

This guard identifies obvious edge-length extrapolation. It is not a proof that every accepted geometry is densely represented in the training set. Predictions outside the documented sampled domain must be treated as extrapolations.

## Limitations

- The model predicts energies, not forces.
- The hard switch at `R_min = 1.8` does not guarantee differentiability across the branch boundary.
- The model is not intended as a force-smooth potential for molecular dynamics.
- Pair-plus-three-body cluster estimates omit irreducible four-body and higher-order contributions.
- The model does not include frequency-dependent electrokinetic, ionic-cloud, or hydrodynamic effects.
- The released internal metrics file contains model-selection metrics; it is not the underlying dataset for the article figures or tables.

## Recorded software environment

```text
Python            3.13.3
NumPy             2.3.3
scikit-learn      1.7.2
joblib            1.5.2
```

Model loading is only claimed as verified in this recorded environment until another environment has been tested explicitly.

## Security

The model uses joblib/pickle serialization. Loading an untrusted file can execute arbitrary code. Download only from the archive DOI and verify the SHA-256 before loading.

## Scientific status

- The model equations, feature transformation, and branch rule are defined computationally by the released code and metadata.
- Individual predictions and validation statistics are numerical observations.
- Consequences for assembly and motif selection are physical interpretations rather than guarantees of the model.
