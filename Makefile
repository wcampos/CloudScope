.PHONY: help setup clean test lint run install dev-install

PYTHON := python3
VENV := .venv
PIP := $(VENV)/bin/pip
PYTHON_VENV := $(VENV)/bin/python
FLASK := $(VENV)/bin/flask

help:
	@echo "Available commands:"
	@echo "make setup      - Create virtual environment and install dependencies"
	@echo "make clean     - Remove virtual environment and cached files"
	@echo "make test      - Run tests"
	@echo "make lint      - Run linting checks"
	@echo "make run       - Run the application"
	@echo "make install   - Install production dependencies"
	@echo "make dev-install - Install development dependencies"

setup: $(VENV)/bin/activate

$(VENV)/bin/activate:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install pytest pylint pytest-cov black

clean:
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +

test: setup
	$(VENV)/bin/pytest tests/ -v --cov=src --cov-report=term-missing

lint: setup
	$(VENV)/bin/pylint src/ app.py
	$(VENV)/bin/black --check src/ app.py

format: setup
	$(VENV)/bin/black src/ app.py

run: setup
	$(PYTHON_VENV) app.py

install:
	$(PIP) install -r requirements.txt

dev-install: install
	$(PIP) install pytest pylint pytest-cov black

# AWS environment setup targets
aws-configure:
	aws configure

check-aws:
	@aws sts get-caller-identity > /dev/null 2>&1 || (echo "AWS credentials not configured. Run 'make aws-configure' first" && exit 1)

.env:
	@echo "Creating .env file..."
	@echo "AWS_REGION=us-east-1" > .env
	@echo "FLASK_ENV=development" >> .env
	@echo "FLASK_APP=app.py" >> .env
	@echo "Please update .env with your configuration" 