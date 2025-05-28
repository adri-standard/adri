.PHONY: clean test install dev-install lint format docs

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	rm -rf .coverage htmlcov/ build/ dist/ *.egg-info
	rm -rf .pytest_cache .mypy_cache
	rm -f *.report.json *.report.html *_report.html *_report.txt
	rm -f crm_audit_* test_data_readiness_report.html

test:
	pytest tests/

test-unit:
	pytest tests/unit/

test-integration:
	pytest tests/integration/

test-coverage:
	pytest tests/ --cov=adri --cov-report=html --cov-report=term

install:
	pip install -e .

dev-install:
	pip install -e ".[dev]"

lint:
	flake8 adri/
	mypy adri/

format:
	black adri/ tests/
	isort adri/ tests/

docs:
	mkdocs build -f config/mkdocs.yml

docs-serve:
	mkdocs serve -f config/mkdocs.yml

check-all: lint test

release-check:
	python scripts/verify_version.py

help:
	@echo "Available commands:"
	@echo "  make clean        - Remove build artifacts and cache files"
	@echo "  make test         - Run all tests"
	@echo "  make test-unit    - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-coverage - Run tests with coverage report"
	@echo "  make install      - Install package in editable mode"
	@echo "  make dev-install  - Install with development dependencies"
	@echo "  make lint         - Run code linters"
	@echo "  make format       - Format code with black and isort"
	@echo "  make docs         - Build documentation"
	@echo "  make docs-serve   - Serve documentation locally"
	@echo "  make check-all    - Run linters and tests"
	@echo "  make release-check - Check version consistency"
