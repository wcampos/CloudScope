.PHONY: build up run down stop logs ps clean test test-code lint format lint-api format-api lint-frontend format-frontend uv sync install install-dev setup ensure-python ensure-node ensure-venv migrate help api frontend migrations db redis

# Default target
help:
	@echo "Available commands:"
	@echo "  make setup     - Create .venv, install Python + frontend deps (run once after clone)"
	@echo "  make build [api|frontend|migrations] - Build all or one image"
	@echo "  make up [api|frontend|db|...]         - Start all or one service (alias: make run)"
	@echo "  make run [api|frontend|db|...]        - Same as make up"
	@echo "  make stop [api|frontend|db|...]      - Stop all or one service"
	@echo "  make down     - Stop and remove all containers"
	@echo "  make logs     - View logs from all containers"
	@echo "  make ps       - List running containers"
	@echo "  make clean    - Remove all containers, volumes, and images"
	@echo "  make test     - Run tests (pytest in API container)"
	@echo "  make test-code - Run tests (alias for make test)"
	@echo "  make lint     - Lint Python (api, tests) and frontend"
	@echo "  make format   - Format Python (api, tests) and frontend"
	@echo "  make lint-api - Lint Python only (ruff)"
	@echo "  make format-api - Format Python only (ruff)"
	@echo "  make install-dev - Install dev deps into .venv (ruff; no uv required)"
	@echo "  make uv        - Install Python deps with uv if available (optional)"
	@echo "  make install  - Same as make uv"
	@echo "  make lint-frontend - Lint frontend only (eslint)"
	@echo "  make format-frontend - Format frontend only (prettier)"
	@echo "  make migrate  - Run database migrations"
	@echo "  make health-check - Curl API /health (port 5001)"
	@echo "  make check-api    - Full connection check (direct + proxy); use after 'make up'"
	@echo "  make help     - Show this help message"

# Dummy targets so "make build api", "make up api", "make stop api" don't fail
api frontend migrations db redis:
	@true

# Build: make build [api|frontend|migrations]
build:
	docker-compose build $(filter-out build,$(MAKECMDGOALS))

# Start: make up [service] or make run [service]
up run:
	docker-compose up -d $(filter-out up run,$(MAKECMDGOALS))

# Stop: make stop [service]
stop:
	docker-compose stop $(filter-out stop,$(MAKECMDGOALS))

# Stop and remove all containers
down:
	docker-compose down

# View container logs
logs:
	docker-compose logs -f

# List running containers
ps:
	docker-compose ps

# Clean up everything
clean:
	docker-compose down -v
	docker system prune -f
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

# Run tests (api container; tests mounted at /app/tests)
test test-code:
	docker-compose exec api python -m pytest /app/tests -v

# Lint and format (run from repo root; Python: pip install ruff; frontend: npm install)
lint: lint-api lint-frontend
format: format-api format-frontend

# Ensure Python and Node are available (brew on macOS)
ensure-python:
	@command -v python3 >/dev/null 2>&1 || (command -v brew >/dev/null 2>&1 || (echo "Install Homebrew first: https://brew.sh" && exit 1); echo "Installing Python (brew)..." && brew install python)
ensure-node:
	@command -v npm >/dev/null 2>&1 || (command -v brew >/dev/null 2>&1 || (echo "Install Homebrew first: https://brew.sh" && exit 1); echo "Installing Node (brew)..." && brew install node)

# Create .venv if missing (avoids PEP 668 externally-managed-environment)
ensure-venv: ensure-python
	@[ -d .venv ] || (echo "Creating .venv..." && python3 -m venv .venv)

# Install dev deps into .venv (works without uv; respects PEP 668)
install-dev: ensure-venv
	@.venv/bin/pip install ruff

# Install all required deps for development (Python in .venv + frontend); installs Python/Node via brew if missing
setup: ensure-venv ensure-node
	@echo "Installing Python deps (ruff) into .venv..."
	@.venv/bin/pip install ruff
	@echo "Installing API Python deps into .venv..."
	@.venv/bin/pip install -r api/requirements.txt
	@echo "Installing frontend deps..."
	@cd frontend && npm install
	@echo "Done. Run: make lint, make format, make up  (Python tools use .venv)"

# Optional: install Python deps with uv if you have it
uv install:
	@if command -v uv >/dev/null 2>&1; then uv sync; else echo "uv not installed. Run: make install-dev  (or pip install ruff)"; fi

lint-api:
	@echo "Linting Python (api, tests) with ruff..."
	@([ -f .venv/bin/ruff ] && .venv/bin/ruff check api tests) || (command -v ruff >/dev/null 2>&1 && ruff check api tests) || (command -v uv >/dev/null 2>&1 && uv run ruff check api tests) || (echo "Run: make setup  or  make install-dev" && exit 1)

format-api:
	@echo "Formatting Python (api, tests) with ruff..."
	@([ -f .venv/bin/ruff ] && .venv/bin/ruff format api tests) || (command -v ruff >/dev/null 2>&1 && ruff format api tests) || (command -v uv >/dev/null 2>&1 && uv run ruff format api tests) || (echo "Run: make setup  or  make install-dev" && exit 1)

lint-frontend:
	@echo "Linting frontend..."
	@cd frontend && npm run lint 2>/dev/null || (echo "Install: cd frontend && npm install" && exit 1)

format-frontend:
	@echo "Formatting frontend..."
	@cd frontend && npm run format 2>/dev/null || (echo "Install: cd frontend && npm install" && exit 1)

# Run database migrations
migrate:
	docker-compose run --rm migrations

# Development shortcuts
dev-api:
	docker-compose logs -f api

dev-frontend:
	docker-compose logs -f frontend

dev-db:
	docker-compose logs -f db

# Database management
db-shell:
	docker-compose exec db psql -U cloudscope -d cloudscope

db-backup:
	@echo "Creating database backup..."
	@docker-compose exec db pg_dump -U cloudscope cloudscope > backup-$$(date +%Y%m%d-%H%M%S).sql

db-restore:
	@if [ -z "$$FILE" ]; then \
		echo "Please specify the backup file: make db-restore FILE=<backup-file>"; \
		exit 1; \
	fi
	@echo "Restoring database from $$FILE..."
	@docker-compose exec -T db psql -U cloudscope cloudscope < $$FILE

# Rebuild and restart specific services
restart-api:
	docker-compose up -d --build api

restart-frontend:
	docker-compose up -d --build frontend

# View service health (API must be reachable at localhost:5001, e.g. via 'docker compose up -d')
health-check:
	@curl -sf http://localhost:5001/health && echo "" || (echo "FAILED: API not reachable. Run: docker compose up -d" && exit 1)
	@echo "Frontend (Docker): http://localhost:3000  |  Dev: npm run dev then http://localhost:5173"

# Full API connection check (direct + via frontend proxy)
check-api:
	@./scripts/check-api.sh 