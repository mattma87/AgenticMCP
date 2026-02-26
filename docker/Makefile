# AgenticMCP v2 - Makefile for Docker operations

.PHONY: help build up down restart logs ps token test clean

# Default target
help:
	@echo "AgenticMCP v2 - Docker Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  build       Build all Docker images"
	@echo "  up          Start all services (production)"
	@echo "  up-dev      Start all services (development with hot reload)"
	@echo "  down        Stop all services"
	@echo "  restart     Restart all services"
	@echo "  logs        Show logs from all services"
	@echo "  ps          Show running services"
	@echo "  token       Generate JWT tokens"
	@echo "  test        Run API tests"
	@echo "  clean       Remove all containers and volumes"
	@echo ""
	@echo "Service-specific:"
	@echo "  logs-backend     Show backend logs"
	@echo "  logs-postgres     Show postgres logs"
	@echo "  shell-backend     Open shell in backend container"

# Build images
build:
	docker-compose -f docker/docker-compose-v2.yml build

# Start services (production)
up:
	docker-compose -f docker/docker-compose-v2.yml up -d
	@echo "Services started. Backend: http://localhost:8000"
	@echo "API Documentation: http://localhost:8000/docs"

# Start services (development)
up-dev:
	docker-compose -f docker/docker-compose.dev.yml up -d
	@echo "Dev services started. Backend: http://localhost:8000"

# Stop services
down:
	docker-compose -f docker/docker-compose-v2.yml down
	docker-compose -f docker/docker-compose.dev.yml down

# Restart services
restart: down up

# View logs
logs:
	docker-compose -f docker/docker-compose-v2.yml logs -f

logs-backend:
	docker-compose -f docker/docker-compose-v2.yml logs -f backend

logs-postgres:
	docker-compose -f docker/docker-compose-v2.yml logs -f postgres

# Show running services
ps:
	docker-compose -f docker/docker-compose-v2.yml ps

# Generate JWT tokens
token:
	@echo "Generating JWT tokens..."
	docker-compose -f docker/docker-compose.dev.yml run --rm token-generator

# Run API tests
test:
	@echo "Testing API..."
	@curl -s http://localhost:8000/health | python -m json.tool
	@echo ""
	@echo "Testing /api/v1/users..."
	@curl -s http://localhost:8000/api/v1/users | python -m json.tool | head -20

# Clean everything
clean:
	docker-compose -f docker/docker-compose-v2.yml down -v
	docker-compose -f docker/docker-compose.dev.yml down -v
	docker rmi agenticmcp-backend agenticmcp-mcp 2>/dev/null || true
	@echo "All containers, volumes, and images removed"

# Initialize database
init-db:
	@echo "Initializing database..."
	docker-compose -f docker/docker-compose-v2.yml run --rm backend python -c "
import asyncio
from backend.main import init_database
asyncio.run(init_database())
"

# Open backend shell
shell-backend:
	docker-compose -f docker/docker-compose-v2.yml exec backend bash

# Rebuild and restart
rebuild: clean build up
