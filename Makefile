.PHONY: help install dev test lint format clean docker-build docker-run docker-stop

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install pytest black flake8 mypy isort

test: ## Run tests
	pytest -v

lint: ## Run linting
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

format: ## Format code
	black . --line-length=88
	isort . --profile black

type-check: ## Run type checking
	mypy . --ignore-missing-imports

clean: ## Clean up cache files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/

run: ## Run the application locally
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

docker-build: ## Build Docker image
	docker build -t attendance-api .

docker-run: ## Run with Docker Compose
	docker-compose up -d

docker-stop: ## Stop Docker Compose
	docker-compose down

docker-logs: ## Show Docker logs
	docker-compose logs -f attendance-api

docker-shell: ## Access container shell
	docker-compose exec attendance-api /bin/bash

production-build: ## Build for production
	docker build -t attendance-api:latest .
	docker build -t attendance-api:$(shell git rev-parse --short HEAD) .

security-scan: ## Run security scan
	pip install safety bandit
	safety check
	bandit -r . -x tests/

setup-env: ## Setup environment file
	cp .env.example .env
	@echo "Please edit .env file with your configuration"
