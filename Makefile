# Makefile for PayWay Django Application
# Local development commands for Docker Compose

.PHONY: help build up down start stop restart logs clean shell web-shell db-shell redis-shell nginx-shell celery-shell migrate collectstatic test lint format

# Default target
help:
	@echo "PayWay Django Application - Docker Compose Commands"
	@echo "=================================================="
	@echo ""
	@echo "Available commands:"
	@echo "  build          - Build all Docker images"
	@echo "  up             - Start all services in detached mode (without Celery)"
	@echo "  up-with-celery - Start all services including Celery (requires install-celery)"
	@echo "  start          - Start all services (alias for up)"
	@echo "  down           - Stop and remove all containers, networks, and volumes"
	@echo "  stop           - Stop all services (alias for down)"
	@echo "  restart        - Restart all services"
	@echo "  logs           - Show logs from all services"
	@echo "  logs-follow    - Show logs with follow mode"
	@echo "  clean          - Stop containers and remove volumes (data will be lost)"
	@echo "  clean-all      - Stop containers, remove volumes and images"
	@echo ""
	@echo "Shell access:"
	@echo "  shell          - Access Django shell"
	@echo "  web-shell      - Access web container shell"
	@echo "  db-shell       - Access database shell"
	@echo "  redis-shell    - Access Redis shell"
	@echo "  nginx-shell    - Access Nginx container shell"
	@echo "  celery-shell   - Access Celery container shell"
	@echo ""
	@echo "Django management:"
	@echo "  migrate        - Run Django migrations"
	@echo "  makemigrations - Create new migrations"
	@echo "  collectstatic  - Collect static files"
	@echo "  createsuperuser - Create Django superuser"
	@echo "  test           - Run Django tests"
	@echo ""
	@echo "Development:"
	@echo "  lint           - Run code linting"
	@echo "  format         - Format code"
	@echo "  install-dev    - Install development dependencies"
	@echo "  install-celery - Install Celery for background tasks"
	@echo ""
	@echo "Monitoring:"
	@echo "  status         - Show container status"
	@echo "  ps             - Show running containers"
	@echo "  health         - Check service health"

# Build Docker images
build:
	@echo "Building Docker images..."
	docker-compose build

# Start all services in detached mode
up:
	@echo "Starting PayWay application..."
	@echo "Note: Celery services are disabled as Celery is not installed"
	docker-compose up -d web db redis nginx
	@echo "Application is starting up..."
	@echo "Web interface: http://localhost"
	@echo "Django admin: http://localhost:8000/admin"
	@echo "API endpoints: http://localhost:8000/api/"

# Alias for up
start: up

# Stop and remove containers, networks, and volumes
down:
	@echo "Stopping PayWay application..."
	docker-compose down

# Alias for down
stop: down

# Restart all services
restart:
	@echo "Restarting PayWay application..."
	docker-compose restart

# Show logs from all services
logs:
	docker-compose logs

# Show logs with follow mode
logs-follow:
	docker-compose logs -f

# Clean up containers and volumes (data will be lost)
clean:
	@echo "Cleaning up containers and volumes..."
	docker-compose down -v
	@echo "All data has been removed!"

# Clean up everything including images
clean-all:
	@echo "Cleaning up everything..."
	docker-compose down -v --rmi all
	@echo "All containers, volumes, and images have been removed!"

# Access Django shell
shell:
	docker-compose exec web python manage.py shell

# Access web container shell
web-shell:
	docker-compose exec web bash

# Access database shell
db-shell:
	docker-compose exec db psql -U payway_user -d payway_db

# Access Redis shell
redis-shell:
	docker-compose exec redis redis-cli

# Access Nginx container shell
nginx-shell:
	docker-compose exec nginx sh

# Access Celery container shell
celery-shell:
	docker-compose exec celery bash

# Run Django migrations
migrate:
	@echo "Running Django migrations..."
	docker-compose exec web python manage.py migrate

# Create new migrations
makemigrations:
	@echo "Creating new migrations..."
	docker-compose exec web python manage.py makemigrations

# Collect static files
collectstatic:
	@echo "Collecting static files..."
	docker-compose exec web python manage.py collectstatic --noinput

# Create Django superuser
createsuperuser:
	docker-compose exec web python manage.py createsuperuser

# Run Django tests
test:
	@echo "Running Django tests..."
	docker-compose exec web python manage.py test

# Run code linting
lint:
	@echo "Running code linting..."
	docker-compose exec web python -m flake8 .

# Format code
format:
	@echo "Formatting code..."
	docker-compose exec web python -m black .

# Install development dependencies
install-dev:
	@echo "Installing development dependencies..."
	docker-compose exec web pip install -r requirements-dev.txt

# Install Celery for background tasks
install-celery:
	@echo "Installing Celery and Redis dependencies..."
	@echo "Uncommenting Celery dependencies in requirements.txt..."
	@sed -i '' 's/# celery\[redis\]==5.3.4/celery[redis]==5.3.4/' requirements.txt
	@sed -i '' 's/# django-celery-beat==2.5.0/django-celery-beat==2.5.0/' requirements.txt
	@echo "Rebuilding container with Celery..."
	docker-compose build web
	@echo "Celery installed successfully!"
	@echo "You can now use 'make up-with-celery' to start all services including Celery"

# Start all services including Celery (after installing it)
up-with-celery:
	@echo "Starting PayWay application with Celery..."
	docker-compose up -d
	@echo "Application is starting up..."
	@echo "Web interface: http://localhost"
	@echo "Django admin: http://localhost:8000/admin"
	@echo "API endpoints: http://localhost:8000/api/"

# Show container status
status:
	@echo "Container status:"
	docker-compose ps

# Show running containers
ps: status

# Check service health
health:
	@echo "Checking service health..."
	@echo "Web service:"
	@curl -f http://localhost:8000/health/ || echo "Web service is not healthy"
	@echo ""
	@echo "Database service:"
	@docker-compose exec db pg_isready -U payway_user -d payway_db || echo "Database service is not healthy"
	@echo ""
	@echo "Redis service:"
	@docker-compose exec redis redis-cli ping || echo "Redis service is not healthy"

# Quick setup for first time
setup:
	@echo "Setting up PayWay application for the first time..."
	@echo "1. Building images..."
	@make build
	@echo "2. Starting services (without Celery)..."
	@make up
	@echo "3. Waiting for services to be ready..."
	@sleep 30
	@echo "4. Running migrations..."
	@make migrate
	@echo "5. Collecting static files..."
	@make collectstatic
	@echo ""
	@echo "Setup complete! Your application is ready at:"
	@echo "Web interface: http://localhost"
	@echo "Django admin: http://localhost:8000/admin"
	@echo ""
	@echo "Note: Celery is not installed. If you need background tasks, run:"
	@echo "  make install-celery"
	@echo "  make up-with-celery"

# Development mode with live reload (if you have a development setup)
dev:
	@echo "Starting development mode..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Production mode
prod:
	@echo "Starting production mode..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Backup database
backup:
	@echo "Creating database backup..."
	docker-compose exec db pg_dump -U payway_user payway_db > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Backup created successfully!"

# Restore database from backup
restore:
	@echo "Restoring database from backup..."
	@read -p "Enter backup filename: " backup_file; \
	docker-compose exec -T db psql -U payway_user -d payway_db < $$backup_file
	@echo "Database restored successfully!" 