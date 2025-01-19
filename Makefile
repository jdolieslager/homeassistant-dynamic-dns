.PHONY: help test lint validate clean _build

# Default target when no arguments are given
help:
	@echo "Dynamic DNS Integration - Available targets:"
	@echo
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

# Internal target for building the Docker image
_build:
	docker compose build

test: _build ## Run tests in Docker
	docker compose up --exit-code-from test

lint: _build ## Run code linting in Docker
	docker compose run --rm test pylint custom_components/dynamic_dns

validate:  ## Run hassfest validation in Docker
	docker run --rm -v ./://github/workspace ghcr.io/home-assistant/hassfest

clean: ## Clean up temporary files and Docker artifacts
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name "*.egg" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".tox" -exec rm -r {} +
	find . -type d -name ".eggs" -exec rm -r {} +
	docker compose down --rmi all -v --remove-orphans 