# NyayaSetu

Helps para-legal volunteers find out who qualifies for free legal aid, which authority to approach and which NALSA scheme applies, in Tamil and English.

**Status:** Day 1 foundation (FastAPI skeleton, quality gates). Live URL from Day 5.

## Who it's for

Para-legal volunteer at a taluk legal services committee in Villupuram who helps villagers get free legal help.

## The problem

Many people who are legally entitled to free legal aid are unaware of their rights or how to access these services. Para-legal volunteers often struggle to navigate multiple laws, NALSA regulations, eligibility criteria, and legal aid schemes to provide accurate guidance. The challenge becomes greater when villagers communicate in Tamil, while most legal resources are available in English. This creates a gap between people who need legal assistance and the services designed to support them.

## Data sources

Legal Services Authorities Act, 1987, NALSA (Free and Competent Legal Services) Regulations, NALSA schemes, Lok Adalat FAQs, and victim compensation schemes.

- https://nalsa.gov.in/
- https://www.indiacode.nic.in/
- Terms: Public law and scheme documents.

## Hardest problem (my interview story)

Eligibility and language: Section 12 categories plus income limits that differ by state must be applied in code, and questions arrive in Tamil, so retrieval must work across Tamil and English.

## Signature feature

Eligibility check in Tamil: answer 6 simple questions in Tamil or English and see whether free legal aid applies and where to go.

## Target metrics

- Eligibility accuracy: 95%+ across 30 test scenarios.
- Tamil-English accuracy gap: within 5 percentage points.
- Document lookup speed: p95 under 500 ms.
- Full answer generation: p95 under 6 seconds.
- First-token response time: under 2 seconds.
- Cost: under ₹0.75 per answered question.
- Availability: 99% monthly uptime of the live URL.

## Run it locally

```bash
uv sync
cp .env.example .env   # Windows: copy .env.example .env
uv run uvicorn nyayasetu.api.main:create_app --factory --reload
```

Then open http://localhost:8000/docs

## Checks

```bash
uv run pytest
uv run ruff check .
```

## Target adjustments

I adjusted the document lookup target from 300 ms to 500 ms, full answer generation from 4 seconds to 6 seconds, first-token response time from 1.5 seconds to 2 seconds, and cost from ₹0.50 to ₹0.75 per question. These targets allow realistic processing time for bilingual Tamil-English legal document retrieval while keeping NyayaSetu affordable and responsive.