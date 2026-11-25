# NyayaSetu – Official Legal Sources

## 1. Purpose

This document maintains the official legal and institutional sources identified for NyayaSetu.

NyayaSetu uses these sources to support legal information retrieval, eligibility guidance, Lok Adalat information and legal aid scheme references.

**Important:** Identifying an online source does not mean that its content has been downloaded, processed, indexed or verified in the database. Repository and ingestion status must be checked separately.

## 2. Official Sources and Research References

### S01 – Legal Services Authorities Act, 1987

- **Authority:** Government of India
- **Official source:** India Code
- **URL:** https://www.indiacode.nic.in/bitstream/123456789/10960/1/the_legal_service_authorities_act%2C_1987.pdf
- **Relevant provisions:** Sections 12, 13 and 19–22E.
- **Used for:** Legal aid eligibility, entitlement and Lok Adalat provisions.
- **Evaluation questions:** Q1, Q4, Q5, Q9 and Q10.
- **Repository status:** This specific India Code PDF is not confirmed in the current NALSA corpus manifest.

### S02 – NALSA Frequently Asked Questions

- **Authority:** National Legal Services Authority (NALSA)
- **Official URL:** https://nalsa.gov.in/faqs/
- **Relevant questions:** Q12, Q16, Q17, Q25, Q27, Q29, Q30, Q35, Q47, Q48, Q49, Q52, Q65 and Q81.
- **Used for:** Legal aid eligibility, application procedures, legal aid institutions, workers' assistance, victim support and Lok Adalat explanations.
- **Evaluation questions:** Q1–Q5 and Q7–Q10.
- **Repository status:** The official FAQ page is recorded in `data/sources.csv`. A corresponding downloaded FAQ document is not confirmed in the current manifest.

### S03 – NALSA Lok Adalats

- **Authority:** National Legal Services Authority (NALSA)
- **URL:** https://nalsa.gov.in/lok-adalats/
- **Used for:** Purpose, jurisdiction, eligible disputes, settlement procedures and Lok Adalat functioning.
- **Evaluation questions:** Q2, Q4, Q5 and Q10.
- **Repository status:** Online research reference. A corresponding downloaded document is not confirmed in the current manifest.

### S04 – NALSA Permanent Lok Adalat

- **Authority:** National Legal Services Authority (NALSA)
- **URL:** https://nalsa.gov.in/permanent-lok-adalat/
- **Used for:** Permanent Lok Adalat jurisdiction, public utility services and decision-making powers.
- **Evaluation question:** Q5.
- **Repository status:** Online research reference. A corresponding downloaded document is not confirmed in the current manifest.

### S05 – NALSA Workers in the Unorganised Sector Scheme, 2015

- **Authority:** National Legal Services Authority (NALSA)
- **Official scheme listing:** https://nalsa.gov.in/preventive-strategic-legal-services-schemes/
- **Tamil Nadu Legal Services Authority listing:** https://tamilnadu.nalsa.gov.in/scheme/nalsa-legal-services-to-the-workers-in-the-unorganized-sector-scheme-2015/
- **Used for:** Legal services and assistance for workers in the unorganised sector.
- **Evaluation question:** Q7.
- **Repository status:** Official scheme reference identified. A corresponding downloaded scheme document is not confirmed in the current manifest.

### S06 – NALSA Compensation Scheme for Women Victims/Survivors of Sexual Assault/Other Crimes, 2018

- **Authority:** National Legal Services Authority (NALSA)
- **Official source:** https://nalsa.gov.in/victim-compensation/
- **Tamil Nadu Legal Services Authority listing:** https://tamilnadu.nalsa.gov.in/scheme/victim-compensation-scheme-for-women-victims-survivors-of-sexual-assault-other-crimes-2018/
- **Used for:** Victim compensation and related legal assistance information.
- **Evaluation question:** Q8.
- **Repository status:** Official scheme reference identified. A corresponding downloaded scheme document is not confirmed in the current manifest.

### S07 – NALSA Official Website

- **Authority:** National Legal Services Authority (NALSA)
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
3. Record retrieval date, publication or amendment date where available, filename, version and checksum for every downloaded document.
4. Cite the exact document and page number or legal section used in each answer.
5. Do not treat an online reference as an ingested database document.
6. Check whether legal provisions, eligibility thresholds and schemes have been amended before using them.
7. Use the applicable Tamil Nadu income threshold rather than hardcoding an outdated amount.
8. Do not invent Lok Adalat schedules, legal provisions, eligibility criteria or scheme details.
9. If the available source documents do not support an answer, respond with "I don't know."
10. Respect applicable source-specific copyright and reuse restrictions. Public accessibility alone does not establish permission to reproduce or redistribute material.

## 5. Unanswerable Question Policy

**Q6: When is the next Lok Adalat in Villupuram?**

The current evaluation dataset does not contain a verified official schedule for the next Lok Adalat in Villupuram.

NyayaSetu must not predict or fabricate a date.

Expected response:

"I don't know."

## 6. Repository and Corpus Status

The active NALSA corpus is maintained under:

`data/raw/nalsa/`

The manifest at `data/manifest.jsonl` records the downloaded documents and their metadata.

**Verified corpus snapshot – 25 November 2026**

| Metric | Verified value |
|---|---:|
| Source inventory entries | 3 |
| Non-empty manifest records | 31 |
| Downloaded manifest records | 31 |
| Unique PDF paths | 31 |
| PDF files verified on disk | 31 |
| PDF pages counted | 1,943 |
| Pages with extractable text | 1,165 |
| Pages without extractable text | 778 |
| Text extraction coverage | 59.96% |
| Remaining pages to 2,000-page target | 57 |
| Target page count | 2,000 |
| Missing files | 0 |
| SHA-256 mismatches | 0 |
| Duplicate SHA-256 values | 0 |
| PDF reading errors | 0 |

All 31 downloaded manifest records are attributed to NALSA. Their filenames, source URLs, checksums and retrieval metadata are recorded in `data/manifest.jsonl`.

The three source-page entries in `data/sources.csv` are:

- NALSA official scheme index.
- NALSA official FAQs.
- Legal Services Authorities Act 1987.

Their recorded licence status is `Not stated`.


`DATASET.md` contains the generated dataset report. Regenerate it after corpus changes using:

```powershell
uv run python scripts/dataset_report.py --full-pages 2000
```

**Database status:** Downloaded files and counted PDF pages do not, by themselves, establish that every document has been parsed, loaded into the database or indexed. These stages must be verified separately.

Research-reference PDFs outside `data/raw/`, sitemap discovery candidates and synthetic test fixtures are excluded from the active corpus totals.

<!-- BEGIN MANIFEST INVENTORY -->
## Direct-document inventory

The following records are taken directly from `data/manifest.jsonl`. The manifest remains the source of truth for downloaded-document metadata.

| # | Document title | Local file | Official URL | Licence | Status |
|---:|---|---|---|---|---|
| 1 | Report on the North Zone Regional Conference on Enhancing Access to Justice | `20260520897097988-362c1d18.pdf` | [Official document](https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2026/05/20260520897097988.pdf) | Not stated | downloaded |
| 2 | Report of the National Conference on “Strengthening Legal Aid Delivery Mechanisms”, 8–9 November 2025 | `20251122262010823-5a7daeba.pdf` | [Official document](https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2025/11/20251122262010823.pdf) | Not stated | downloaded |
| 3 | Not supplied (manifest title: View) | `2025040866630099-49d08f01.pdf` | [Official document](https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2025/04/2025040866630099.pdf) | Not stated | downloaded |
| 4 | Not supplied (manifest title: View) | `202504081255775595-d338f555.pdf` | [Official document](https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2025/04/202504081255775595.pdf) | Not stated | downloaded |
| 5 | Not supplied (manifest title: View) | `202608121217116933-ab61d09d.pdf` | [Official document](https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2026/08/202608121217116933.pdf) | Not stated | downloaded |
| 6 | Not supplied (manifest title: View) | `1756544777-fea03c6b.pdf` | [Official document](https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2025/08/1756544777.pdf) | Not stated | downloaded |
| 7 | Not supplied (manifest title: View) | `1756544763-ddfff673.pdf` | [Official document](https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2025/08/1756544763.pdf) | Not stated | downloaded |
| 8 | Not supplied (manifest title: View) | `202508011983280523-e2819e14.pdf` | [Official document](https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2025/08/202508011983280523.pdf) | Not stated | downloaded |
| 9 | Not supplied (manifest title: View) | `202505101174316797-1d4b02f1.pdf` | [Official document](https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2025/05/202505101174316797.pdf) | Not stated | downloaded |
| 10 | Not supplied (manifest title: View) | `202505101337160458-433e4f73.pdf` | [Official document](https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2025/05/202505101337160458.pdf) | Not stated | downloaded |
| 11 | Not supplied (manifest title: View) | `202505031407313073-3d80853c.pdf` | [Official document](https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2025/05/202505031407313073.pdf) | Not stated | downloaded |
| 12 | Not supplied (manifest title: View) | `202504081834821576-35eb6f80.pdf` | [Official document](https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2025/04/202504081834821576.pdf) | Not stated | downloaded |
| 13 | Not supplied (manifest title: View) | `20250408408064338-3434fcd0.pdf` | [Official document](https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2025/04/20250408408064338.pdf) | Not stated | downloaded |
| 14 | Not supplied (manifest title: View) | `202504081039897814-12419a57.pdf` | [Official document](https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2025/04/202504081039897814.pdf) | Not stated | downloaded |
| 15 | Not supplied (manifest title: View) | `202504082089115766-85709992.pdf` | [Official document](https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2025/04/202504082089115766.pdf) | Not stated | downloaded |
| 16 | Not supplied (manifest title: View) | `202504081671720977-f45ae34e.pdf` | [Official document](https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2025/04/202504081671720977.pdf) | Not stated | downloaded |
| 17 | Not supplied (manifest title: View) | `202504081619659211-34170aee.pdf` | [Official document](https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2025/04/202504081619659211.pdf) | Not stated | downloaded |
| 18 | Not supplied (manifest title: View) | `20250408278181159-94484b13.pdf` | [Official document](https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2025/04/20250408278181159.pdf) | Not stated | downloaded |
| 19 | Not supplied (manifest title: View) | `202504081824353808-0ec1b6ab.pdf` | [Official document](https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2025/04/202504081824353808.pdf) | Not stated | downloaded |
| 20 | Not supplied (manifest title: View) | `202505032006718436-39f7c05a.pdf` | [Official document](https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2025/04/202505032006718436.pdf) | Not stated | downloaded |
| 21 | Not supplied (manifest title: View) | `202504082100174404-718fecf3.pdf` | [Official document](https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2025/04/202504082100174404.pdf) | Not stated | downloaded |
| 22 | Not supplied (manifest title: View) | `202505142178608-0e5ae2e9.pdf` | [Official document](https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2025/05/202505142178608.pdf) | Not stated | downloaded |
| 23 | Not supplied (manifest title: View) | `202504081540884465-660db624.pdf` | [Official document](https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2025/04/202504081540884465.pdf) | Not stated | downloaded |
| 24 | Not supplied (manifest title: View) | `202504081796627129-3bad05b2.pdf` | [Official document](https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2025/04/202504081796627129.pdf) | Not stated | downloaded |
| 25 | Not supplied (manifest title: View) | `202606021189832834-92a82c0c.pdf` | [Official document](https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2026/06/202606021189832834.pdf) | Not stated | downloaded |
| 26 | Not supplied (manifest title: View) | `20250409258379504-8e8276b9.pdf` | [Official document](https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2025/04/20250409258379504.pdf) | Not stated | downloaded |
| 27 | Not supplied (manifest title: View) | `20250409317756439-6aa7e824.pdf` | [Official document](https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2025/04/20250409317756439.pdf) | Not stated | downloaded |
| 28 | Not supplied (manifest title: View) | `202504091237499824-db27697c.pdf` | [Official document](https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2025/04/202504091237499824.pdf) | Not stated | downloaded |
| 29 | Not supplied (manifest title: View) | `20250409581122417-9d79ea54.pdf` | [Official document](https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2025/04/20250409581122417.pdf) | Not stated | downloaded |
| 30 | Not supplied (manifest title: View) | `2025040925439249-c7a90332.pdf` | [Official document](https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2025/04/2025040925439249.pdf) | Not stated | downloaded |
| 31 | Not supplied (manifest title: View) | `20250409901564205-3569eb69.pdf` | [Official document](https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2025/04/20250409901564205.pdf) | Not stated | downloaded |

**Inventory total:** 31 manifest records.

All records are attributed to NALSA. A recorded download or public URL does not establish a separate reuse licence or unrestricted redistribution permission.

<!-- END MANIFEST INVENTORY -->
## 7. Maintenance

Review official sources whenever relevant laws, schemes, eligibility limits or institutional guidance change.

For each newly collected document:

- Verify that the source is eligible for the intended academic use.
- Record the official source URL and retrieval date.
- Record the document title and issuing authority.
- Preserve publication or amendment information where available.
- Calculate and record its SHA-256 checksum.
- Verify that the PDF can be opened and its pages read.
- Update the manifest and regenerate `DATASET.md`.
- Verify parsing and database ingestion separately.

**Last reviewed:** 25 November 2026.
