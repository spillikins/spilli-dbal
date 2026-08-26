VENV_DIR = venv
PYTHON = python3.12
PIP = $(VENV_DIR)/bin/pip
PYTHON_VENV = $(VENV_DIR)/bin/python
TOX = $(VENV_DIR)/bin/tox
PRE_COMMIT = $(VENV_DIR)/bin/pre-commit


.PHONY: venv test tox format clean build install upload_to_testpypi upload_to_pypi all


venv: venv/pyvenv.cfg $(PKG_DIR)
	# Create virtual environment.

venv/pyvenv.cfg: pyproject.toml $(PKG_DIR)
	$(PYTHON) -m venv $(VENV_DIR)
	$(PIP) -q install --upgrade pip wheel
	$(PIP) -q install -e ".[dev]" && $(PIP) -q install -e .

format: venv
	# Run checking and formatting sources.
	$(PRE_COMMIT) run -a

test: venv
	# Run pytest.
	./venv/bin/pytest -x --cov-report term-missing:skip-covered --cov=src/ tests/

tox: venv
	# Testing project via several Python versions.
	$(TOX) --parallel

clean:
	rm -rf dist/
	rm -rf src/Spilli-DBAL.egg-info
	rm -rf venv

build: clean venv
	$(PYTHON_VENV) -m build

install: build
	$(PIP) install dist/spilli_dbal-*.tar.gz
	$(PRE_COMMIT) install

upload_to_testpypi: build
	$(PYTHON_VENV) -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*

upload_to_pypi: build
	$(PYTHON_VENV) -m twine upload dist/*

all: install tox
