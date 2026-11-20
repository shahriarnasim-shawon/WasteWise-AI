# WasteWiseAI - Developer & CI Makefile

.PHONY: dev test simulate build seed clean

PYTHON ?= $(shell if [ -f .venv/bin/python ]; then echo .venv/bin/python; else echo python3; fi)
PYTEST ?= $(shell if [ -f .venv/bin/pytest ]; then echo .venv/bin/pytest; else echo pytest; fi)

# Run backend development server
dev:
	PYTHONPATH=. $(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run full automated test suite (inference, API, agents, simulation)
test:
	PYTHONPATH=. $(PYTHON) -m pytest tests/ -v

# Run the 30-day canteen simulation proving >=30% waste reduction
simulate:
	PYTHONPATH=. $(PYTHON) -m app.sim

# Build static React frontend
build:
	cd web && npm run build

# Seed database with 3 weeks of historical operations
seed:
	PYTHONPATH=. $(PYTHON) scripts/seed_data.py

# Clean generated caches and temporary databases
clean:
	rm -rf __pycache__ app/**/__pycache__ tests/__pycache__ .pytest_cache
	rm -f wastewise.db
