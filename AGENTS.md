# AGENTS.md (spilli-dbal)

## Overview
- Library: web-framework independent CRUD via SQLAlchemy 2.0 + Marshmallow 4.0. Package in `src/spilli_dbal/` (setuptools finds `spilli_dbal*`).
- Python >= 3.12 (tested 3.12/3.13/3.14). Main exports from `spilli_dbal.__init__`: `ModelMixin`, `UTCDateTime`, `SqlaDBAL`, `StatementMaker`, `SpilliDBALError`.

## Key architecture
- `spilli_dbal/models/`: `ModelMixin` gives `id` (UUID, default `uuid4()`), `created_at`/`updated_at` using `models/fields.UTCDateTime`. `UTCDateTime` requires tz-aware UTC on bind, normalizes naive result values to UTC.
- `spilli_dbal/dbal/sqla.py`: Generic `SqlaDBAL[M]` extracts the model from `SqlaDBAL[Model]` subclass via `__orig_bases__` (must subclass with type param). CRUD: `create/update` commit/rollback with DB-specific IntegrityError/CompileError mapping to `spilli_dbal.dbal.exceptions` (SQLite/Postgres handled). `update` uses `returning(self._model)` + `scalars().one()`. `bulk_create` uses `session.execute(insert(self._model), data)` (no commit). `read_filtered_list` supports `in_` when passing lists; `sort_field`/`sort_order`. `delete/bulk_delete` execute directly.
- `spilli_dbal/dbal/paginate.py`: `PageMixin` parses query params by prefix: filters `lt/le/eq/ne/ge/gt/in`, search `contain__...` -> `ilike %...%`, sort `sort__field` with `asc/desc`. Builds `where` as `{'and': [...]}` and passes to `StatementMaker`. `paginate` can attach `_metadata.pagination` if `include_metadata=True` (uses count query with `limit/offset/order_by` cleared).
- `spilli_dbal/statement_maker.py`: Validates via `SQLJSONSchema` (Marshmallow). `make_where` only accepts top-level single key `and` (top-level `or` raises NotImplementedError). Operators: `lt/le/eq/ne/ge/gt/in/ilike`. `ilike` wraps value as `f'%{value}%'`.
- `spilli_dbal/schemas/base.py`: `BaseSchema` drops empty values on dump (`''`, `None`, `...`, `[]`, `{}`, `()`, `set`) recursively except `skipped_keys`; enforces UTC on datetime fields.

## Workflow
- After every change, run `make format` for verification and autoformatting. Use ONLY this command for linting and autoformatting.
- Before committing, run `make test`.

## Dev commands (from Makefile)
- Create venv + install dev deps editable: `make venv` (uses `python3.12`)
- Run tests: `make test` → `./venv/bin/pytest -x --cov-report term-missing:skip-covered --cov=src/ tests/`
- Run pre-commit on all files: `make format`
- Run tox across py314/py313/py312 (parallel): `make tox`
- Build sdist/wheel: `make build` (cleans first)
- Install from built sdist + install pre-commit hooks: `make install`
- Full CI-like: `make all` = `install` + `tox`

## Tests
- Fixtures in `tests/conftest.py` use in-memory SQLite with `PRAGMA foreign_keys=ON`, create models `Parents/Children/Fathers` inheriting `ModelMixin+Base`, provide DBAL subclasses and helpers. Pagination serialized via `ParentPaginationSchema`. See `tests/dbal/`, `tests/test_pagination_mixin.py`, `tests/test_statement_maker.py`, `tests/test_model_mixin.py`.

## Tooling / CI
- Pre-commit: pyupgrade (py312+), black (line 100, skip string normalization), isort-like reorder-python-imports, flake8 with bugbear/implicit-str-concat/pytest plugins, bandit (excludes tests/venv), docformatter/docsig/pycln, etc. Config in `.pre-commit-config.yaml`, styles in `pyproject.toml`.
- CI (`.github/workflows/testing.yaml`): linters/test/tox/build on push (Python 3.12/3.13/3.14).
- Tox config in `pyproject.toml` `[tool.tox]` legacy_ini uses env_list py314/py313/py312, installs editable `[dev]` then `.` and runs `pytest`.

## Gotchas
- `SqlaDBAL` must be subclassed as `SqlaDBAL[YourModel]` or instantiation will fail type extraction.
- `StatementMaker.make_where` only supports a single top-level `and` (top-level `or` not implemented). `PageMixin` always builds `{'and': filters}` when filters exist.
- `paginate` with `contain__` uses `ilike` with `f'%{value}%'` (substring match). `sort__field` requires value in `_sort_value` (`asc`/`desc`).
- `UTCDateTime` rejects naive datetimes and non-UTC tz; result naive values are coerced to UTC.
- `bulk_create` does not commit and returns SQLAlchemy Result; `create/update` manage commits/rollbacks and map errors.
- In tests, models must satisfy `ModelMixin` expectations (UUID id).
