# AWS Inventory

[![Tests](https://github.com/wcampos/aws_inventory/actions/workflows/test.yml/badge.svg)](https://github.com/wcampos/aws_inventory/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/wcampos/aws_inventory/branch/main/graph/badge.svg)](https://codecov.io/gh/wcampos/aws_inventory)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-%23FE5196?logo=conventionalcommits&logoColor=white)](https://conventionalcommits.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Flask web application for viewing and managing AWS resources with a modern, responsive interface.

## Features

### Dashboard
- Unified view of all AWS resources
- Filter resources by category (Compute, Storage, Network)
- Interactive tables with sorting, searching, and pagination
- Responsive design for all devices

### AWS Services Support
- EC2 instances and related resources
  - Instance details and status
  - VPCs and Subnets
  - Security Groups and rules
- Database Services
  - RDS instances
  - DynamoDB tables
- Storage
  - S3 buckets with region information
- Serverless
  - Lambda functions with runtime details
- Load Balancing
  - Application Load Balancers
  - Target Groups

### Profile Management
- Multiple AWS profile support
- Secure credential storage
- Easy profile switching
- Region selection

## Requirements

- Python 3.13
- PostgreSQL database
- AWS credentials
- Docker (optional, for containerized deployment)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/wcampos/aws_inventory.git
cd aws_inventory
```

2. Set up environment variables:
```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your configuration
vim .env
```

The following environment variables are available:
- **Database Configuration**
  - `DATABASE_URL`: Complete database URL (optional, constructed from individual settings if not provided)
  - `DB_HOST`: Database host (default: localhost)
  - `DB_PORT`: Database port (default: 5432)
  - `DB_NAME`: Database name (default: awsprofiles)
  - `DB_USER`: Database user (default: awsuser)
  - `DB_PASSWORD`: Database password (default: awspass)
- **Flask Configuration**
  - `FLASK_APP`: Application entry point (default: app.py)
  - `FLASK_ENV`: Environment (development/production)
  - `SECRET_KEY`: Secret key for session management
- **Logging Configuration**
  - `LOG_LEVEL`: Logging level (default: INFO)
  - `LOG_FILE`: Log file path (default: logs/aws_inventory.log)
  - `LOG_MAX_BYTES`: Maximum log file size (default: 10240)
  - `LOG_BACKUP_COUNT`: Number of backup log files (default: 10)

3. Set up the development environment:
```bash
make setup
```
This will:
- Create a virtual environment
- Install dependencies
- Set up the database
- Run initial migrations

4. Configure your AWS credentials either through:
- AWS CLI: `aws configure`
- Web interface: Add profile through the application

## Usage

### Local Development
```bash
python app.py
```
Access the application at `http://localhost:5000`

### Docker Deployment
```bash
# Build and start services
make dev-setup

# Stop services
make docker-down
```

## Development

### Release Process

To create a new release:
1. Create a new branch with the format `release/X.Y.Z` (e.g., `release/1.0.0`)
2. Make your changes and update version numbers as needed
3. Create a PR with the same version in the title (e.g., "release/1.0.0: Description of changes")
4. When the PR is merged to main, a GitHub Action will automatically:
   - Create a new tag with the version number
   - Generate a ZIP file of the release
   - Create a GitHub Release with release notes

### Database Management
```bash
# Create a new migration
make migrate-create name=migration_name

# Run migrations
make migrate-run

# Check migration status
make migrate-status
```

### Testing
```bash
# Run all tests
make test

# Run with coverage
make test-coverage
```

### Code Quality
```bash
# Format code
make format

# Run linter
make lint

# Run all checks
make all
```

The project uses:
- Black for code formatting
- Pylint for code linting
- Pytest for testing
- Conventional Commits for commit messages

### Commit Message Format

This project follows [Conventional Commits](https://www.conventionalcommits.org/). Each commit message should be structured as follows:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:
- feat: A new feature
- fix: A bug fix
- docs: Documentation only changes
- style: Changes that do not affect the meaning of the code
- refactor: A code change that neither fixes a bug nor adds a feature
- test: Adding missing tests or correcting existing tests
- chore: Changes to the build process or auxiliary tools

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.


