# All targets run headlessly. `make venv` once, then `make ci` before committing.
# PYTHONPATH is cleared so host packages (e.g. ROS) cannot leak into results.
unexport PYTHONPATH
export MPLBACKEND := Agg

BOOTSTRAP_PYTHON ?= python3
VENV ?= .venv
PY := $(VENV)/bin/python
SIM_DIR ?= build/sim

.PHONY: venv check test simulate report cad fea visual motor architecture coupled coupled-verify buffer-study electrical preliminary-costs compact-package compact-candidate compact-structure compact-plots support-revision revision-power r2-package r2-candidate r3-candidate control-study r3c-candidate fast-study quick t retest ci clean

venv:
	$(BOOTSTRAP_PYTHON) -m venv $(VENV)
	$(PY) -m pip install -q --upgrade pip
	$(PY) -m pip install -q -c constraints.txt -e '.[dev,cad,fea,engineering]'

check:
	$(PY) -m odrt check

# Tests run in parallel. `make quick` skips tests marked slow (whole-scenario
# simulations, CAD builds); `make t T=tests/test_x.py K=expr` runs a subset;
# `make retest` reruns only the tests that failed last time.
PYTEST := $(PY) -m pytest -n auto
test:
	$(PYTEST)

quick:
	$(PYTEST) -m "not slow"

t:
	$(PY) -m pytest $(or $(T),tests) $(if $(K),-k "$(K)")

retest:
	$(PY) -m pytest --lf -x

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

coupled:
	$(PY) -m odrt.fresh coupled || $(PY) -m odrt coupled --reports reports

coupled-verify:
	$(PY) -m odrt.fresh coupled-verify || $(PY) -m odrt coupled --reports reports --verify

architecture:
	$(PY) -m odrt architecture --reports reports

buffer-study:
	$(PY) -m odrt.fresh buffer-study || $(PY) -m odrt.buffer_study

electrical:
	$(PY) -m odrt.electrical_definition

preliminary-costs:
	$(PY) -m odrt.preliminary_costs

compact-package:
	$(PY) -m odrt.compact_package

compact-candidate:
	$(PY) -m odrt.fresh compact-candidate || $(PY) -m odrt.compact_candidate

compact-structure: compact-candidate
	$(PY) -m odrt.compact_structure

compact-plots: compact-candidate
	$(PY) -m odrt.compact_plots

support-revision:
	$(PY) -m odrt.support_revision

revision-power:
	$(PY) -m odrt.fresh revision-power || ($(PY) -m odrt.revision_power && $(PY) -m odrt.verify_revision_power)

r2-package:
	$(PY) -m odrt.r2_package

r2-candidate:
	$(PY) -m odrt.fresh r2-candidate || $(PY) -m odrt.r2_candidate r2

r3-candidate:
	$(PY) -m odrt.fresh r3-candidate || $(PY) -m odrt.r2_candidate r3

r3c-candidate:
	$(PY) -m odrt.fresh r3c-candidate || $(PY) -m odrt.r2_candidate r3c

control-study:
	$(PY) -m odrt.fresh control-study || $(PY) -m odrt.control_study

fast-study:
	$(PY) -m odrt.fresh fast-study || $(PY) -m odrt.fast_motion_study

# Local CI: validate inputs, run tests, regenerate reports, and fail if the
# committed reports are stale. Slow studies are skipped when their recorded
# input fingerprint is unchanged; `FORCE=1 make ci` regenerates everything.
ci: check test report cad fea visual motor architecture coupled-verify buffer-study electrical preliminary-costs compact-package compact-structure compact-plots support-revision revision-power r2-package r2-candidate r3-candidate control-study r3c-candidate fast-study
	git diff --exit-code -- reports/ || (echo "reports/ is stale: commit the regenerated reports" && exit 1)

clean:
	rm -rf build .pytest_cache
