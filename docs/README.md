# Cite — Project Documents

Cite is an agentic research assistant where every answer is backed by a source.
This folder holds all project documents, one folder per lifecycle stage. v2.0 documents are added to the same stage folders as short addenda (e.g. `1-requirements/change-request-v2.md`).

## Repository layout

| Folder | Contents |
|---|---|
| `docs/` | All project documents (this folder) |
| `backend/` | FastAPI app, agent loop, tools, database (from Dev-1) |
| `frontend/` | Next.js chat UI (from Dev-1) |
| `eval/` | Agent evaluation set (`questions.csv`) and results (Stage 4) |

## Document map

| Stage | Folder | Documents | v1.0 status |
|---|---|---|---|
| 1. Requirements | `1-requirements/` | `BRD.md`, `use-cases.md`, `requirements.md` | Approved 2026-10-17 |
| 2. Design | `2-design/` | `design.md` | Approved 2026-10-17 |
| 3. Development | `3-development/` | `dev-1.md` … `dev-5.md` | Dev-1, Dev-2 done · Dev-3 awaiting review |
| 4. QA | `4-qa/` | `test-plan.md`, `traceability.md`, `qa-report.md` | Not started |
| 5. Deployment | `5-deployment/` | `release-notes-v1.0.md` | Not started |

`glossary.md` explains the AI/agent terms used in these documents in plain language.

## Traceability IDs

| Prefix | Meaning | Defined in |
|---|---|---|
| BR-xx | Business requirement | `BRD.md` |
| UC-xx | Use case | `use-cases.md` |
| FR-xx | Functional requirement | `requirements.md` |
| NFR-xx | Non-functional requirement | `requirements.md` |
| AC-xx | Acceptance criterion | `requirements.md` |
| TC-xx | Test case | `4-qa/test-plan.md` |
| BUG-xx | Defect | `4-qa/qa-report.md` |

Chain: BR → UC → FR/NFR → AC → TC → (BUG).
