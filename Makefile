DOCKER_COMPOSE = docker compose
STOREFRONT_BACKEND_CONTAINER = storefront_catalog_service
PYTHON = python
MANAGE_PY = manage.py

.DEFAULT_GOAL := help

# =============================================================================
# Main Commands
# =============================================================================
.PHONY: help
help: ## Show this help
	@echo "Usage: make [target]"
	@echo ""
	@echo "🚀 Quick Start:"
	@echo "  make init    - First time: install deps, build, start"
	@echo "  make up       - Start containers (subsequent runs)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

.PHONY: init
init: ## First time setup: install deps, build and start containers
	@if [ ! -f .env ]; then \
		echo "📄 Creating .env from .env.example..."; \
		cp .env.example .env; \
	fi
	@echo "📦 Installing backend dev dependencies..."
	cd storefront_catalog_service && uv sync --extra dev
	@echo "📦 Installing frontend dependencies..."
	cd storefront_catalog_service_frontend/app && npm install
	@echo "📦 Installing pre-commit hooks..."
	@command -v pre-commit >/dev/null 2>&1 || pip install pre-commit
	pre-commit install
	@echo "🔨 Building containers..."
	$(DOCKER_COMPOSE) build
	@echo "🚀 Starting containers..."
	$(DOCKER_COMPOSE) up -d
	@echo ""
	cd storefront_catalog_service_frontend/app && npm run dev
	@echo "🎉 Project started successfully! (temporally not reachable because of react starting not in docker) "

.PHONY: up
up: ## Start containers (for subsequent runs)
	$(DOCKER_COMPOSE) up -d

.PHONY: down
down: ## Stop all containers
	$(DOCKER_COMPOSE) down

.PHONY: build
build: ## Build Docker images
	$(DOCKER_COMPOSE) build

.PHONY: rebuild
rebuild: ## Rebuild images and start
	$(DOCKER_COMPOSE) up -d --build

.PHONY: restart
restart: down up ## Restart all containers

.PHONY: logs
logs: ## Show container logs
	$(DOCKER_COMPOSE) logs -f

# =============================================================================
# Pre-commit
# =============================================================================

.PHONY: pre-commit
pre-commit: ## Run pre-commit on all files
	pre-commit run --all-files

# =============================================================================
# Django Commands
# =============================================================================

.PHONY: shell
shell: ## Open shell in backend container
	docker exec -it $(STOREFRONT_BACKEND_CONTAINER) sh

.PHONY: bash
bash: ## Open bash in backend container
	docker exec -it $(STOREFRONT_BACKEND_CONTAINER) bash

.PHONY: makemigrations
makemigrations: ## Create Django migrations
	docker exec -it $(STOREFRONT_BACKEND_CONTAINER) $(PYTHON) $(MANAGE_PY) makemigrations

.PHONY: migrate
migrate: ## Apply Django migrations
	docker exec -it $(STOREFRONT_BACKEND_CONTAINER) $(PYTHON) $(MANAGE_PY) migrate

.PHONY: createsuperuser
createsuperuser: ## Create Django superuser
	docker exec -it $(STOREFRONT_BACKEND_CONTAINER) $(PYTHON) $(MANAGE_PY) createsuperuser

.PHONY: collectstatic
collectstatic: ## Collect static files
	docker exec -it $(STOREFRONT_BACKEND_CONTAINER) $(PYTHON) $(MANAGE_PY) collectstatic --noinput

.PHONY: shell-django
shell-django: ## Open Django shell
	docker exec -it $(STOREFRONT_BACKEND_CONTAINER) $(PYTHON) $(MANAGE_PY) shell

.PHONY: test
test: ## Run tests
	docker exec -it $(STOREFRONT_BACKEND_CONTAINER) $(PYTHON) $(MANAGE_PY) test
