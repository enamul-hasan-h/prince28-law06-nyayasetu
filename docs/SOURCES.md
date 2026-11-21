# NyayaSetu – Official Legal Sources

## 1. Purpose

This document maintains the official legal and institutional sources identified for NyayaSetu.

NyayaSetu uses these sources as references for legal information, eligibility guidance, Lok Adalat information and legal aid schemes.

**Important:** Listing a source here does not mean that its document has already been downloaded, processed or indexed in the database.

## 2. Official Sources

### S01 – Legal Services Authorities Act, 1987

- **Authority:** Government of India
- **Official source:** India Code
- **URL:** https://www.indiacode.nic.in/bitstream/123456789/10960/1/the_legal_service_authorities_act%2C_1987.pdf
- **Relevant provisions:** Sections 12, 13, 19–22E
- **Used for:** Legal aid eligibility, entitlement and Lok Adalat provisions.
- **Evaluation questions:** Q1, Q4, Q5, Q9 and Q10.
- **Repository status:** Not present as a PDF in `data/`.

### S02 – NALSA Frequently Asked Questions

- **Authority:** National Legal Services Authority (NALSA)
- **URL:** https://nalsa.gov.in/faqs/
- **Relevant questions:** Q12, Q16, Q17, Q25, Q27, Q29, Q30, Q35, Q47, Q48, Q49, Q52, Q65 and Q81.
- **Used for:** Legal aid eligibility, application procedures, legal aid institutions, workers' assistance, victim support and Lok Adalat explanations.
- **Evaluation questions:** Q1–Q5 and Q7–Q10.
- **Repository status:** Not present as a downloaded source document in `data/`.

### S03 – NALSA Lok Adalats

- **Authority:** National Legal Services Authority (NALSA)
- **URL:** https://nalsa.gov.in/lok-adalats/
- **Used for:** Purpose, jurisdiction, eligible disputes, settlement procedures and Lok Adalat functioning.
- **Evaluation questions:** Q2, Q4, Q5 and Q10.
- **Repository status:** Online reference identified; local ingestion not verified.

### S04 – NALSA Permanent Lok Adalat

- **Authority:** National Legal Services Authority (NALSA)
- **URL:** https://nalsa.gov.in/permanent-lok-adalat/
- **Used for:** Permanent Lok Adalat jurisdiction, public utility services and decision-making powers.
- **Evaluation question:** Q5.
- **Repository status:** Online reference identified; local ingestion not verified.

### S05 – NALSA Workers in the Unorganised Sector Scheme, 2015

- **Authority:** National Legal Services Authority (NALSA)
- **Official scheme listing:** https://nalsa.gov.in/preventive-strategic-legal-services-schemes/
- **Tamil Nadu Legal Services Authority listing:** https://tamilnadu.nalsa.gov.in/scheme/nalsa-legal-services-to-the-workers-in-the-unorganized-sector-scheme-2015/
- **Used for:** Legal services and assistance for workers in the unorganised sector.
- **Evaluation question:** Q7.
- **Repository status:** Official scheme identified; local PDF ingestion not verified.

### S06 – NALSA Compensation Scheme for Women Victims/Survivors of Sexual Assault/Other Crimes, 2018

- **Authority:** National Legal Services Authority (NALSA)
- **Official source:** https://nalsa.gov.in/victim-compensation/
- **Tamil Nadu Legal Services Authority listing:** https://tamilnadu.nalsa.gov.in/scheme/victim-compensation-scheme-for-women-victims-survivors-of-sexual-assault-other-crimes-2018/
- **Used for:** Victim compensation and related legal assistance information.
- **Evaluation question:** Q8.
- **Repository status:** Official scheme identified; local PDF ingestion not verified.

### S07 – NALSA Official Website

- **Authority:** National Legal Services Authority
- **URL:** https://nalsa.gov.in/
- **Used for:** Official institutional information, legal aid programmes, schemes and updates.
- **Repository status:** Reference portal.

## 3. Source-to-Question Mapping

| Question | Primary source references |
|---|---|
| Q1 | S01, S02 |
| Q2 | S01, S03 |
| Q3 | S02, S05 |
| Q4 | S01, S02, S03 |
| Q5 | S01, S03, S04 |
| Q6 | No supporting document; must return "I don't know." |
| Q7 | S02, S05 |
| Q8 | S02, S06 |
| Q9 | S01, S02 |
| Q10 | S01, S02, S03 |

## 4. Source Handling and Reliability Rules

1. Prefer official government sources, India Code and NALSA publications.
2. Record the document title, issuing authority, relevant section or page and official URL.
3. Cite the exact document and page number or legal section used in each answer.
4. Do not treat an online reference as an ingested database document.
5. Check whether legal provisions, eligibility thresholds and schemes have been amended before using them.
6. Use the applicable Tamil Nadu income threshold rather than hardcoding an outdated amount.
7. Do not invent Lok Adalat schedules, legal provisions, eligibility criteria or scheme details.
8. If the available source documents do not support an answer, respond with "I don't know."

## 5. Unanswerable Question Policy

**Q6: When is the next Lok Adalat in Villupuram?**

The current evaluation dataset does not contain an official schedule for the next Lok Adalat in Villupuram.

NyayaSetu must not predict or fabricate a date.

Expected response:

"I don't know."

## 6. Repository and Ingestion Status

At the time of this documentation:

- `data/sample_records.json` is present.
- No source PDF files are present in the repository's `data/` directory.
- The official sources listed above have been identified for research.
- Their actual database ingestion and indexing must be verified separately.

Update this section when source documents are downloaded, processed and loaded into the database.

## 7. Maintenance

Review official sources whenever relevant laws, schemes, eligibility limits or institutional guidance change.

For each downloaded document, record its retrieval date, publication or amendment date where available, filename, version and checksum.

**Last reviewed:** 21 November 2026.
