DOCKER_COMPOSE = docker compose
STOREFRONT_BACKEND_CONTAINER = storefront_catalog_service
PYTHON = python
MANAGE_PY = manage.py


.PHONY: up
up: ## Start all containers
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
