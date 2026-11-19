.PHONY: install test test-unit test-integration coverage lint format check up down logs

install:
	uv sync --dev

test:
	uv run poe test

test-unit:
	uv run poe test-unit

test-integration:
	uv run poe test-integration

coverage:
	uv run poe coverage

lint:
	uv run poe lint

format:
	uv run poe format

check:
	uv run poe check

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f
