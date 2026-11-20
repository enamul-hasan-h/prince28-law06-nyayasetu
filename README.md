# NyayaSetu

[![CI](https://github.com/enamul-hasan-h/prince28-law06-nyayasetu/actions/workflows/ci.yml/badge.svg)](https://github.com/enamul-hasan-h/prince28-law06-nyayasetu/actions/workflows/ci.yml)
[![Live](https://img.shields.io/website?url=https%3A%2F%2Fnyayasetu-9ck6.onrender.com%2Fhealth&label=live)](https://nyayasetu-9ck6.onrender.com/docs)

NyayaSetu helps para-legal volunteers identify who qualifies for free legal aid, which authority to approach, and which NALSA scheme applies, in Tamil and English.

**Status:** Week 1 complete - CI/CD configured - Live: https://nyayasetu-9ck6.onrender.com

## Who it's for

Para-legal volunteers at a Taluk Legal Services Committee in Villupuram who help villagers access free legal assistance.

## The problem

Many people who are legally entitled to free legal aid are unaware of their rights or how to access these services.

Para-legal volunteers often struggle to navigate multiple laws, NALSA regulations, eligibility criteria, and legal aid schemes to provide accurate guidance. The challenge becomes greater when villagers communicate in Tamil, while most legal resources are available in English.

This creates a gap between people who need legal assistance and the services designed to support them.

## Data sources

- Legal Services Authorities Act, 1987
- NALSA (Free and Competent Legal Services) Regulations
- NALSA schemes
- Lok Adalat FAQs
- Victim compensation schemes

Official sources:

- [National Legal Services Authority](https://nalsa.gov.in/)
- [India Code](https://www.indiacode.nic.in/)

**Terms:** Public law and scheme documents.

## Hardest problem (my interview story)

**Eligibility and language:** Section 12 categories and income limits that differ by state must be applied correctly in code. Questions may arrive in Tamil, so document retrieval must work across both Tamil and English.

## Signature feature

**Eligibility check in Tamil:** Answer six simple questions in Tamil or English to understand whether free legal aid may apply and where to approach for assistance.

## Technology stack

- **Backend:** Python 3.12, FastAPI
- **Database:** PostgreSQL with pgvector
- **ORM and migrations:** SQLAlchemy, Alembic
- **Configuration:** Pydantic Settings
- **Testing:** pytest, pytest-asyncio, pytest-cov
- **Code quality:** Ruff, pre-commit
- **Package management:** uv
- **Task runner:** Poe the Poet
- **Containerization:** Docker, Docker Compose
- **Cache service:** Redis

## Run locally

### Prerequisites

- Python 3.12+
- uv
- PostgreSQL

### Setup

Install project dependencies:

```bash
uv sync --dev
```

Create your environment file.

**Windows PowerShell:**

```powershell
Copy-Item .env.example .env
```

**Linux/macOS:**

```bash
cp .env.example .env
```

Configure `DATABASE_URL` in `.env` with your PostgreSQL connection string.

Run the application:

```bash
uv run uvicorn nyayasetu.api.main:create_app --factory --reload
```

Open the API documentation:

[http://localhost:8000/docs](http://localhost:8000/docs)

## Run with Docker Compose

### Prerequisites

- Docker Desktop
- Docker Compose

Build and start the services:

```bash
docker compose up --build -d
```

The Compose stack includes:

| Service | Purpose |
|---|---|
| `api` | FastAPI application |
| `db` | PostgreSQL with pgvector |
| `redis` | Redis service |
| `migrate` | Runs database migrations and loads sample data |

Check service status:

```bash
docker compose ps -a
```

Check application health:

```powershell
curl.exe http://localhost:8000/health
curl.exe http://localhost:8000/ready
```

Useful Docker commands:

```bash
docker compose logs -f
docker compose down
```

Service ports:

- API: `8000`
- PostgreSQL: `5433`
- Redis: `6379`

**Note:** `docker compose down` preserves database data. Use `docker compose down -v` only when you intentionally want to delete the PostgreSQL volume and its data.

## Testing

Tests are separated into unit and integration suites.

Run the unit tests:

```bash
uv run poe test-unit
```

Run the integration tests:

```bash
uv run poe test-integration
```

Run all tests:

```bash
uv run poe test
```

Generate test coverage:

```bash
uv run poe coverage
```

### Integration test database

Integration tests use a dedicated PostgreSQL database named `app_test`.

The Compose initialization configuration creates this database when the PostgreSQL volume is initialized for the first time.

The integration test runner automatically:

1. Drops and recreates the dedicated test database.
2. Applies all Alembic migrations.
3. Runs the integration tests.

**Windows PowerShell:**

Before running the integration tests, configure the two required PostgreSQL connection environment variables in your local PowerShell session. Refer to `scripts/run_integration_tests.py` for their exact names and validation requirements.

Then run:

```powershell
uv run poe test-integration
```

The administrative connection must target the `postgres` database, while the test connection must target `app_test`. The runner validates the configuration before resetting the dedicated test database.

Integration tests skip automatically when the required test database configuration is not available.

## Code quality

Run lint checks:

```bash
uv run poe lint
```

Format the code:

```bash
uv run poe format
```

Check formatting without modifying files:

```bash
uv run ruff format --check .
```

Run the combined lint and test checks:

```bash
uv run poe check
```

## Makefile

Common development commands are also available through the Makefile on systems with GNU Make installed.

```bash
make install
make test
make test-unit
make test-integration
make coverage
make lint
make format
make check
make up
make down
make logs
```

On Windows without GNU Make, use the equivalent `uv run poe` commands.

## Target metrics

- Eligibility accuracy: 95%+ across 30 test scenarios.
- Tamil-English accuracy gap: within 5 percentage points.
- Document lookup speed: p95 under 500 ms.
- Full answer generation: p95 under 6 seconds.
- First-token response time: under 2 seconds.
- Cost: under ₹0.75 per answered question.
- Availability: 99% monthly uptime of the live URL.

## Target adjustments

I adjusted the document lookup target from 300 ms to 500 ms, full answer generation from 4 seconds to 6 seconds, first-token response time from 1.5 seconds to 2 seconds, and cost from ₹0.50 to ₹0.75 per question.

These targets allow realistic processing time for bilingual Tamil-English legal document retrieval while keeping NyayaSetu affordable and responsive.
