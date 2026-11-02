# All targets run headlessly. `make venv` once, then `make ci` before committing.
# PYTHONPATH is cleared so host packages (e.g. ROS) cannot leak into results.
unexport PYTHONPATH
export MPLBACKEND := Agg

BOOTSTRAP_PYTHON ?= python3
VENV ?= .venv
PY := $(VENV)/bin/python
SIM_DIR ?= build/sim

.PHONY: venv check test simulate report cad fea visual motor ci clean

venv:
	$(BOOTSTRAP_PYTHON) -m venv $(VENV)
	$(PY) -m pip install -q --upgrade pip
	$(PY) -m pip install -q -c constraints.txt -e '.[dev,cad,fea]'

check:
	$(PY) -m odrt check

test:
	$(PY) -m pytest

simulate:
	$(PY) -m odrt simulate --out $(SIM_DIR)

report: simulate
	$(PY) -m odrt report --sim $(SIM_DIR) --out reports

cad: simulate
	$(PY) -m odrt cad --out build/cad --reports reports --sim $(SIM_DIR)/metrics.json

fea:
	$(PY) -m odrt fea --reports reports

visual: cad
	$(PY) -m odrt visual --out build/visual

motor:
	$(PY) -m odrt motor --reports reports

# Local CI: validate inputs, run tests, regenerate reports, and fail if the
# committed reports are stale.
ci: check test report cad fea visual motor
	git diff --exit-code -- reports/ || (echo "reports/ is stale: commit the regenerated reports" && exit 1)

clean:
	rm -rf build .pytest_cache
