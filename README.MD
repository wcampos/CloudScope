# AWS Inventory Management System

A containerized web application for managing and monitoring AWS resources across multiple accounts and regions.

## Architecture

The application is split into three main components:

1. **API Service (Port 5000)**
   - Handles AWS resource management
   - Provides RESTful endpoints
   - Manages database operations
   - Built with Flask-RESTful and SQLAlchemy

2. **UI Service (Port 8000)**
   - Provides web interface
   - Communicates with API service
   - Handles user interactions
   - Built with Flask and Bootstrap

3. **Database Service**
   - PostgreSQL database
   - Stores AWS profile information
   - Manages application state

## Prerequisites

- Docker and Docker Compose
- Make (optional, but recommended)
- AWS credentials with appropriate permissions

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/aws_inventory.git
   cd aws_inventory
   ```

2. Start the application:
   ```bash
   make up
   ```

3. Access the application:
   - Web UI: http://localhost:8000
   - API: http://localhost:5000

## Available Make Commands

- `make build` - Build all Docker images
- `make up` - Start all containers
- `make down` - Stop and remove all containers
- `make logs` - View logs from all containers
- `make ps` - List running containers
- `make clean` - Remove all containers, volumes, and images
- `make test` - Run tests
- `make migrate` - Run database migrations

Development shortcuts:
- `make dev-api` - View API service logs
- `make dev-ui` - View UI service logs
- `make dev-db` - View database logs

Database management:
- `make db-shell` - Open PostgreSQL shell
- `make db-backup` - Create database backup
- `make db-restore FILE=<backup-file>` - Restore database from backup

Service management:
- `make restart-api` - Rebuild and restart API service
- `make restart-ui` - Rebuild and restart UI service
- `make health-check` - Check services health

## API Endpoints

### Profiles
- `GET /api/profiles` - List all AWS profiles
- `POST /api/profiles` - Create new AWS profile
- `GET /api/profiles/<id>` - Get specific profile
- `PUT /api/profiles/<id>` - Update profile
- `DELETE /api/profiles/<id>` - Delete profile

### AWS Resources
- `GET /api/resources` - Get AWS resources for active profile

### Health Check
- `GET /health` - Service health status

## Development

### Project Structure
```
aws_inventory/
├── api/
│   ├── app.py
│   ├── aws_classes.py
│   ├── models.py
│   ├── migrations/
│   └── requirements.txt
├── ui/
│   ├── app.py
│   ├── templates/
│   ├── static/
│   └── requirements.txt
├── docker-compose.yml
├── Makefile
└── README.md
```

### Adding New Features

1. API Changes:
   - Add new endpoints in `api/app.py`
   - Update models in `api/models.py`
   - Create database migrations if needed

2. UI Changes:
   - Add new routes in `ui/app.py`
   - Create/update templates in `ui/templates/`
   - Add static files in `ui/static/`

### Database Migrations

1. Create a new migration:
   ```bash
   make migrate
   ```

2. Apply migrations:
   ```bash
   make up
   ```

## Configuration

Environment variables:
- `FLASK_ENV` - Environment (development/production)
- `DATABASE_URL` - PostgreSQL connection URL
- `API_BASE_URL` - API service URL
- `FLASK_SECRET_KEY` - Flask session secret key

## Security

- AWS credentials are stored securely in the database
- All sensitive data is encrypted at rest
- CORS is enabled for API service
- Non-root users are used in containers

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.


