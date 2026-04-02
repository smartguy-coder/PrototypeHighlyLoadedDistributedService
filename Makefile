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
	@echo "🎉 Project started successfully!"

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

# =============================================================================
# PyPI Package Publishing
# =============================================================================

PYPI_PACKAGE_DIR = pypi_package_utils

.PHONY: pypi-clean
pypi-clean: ## Clean PyPI package build artifacts
	@echo "🧹 Cleaning build artifacts..."
	cd $(PYPI_PACKAGE_DIR) && rm -rf dist/ build/ *.egg-info .pytest_cache/
	find $(PYPI_PACKAGE_DIR) -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Clean completed!"

.PHONY: pypi-test
pypi-test: ## Run tests for PyPI package
	@echo "🧪 Running tests..."
	cd $(PYPI_PACKAGE_DIR) && uv sync --extra dev
	cd $(PYPI_PACKAGE_DIR) && uv run pytest -v
	@echo "✅ Tests passed!"

.PHONY: pypi-build
pypi-build: ## Build PyPI package (wheel)
	@echo "🧹 Cleaning old builds..."
	cd $(PYPI_PACKAGE_DIR) && rm -rf dist/ build/ *.egg-info
	@echo "📦 Building wheel..."
	cd $(PYPI_PACKAGE_DIR) && uv build --wheel
	@echo "✅ Build completed!"

.PHONY: pypi-publish
pypi-publish: pypi-test pypi-build ## Run tests, build and publish package to PyPI
	@echo "🔍 Checking package..."
	cd $(PYPI_PACKAGE_DIR) && uv run twine check dist/*
	@echo "🚀 Publishing to PyPI (enter credentials when prompted)..."
	cd $(PYPI_PACKAGE_DIR) && uv run twine upload dist/*
	@echo "✅ Published! pip install prototype-highly-loaded-distributed-service-utils"
	$(MAKE) pypi-clean
