# Contributing

1. Create a branch from `main`.
2. Add or update tests for every numerical change.
3. Run:

```bash
python -m compileall -q src examples tests
python -m pytest -q
```

4. Do not change manuscript numbers from code inspection alone. Numerical claims must be updated only after the corresponding calculation has been rerun and its result artifact archived.
5. In pull requests, distinguish model definitions, numerical observations, and physical interpretations.
