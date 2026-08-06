# Interpretation scope

## Defined within the model

- The matrix-SCM linear system and energy functional are defined by the source code and the stated dielectric-sphere parameters.
- The irreducible triplet contribution is defined as `Delta3 = mean_k(U3 - 3 U1) - sum(phi_pair)`.
- Pair-plus-ML3B cluster predictions are a truncated expansion and omit irreducible terms of order four and above.
- The eight-orientation circular average is the numerical averaging rule implemented by the code.

## Numerical observations

- Every value returned for a specific geometry is a numerical observation for the selected parameters, discretization, pair map, and model version.
- Accuracy, sign agreement, extrapolation behavior, and runtime claims must be tied to actual validation outputs rather than inferred from source code.
- The included metrics JSON reports internal model-selection metrics. It is not the complete dataset underlying the article's figures and tables.

## Physical interpretation

- Consequences for motif selection, assembly pathways, or experimental control are physical interpretations.
- The fixed-permittivity electrostatic implementation does not itself calculate colloidal diffusion times, polarization relaxation times, electrokinetic effects, or hydrodynamic flows.
