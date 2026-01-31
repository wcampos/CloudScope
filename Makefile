.PHONY: build up run down stop logs ps clean test migrate help api frontend migrations db redis

# Default target
help:
	@echo "Available commands:"
	@echo "  make build [api|frontend|migrations] - Build all or one image"
	@echo "  make up [api|frontend|db|...]         - Start all or one service (alias: make run)"
	@echo "  make run [api|frontend|db|...]        - Same as make up"
	@echo "  make stop [api|frontend|db|...]      - Stop all or one service"
	@echo "  make down     - Stop and remove all containers"
	@echo "  make logs     - View logs from all containers"
	@echo "  make ps       - List running containers"
	@echo "  make clean    - Remove all containers, volumes, and images"
	@echo "  make test     - Run tests"
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

# Run tests
test:
	docker-compose exec api python -m pytest

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