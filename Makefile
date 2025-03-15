.PHONY: help setup clean test lint format docker-* db-* migrate-*

# Variables
PYTHON = python3.13
VENV = .venv
PIP = $(VENV)/bin/pip
PYTEST = $(VENV)/bin/pytest
BLACK = $(VENV)/bin/black
PYLINT = $(VENV)/bin/pylint
DOCKER_COMPOSE = docker compose

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development environment setup
setup: ## Create virtual environment and install dependencies
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

clean: ## Remove virtual environment and cache files
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type f -name "coverage.xml" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".eggs" -exec rm -rf {} +
	find . -type f -name "*.egg-info" -exec rm -rf {} +

# Testing and code quality
test: ## Run tests with coverage
	$(PYTEST) tests/ -v --cov=src --cov-report=term-missing

lint: ## Run pylint
	$(PYLINT) src/ tests/ app.py

format: ## Format code with black
	$(BLACK) src/ tests/ app.py

# Docker commands
docker-build: ## Build Docker images
	$(DOCKER_COMPOSE) build

docker-up: ## Start Docker containers in detached mode
	$(DOCKER_COMPOSE) up -d

docker-down: ## Stop Docker containers
	$(DOCKER_COMPOSE) down

docker-logs: ## View Docker container logs
	$(DOCKER_COMPOSE) logs -f

docker-ps: ## List running Docker containers
	$(DOCKER_COMPOSE) ps

docker-test: ## Run tests in Docker container
	$(DOCKER_COMPOSE) run --rm test

docker-clean: ## Remove Docker containers, images, and volumes
	$(DOCKER_COMPOSE) down -v --rmi all

docker-shell: ## Open a shell in the web container
	$(DOCKER_COMPOSE) exec web /bin/bash

# Database commands
db-init: ## Initialize the database
	$(DOCKER_COMPOSE) exec web flask db init

db-migrate: ## Create a new database migration
	$(DOCKER_COMPOSE) exec web flask db migrate

db-upgrade: ## Apply database migrations
	$(DOCKER_COMPOSE) exec web flask db upgrade

db-downgrade: ## Rollback database migration
	$(DOCKER_COMPOSE) exec web flask db downgrade

db-shell: ## Open PostgreSQL shell
	$(DOCKER_COMPOSE) exec db psql -U awsuser -d awsprofiles

# Migration commands
migrate-create: ## Create a new migration file (usage: make migrate-create name=migration_name)
	@if [ -z "$(name)" ]; then \
		echo "Error: migration name not provided. Usage: make migrate-create name=migration_name"; \
		exit 1; \
	fi
	@echo "-- Migration: $(name)" > migrations/$(shell date +%Y%m%d%H%M%S)_$(name).sql
	@echo "Created new migration file: migrations/$(shell date +%Y%m%d%H%M%S)_$(name).sql"

migrate-run: ## Run database migrations
	$(DOCKER_COMPOSE) up migrations

migrate-status: ## Check migration status
	$(DOCKER_COMPOSE) exec db psql -U awsuser -d awsprofiles -c "SELECT * FROM aws_profiles;"

# Combined commands
dev-setup: docker-build docker-up migrate-run ## Set up development environment with Docker

dev-clean: docker-down docker-clean clean ## Clean up development environment

all: clean setup format lint test ## Clean, setup, format, lint, and test 