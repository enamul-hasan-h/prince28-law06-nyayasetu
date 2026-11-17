# Requirements: NyayaSetu

## Functional (what it does)

1. A user can ask a question in plain English or Tamil and get an answer drawn from my official legal sources.
2. Every answer cites the document and page number or legal section it came from.
3. If the documents do not contain the answer, the product says "I don't know" instead of guessing.
4. Signature feature: Eligibility check in Tamil or English: answer 6 simple questions and see whether free legal aid applies and where to go.
5. A user can browse and search the underlying records through GET /v1/documents.

## Non-functional (how well, with numbers)

| # | Quality | Target | How I will measure it |
|---|---|---|---|
| 1 | Speed: record lookups | p95 under 500 ms for GET /v1/documents | Load test (Week 6) |
| 2 | Speed: answers | p95 under 6 seconds for a full answer; first token under 2 seconds | Traces (Week 5) |
| 3 | Accuracy | Eligibility correct for 95%+ of 30 scenarios; Tamil questions answered within 5 percentage points of English accuracy. | Golden question set (Weeks 4 and 5) |
| 4 | Cost | Under Rs. 0.75 per answered question | llm_calls table (Week 2) |
| 5 | Availability | 99% monthly uptime of the live URL | Uptime monitor from Day 5 |