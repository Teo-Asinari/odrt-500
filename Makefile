# All targets run headlessly. `make venv` once, then `make ci` before committing.
# PYTHONPATH is cleared so host packages (e.g. ROS) cannot leak into results.
unexport PYTHONPATH
export MPLBACKEND := Agg

BOOTSTRAP_PYTHON ?= python3
VENV ?= .venv
PY := $(VENV)/bin/python
SIM_DIR ?= build/sim

.PHONY: venv check test simulate report ci clean

venv:
	$(BOOTSTRAP_PYTHON) -m venv $(VENV)
	$(PY) -m pip install -q --upgrade pip
	$(PY) -m pip install -q -c constraints.txt -e '.[dev]'

check:
	$(PY) -m odrt check

test:
	$(PY) -m pytest

simulate:
	$(PY) -m odrt simulate --out $(SIM_DIR)

report: simulate
	$(PY) -m odrt report --sim $(SIM_DIR) --out reports

# Local CI: validate inputs, run tests, regenerate reports, and fail if the
# committed reports are stale.
ci: check test report
	git diff --exit-code -- reports/ || (echo "reports/ is stale: commit the regenerated reports" && exit 1)

clean:
	rm -rf build .pytest_cache
