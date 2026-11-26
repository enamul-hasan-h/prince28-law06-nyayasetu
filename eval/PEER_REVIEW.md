# Peer Review: NyayaSetu – 20-Question Classification Test Set

**Project:** NyayaSetu

**Review date:** 26 November 2026

**Reviewer:** Classmate

**Review status:** Completed

**Review outcome:** Accepted – No changes recommended
## 1. Review Objective

The purpose of this peer review was to independently check the expected classifications of the 20 questions in `eval/prompt_testset.jsonl`.

The reviewer assessed whether each question was correctly assigned to one of the three routing categories:

- **docs:** The collected legal-aid documents can answer the question.
- **personal:** The question requires live information or private, individual case details.
- **off_topic:** The question is unrelated to NyayaSetu's legal-aid purpose.

## 2. Review Findings

| Question range | Expected label | Reviewer feedback |
|---|---|---|
| Q1–Q5 | `docs` | Correct. These questions can be answered using legal-aid documents. |
| Q6 | `personal` | Correct. The next Lok Adalat date requires current information. |
| Q7–Q10 | `docs` | Correct. These concern legal-aid eligibility and available schemes. |
| Q11–Q14 | `personal` | Correct. These require individual case status, hearing information, or predictions. |
| Q15–Q19 | `off_topic` | Correct. These questions are unrelated to NyayaSetu's legal-aid purpose. |
| Q20 | `personal` | Correct. Although it concerns legal aid, it asks for private application status and lawyer assignment information. |

## 3. Overall Feedback

The reviewer found that the test set appropriately covers all three classification categories. It includes straightforward legal questions, multi-step legal-aid questions, live-information requests, private case-status questions, and unrelated questions.

Question 20 was highlighted as a useful difficult example because it combines a legal-aid topic with a request for personal application information.

## 4. Review Outcome

**Recommendation:** Keep the current labels. No changes are suggested.

All 20 expected classifications were accepted by the reviewer. No modifications to the test-set labels were required as a result of this review.

## 5. Project Record

The peer-review feedback is documented as part of the Day 09 prompt-testing work.

**Related files:**
- `eval/prompt_testset.jsonl` – The 20-question classification test set.
- `prompts/classify_v3.md` – The router prompt containing independent examples.
- `tests/unit/test_classify.py` – Unit tests for classification and prompt handling.
