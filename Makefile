.PHONY: build up down logs ps clean test migrate help

# Default target
help:
	@echo "Available commands:"
	@echo "  make build    - Build all Docker images"
	@echo "  make up       - Start all containers"
	@echo "  make down     - Stop and remove all containers"
	@echo "  make logs     - View logs from all containers"
	@echo "  make ps       - List running containers"
	@echo "  make clean    - Remove all containers, volumes, and images"
	@echo "  make test     - Run tests"
	@echo "  make migrate  - Run database migrations"
	@echo "  make help     - Show this help message"

# Build Docker images
build:
	docker-compose build

# Start containers
up:
	docker-compose up -d

# Stop and remove containers
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

dev-ui:
	docker-compose logs -f ui

dev-db:
	docker-compose logs -f db

# Database management
db-shell:
	docker-compose exec db psql -U awsuser -d awsprofiles

db-backup:
	@echo "Creating database backup..."
	@docker-compose exec db pg_dump -U awsuser awsprofiles > backup-$$(date +%Y%m%d-%H%M%S).sql

db-restore:
	@if [ -z "$$FILE" ]; then \
		echo "Please specify the backup file: make db-restore FILE=<backup-file>"; \
		exit 1; \
	fi
	@echo "Restoring database from $$FILE..."
	@docker-compose exec -T db psql -U awsuser awsprofiles < $$FILE

# Rebuild and restart specific services
restart-api:
	docker-compose up -d --build api

restart-ui:
	docker-compose up -d --build ui

# View service health
health-check:
	@echo "Checking API health..."
	@curl -s http://localhost:5000/health
	@echo "\nChecking UI health..."
	@curl -s http://localhost:8000/health 