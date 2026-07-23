# Interpretation scope

## Model definitions and physically established statements within the model

- The matrix-SCM linear system and the energy functional are defined by the source code and the stated dielectric-sphere model.
- The irreducible triplet contribution is defined as
  `Delta3 = mean_k(U3 - 3 U1) - sum(phi_pair)`.
- Pair-plus-ML3B cluster predictions are a truncated expansion and omit irreducible terms of order four and above.

## Numerical observations

- Every value returned for a specific geometry is a numerical observation for the selected parameters, discretization, pair map, and model version.
- Accuracy, sign agreement, extrapolation behavior, and runtime claims must be taken from archived validation outputs, not inferred from source code.

## Interpretation

- Consequences for motif selection, assembly pathways, or experimental control are physical interpretations. They are not guaranteed by the software API alone.
