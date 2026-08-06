# Contributing

1. Create a branch from `main`.
2. Add or update tests for every numerical or API change.
3. Run:

```bash
python -m compileall -q src examples tests tools
python -m pytest -q
python -m rotating_field_three_body --help
```

4. Do not commit trained `.joblib` files, downloaded assets, article plotting outputs, or private research backups.
5. Do not change manuscript numbers from code inspection alone. Numerical claims may be updated only after the corresponding calculation has been rerun and its result artifact checked.
6. In pull requests, distinguish model definitions, numerical observations, and physical interpretations.
