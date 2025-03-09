.PHONY: install test lint format clean

install:
	pip install -r requirements-dev.txt

test:
	pytest tests/ --cov=epb_api --cov-report=term-missing

lint:
	flake8 epb_api tests
	mypy epb_api tests
	black --check epb_api tests
	isort --check-only epb_api tests

format:
	black epb_api tests
	isort epb_api tests

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
