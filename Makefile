.PHONY: venv install lint format clean run

venv:
	python -m venv .venv

install: venv
	python -m pip install -e ".[dev]"

lint:
	ruff check .
	mypy .

format:
	ruff format .
	ruff check --fix .

clean:
	rm -rf .mypy_cache dist build
	rm -rf .venv
	rm -rf src/*.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +

run:
	snowfall
