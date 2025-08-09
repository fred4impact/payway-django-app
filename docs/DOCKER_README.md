# Docker Setup for PayWay Django Application

This document provides comprehensive instructions for building, running, and deploying the PayWay Django application using Docker.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 4GB RAM available for Docker
- Git

## Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd payway-django-app
```

### 2. Environment Configuration

Create a `.env` file in the root directory:

```bash
# Django Settings
SECRET_KEY=your-super-secret-key-change-in-production
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database
DATABASE_URL=postgresql://payway_user:payway_password@db:5432/payway_db
POSTGRES_DB=payway_db
POSTGRES_USER=payway_user
POSTGRES_PASSWORD=payway_password

# Redis
REDIS_URL=redis://redis:6379/0

# Security
DJANGO_SETTINGS_MODULE=payway.settings
```

### 3. Build and Run

```bash
# Build the application
docker-compose build

# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f web
```

### 4. Initial Setup

```bash
# Run database migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

## Docker Commands Reference

### Building Images

```bash
# Build specific service
docker-compose build web

# Build with no cache
docker-compose build --no-cache web

# Build production image
docker build -t payway:latest .
```

### Running Services

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d web

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Restart service
docker-compose restart web
```

### Managing Data

```bash
# View running containers
docker-compose ps

# Execute commands in container
docker-compose exec web python manage.py shell

# View logs
docker-compose logs web
docker-compose logs -f web

# Backup database
docker-compose exec db pg_dump -U payway_user payway_db > backup.sql

# Restore database
docker-compose exec -T db psql -U payway_user payway_db < backup.sql
```

## Service Architecture

### Web Service (Django)
- **Port**: 8000
- **Image**: Built from local Dockerfile
- **Dependencies**: Database, Redis
- **Health Check**: `/health/` endpoint

### Database (PostgreSQL)
- **Port**: 5432
- **Image**: postgres:15-alpine
- **Data**: Persistent volume
- **Health Check**: Connection test

### Redis
- **Port**: 6379
- **Image**: redis:7-alpine
- **Data**: Persistent volume
- **Health Check**: PING command

### Nginx
- **Ports**: 80 (HTTP), 443 (HTTPS)
- **Image**: nginx:alpine
- **Features**: Reverse proxy, static files, SSL termination

### Celery (Optional)
- **Worker**: Background task processing
- **Beat**: Scheduled task management

## Production Deployment

### 1. Production Dockerfile

The production Dockerfile includes:
- Multi-stage build for optimization
- Security hardening (non-root user)
- Health checks
- Optimized Python environment

### 2. Environment Variables

```bash
# Production settings
DEBUG=False
SECRET_KEY=<strong-secret-key>
ALLOWED_HOSTS=<your-domain.com>
DATABASE_URL=<production-db-url>
REDIS_URL=<production-redis-url>
```

### 3. SSL Configuration

Place your SSL certificates in `nginx/ssl/`:
- `cert.pem` - SSL certificate
- `key.pem` - Private key

### 4. Scaling

```bash
# Scale web service
docker-compose up -d --scale web=3

# Scale celery workers
docker-compose up -d --scale celery=2
```

## Development Workflow

### 1. Development Mode

```bash
# Start development services
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Run tests
docker-compose exec web python manage.py test

# Run development server
docker-compose exec web python manage.py runserver 0.0.0.0:8000
```

### 2. Code Changes

```bash
# Rebuild after code changes
docker-compose build web
docker-compose up -d web

# Or use volume mounting for development
docker-compose -f docker-compose.dev.yml up -d
```

### 3. Database Management

```bash
# Reset database
docker-compose down -v
docker-compose up -d db
docker-compose exec web python manage.py migrate

# Load fixtures
docker-compose exec web python manage.py loaddata initial_data.json
```

## Monitoring and Logging

### 1. Health Checks

```bash
# Check application health
curl http://localhost/health/

# Check database health
docker-compose exec db pg_isready -U payway_user

# Check Redis health
docker-compose exec redis redis-cli ping
```

### 2. Logs

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs web
docker-compose logs nginx

# Follow logs in real-time
docker-compose logs -f web
```

### 3. Performance Monitoring

```bash
# Container resource usage
docker stats

# Service status
docker-compose ps

# Network inspection
docker network inspect payway-django-app_payway-network
```

## Troubleshooting

### Common Issues

#### 1. Port Conflicts
```bash
# Check port usage
sudo netstat -tulpn | grep :8000

# Change ports in docker-compose.yml
ports:
  - "8001:8000"  # Use port 8001 instead
```

#### 2. Permission Issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# Fix Docker volume permissions
docker-compose exec web chown -R appuser:appuser /app
```

#### 3. Database Connection Issues
```bash
# Check database status
docker-compose exec db pg_isready -U payway_user

# Reset database
docker-compose down -v
docker-compose up -d db
```

#### 4. Memory Issues
```bash
# Check Docker memory usage
docker system df

# Clean up unused resources
docker system prune -a

# Increase Docker memory limit in Docker Desktop
```

### Debug Commands

```bash
# Inspect container
docker-compose exec web bash

# Check Django settings
docker-compose exec web python manage.py check

# Verify static files
docker-compose exec web python manage.py collectstatic --dry-run

# Test database connection
docker-compose exec web python manage.py dbshell
```

## Security Considerations

### 1. Environment Variables
- Never commit `.env` files to version control
- Use strong, unique secrets in production
- Rotate secrets regularly

### 2. Network Security
- Use internal Docker networks
- Limit exposed ports
- Implement rate limiting

### 3. Container Security
- Run containers as non-root users
- Keep base images updated
- Scan images for vulnerabilities

### 4. Data Security
- Encrypt sensitive data
- Use secure database connections
- Implement proper backup strategies

## Backup and Recovery

### 1. Database Backup

```bash
# Create backup
docker-compose exec db pg_dump -U payway_user payway_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T db pg_dump -U payway_user payway_db > $BACKUP_DIR/backup_$DATE.sql
```

### 2. Volume Backup

```bash
# Backup volumes
docker run --rm -v payway-django-app_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_data_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .

# Restore volumes
docker run --rm -v payway-django-app_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_data_20231201_120000.tar.gz -C /data
```

## Performance Optimization

### 1. Docker Optimizations

```bash
# Use build cache
docker-compose build --parallel

# Optimize image layers
# Use multi-stage builds (already implemented)

# Use appropriate base images
# python:3.11-slim for production
```

### 2. Application Optimizations

```bash
# Enable Django caching
# Configure Redis as cache backend

# Use CDN for static files
# Configure django-storages

# Database optimization
# Use connection pooling
# Implement query optimization
```

## Next Steps

1. **Production Deployment**: Configure production environment variables
2. **SSL Setup**: Obtain and configure SSL certificates
3. **Monitoring**: Implement application monitoring and alerting
4. **CI/CD**: Set up automated deployment pipeline
5. **Backup Strategy**: Implement automated backup and recovery
6. **Scaling**: Plan for horizontal scaling and load balancing

## Support

For issues and questions:
- Check Docker logs: `docker-compose logs`
- Review Django logs in the application
- Check system resources: `docker stats`
- Consult Django and Docker documentation
