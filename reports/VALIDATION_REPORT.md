# Validation report

Date: 2026-07-23

## Checks performed

```bash
python -m py_compile src/rotating_field_three_body/*.py examples/*.py tests/*.py tools/verify_release.py
python -m pytest -q
PYTHONPATH=src python -m rotating_field_three_body --help
PYTHONPATH=src python examples/run_one_scm_triplet.py --lmax 1 --n-quad 40
python -m pip wheel . --no-deps --no-build-isolation -w dist
```

## Results

- Python compilation: passed.
- Test suite: 9 passed.
- CLI parser: passed.
- Reduced SCM smoke run: passed and wrote `reports/scm_smoke_output.json`.
- Wheel build: passed; temporary build products were removed from the repository starter.

## Important limitations

- The 5.77 GB canonical joblib model was not available in the active project folder and is not bundled.
- Therefore, no end-to-end prediction with the actual trained model was rerun in this packaging stage.
- The SCM smoke run used `lmax=1`, `n_quad=40`; its numerical value is only a software check and must not be used in the manuscript.
- No manuscript number was changed.
