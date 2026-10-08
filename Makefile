UV ?= $(or $(shell command -v uv),$(HOME)/portfolio/.tools/bin/uv)
PYTHON ?= $(UV) run python
.PHONY: policy-note setup data quick all test lint figures report readme-numbers clean
setup:
	$(UV) sync --locked
quick:
	$(UV) run python scripts/research.py --quick
lint:
	$(UV) run ruff check .
	$(UV) run ruff format --check .
	$(UV) run mypy src
test:
	$(UV) run pytest
all:
	$(UV) run python scripts/research.py
	$(UV) run python scripts/preserve_mm.py
	$(UV) run python scripts/yoy.py
	$(UV) run python scripts/outputs.py
data:
	$(UV) run python -c "from inflation_forecast_nowcast.sources import acquire; from pathlib import Path; acquire(Path.cwd())"
figures readme-numbers:
	$(PYTHON) scripts/public_presentation.py
report:
	$(PYTHON) scripts/technical_report.py
policy-note:
	$(PYTHON) scripts/public_presentation.py
clean:
	@echo "Remove generated artifacts explicitly after inspecting them; no automatic data deletion."

.PHONY: v3 v3-outputs
v3:
	$(PYTHON) scripts/v3.py
v3-outputs:
	$(PYTHON) scripts/public_presentation.py
