# Как применить пакет в Windows

## 1. Сохранить резервную копию текущего проекта

```powershell
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
Compress-Archive -Path D:\Projects\article1\* `
  -DestinationPath "D:\Projects\article1_before_github_$stamp.zip"
Get-FileHash "D:\Projects\article1_before_github_$stamp.zip" -Algorithm SHA256
```

## 2. Распаковать starter в отдельный каталог

Например:

```text
D:\Projects\rotating-field-three-body
```

Не распаковывайте поверх текущего расчётного проекта.

## 3. При необходимости импортировать исследовательские скрипты

```powershell
cd D:\Projects\rotating-field-three-body
.\tools\import_existing_project_files.ps1 `
  -SourceRoot D:\Projects\article1
```

Скрипт предварительно сохраняет резервные копии импортируемых файлов внутри `source_backup`.

## 4. Создать среду и проверить

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

Get-ChildItem `
  src\rotating_field_three_body\*.py, `
  examples\*.py, `
  tests\*.py | ForEach-Object { python -m py_compile $_.FullName }
python -m pytest -q
rf3b --help
```

Ожидается: `9 passed` до добавления новых тестов.

## 5. Добавить модель

Модель в starter не включена. После размещения на Zenodo:

1. скопируйте `data\asset_manifest.template.json` в `data\asset_manifest.json`;
2. замените URL-заглушки;
3. выполните:

```powershell
rf3b download-assets `
  --manifest data\asset_manifest.json `
  --destination data\external
```

## 6. Создать репозиторий GitHub

После просмотра авторов, лицензии и `CITATION.cff`:

```powershell
.\tools\create_github_repo.ps1
```

Или вручную:

```powershell
git init
git branch -M main
git add .
git commit -m "Initial public reproducibility release"
gh repo create vanyasimkin/rotating-field-three-body `
  --public --source . --remote origin --push
```

## 7. Проверочные расчёты

```powershell
python examples\run_one_scm_triplet.py --lmax 1 --n-quad 80
```

Это только smoke test. Для параметров статьи:

```powershell
rf3b scm-triplet `
  --coordinates data\triplet_example.json `
  --pair-map data\scm_pair_orientation_map_lmax6_beta2p5.npz `
  --lmax 6 `
  --n-quad 8000 `
  --n-orient 8 `
  --output outputs\triplet_scm.json
```

Числа статьи обновляются только после фактического расчёта и проверки архивированного результата.
