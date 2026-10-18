# Business Requirements Document — Cite v1.0

| | |
|---|---|
| Project | Cite (repo: `cite-agent`) |
| Release | v1.0 — Basic Agent |
| Sponsor / Owner | Omar |
| Date | 2026-10-17 |
| Status | Draft, awaiting sponsor approval |

## 1. Problem statement
Students and researchers spend a lot of time jumping between their own PDFs, web searches, and a calculator to answer one question. General chatbots can answer quickly, but they often make up facts and give no sources, so the answer cannot be trusted or checked. Users need an assistant that looks things up for them and shows exactly where each part of the answer came from.

## 2. Business objectives

| ID | Objective |
|---|---|
| BR-01 | Answer research questions from the user's own uploaded PDFs, citing document name and page. |
| BR-02 | Use the web when the documents are not enough, citing each web source by title and URL. |
| BR-03 | Give exact results for calculations by using a calculator tool instead of the model's guess. |
| BR-04 | Decide on its own which sources to use and combine them when a question needs more than one. |
| BR-05 | Be honest: say clearly when no answer can be found instead of making one up. |
| BR-06 | Be transparent: show the user every step the assistant took to reach the answer. |
| BR-07 | Keep running costs low and predictable, so a public demo is safe to host. |

## 3. Stakeholders and users

| Stakeholder | Role / interest |
|---|---|
| Omar (sponsor, developer) | Owns scope, approves each stage gate, builds and runs the system. |
| Students and researchers (primary users) | Upload course material or papers and ask questions about them. |
| Recruiters and hiring managers (demo visitors) | Try the live demo and read the docs to judge BA and engineering skills. |
| External providers | Anthropic (Claude LLM) and a web search API (e.g. Tavily). |

## 4. Scope

**In scope (v1.0)**
- Upload PDFs; extract, chunk, embed, and store them for search.
- An agent with 3 tools: `search_documents`, `web_search`, `calculator`.
- Agent loop with a step limit and graceful tool-error handling.
- Final answers with citations: `[doc name, p. X]` and `[title](URL)`.
- Chat UI: upload, ask, view the answer with clickable citations, and a collapsible "Agent steps" panel.
- Every step logged to the database.
- Public demo with rate limiting and a daily cost cap.

**Out of scope (v1.0, some planned for v2.0)**
- Streaming responses, conversation memory, research planning, self-verification.
- Multiple document collections, user accounts / authentication.
- Reading full web pages, CSV/Excel data, scanned (image-only) PDFs (no OCR).

## 5. Assumptions and constraints

**Assumptions**
- PDFs are in English and contain selectable text (not scanned images).
- Typical use: up to 20 PDFs, each ≤ 50 pages and ≤ 20 MB (research papers, lecture slides, reports).
- All users share one document collection (no accounts in v1).
- Free tiers of the web search API and hosting providers are enough for demo traffic.

**Constraints**
- One developer, part-time, alongside a full course load.
- Cost: on average ≤ $0.05 per question; the public demo's daily spend must not exceed $2.
- The Claude model is set by an env var. Default: Claude Sonnet 5.5 (`claude-sonnet-5-5`) to balance cost and quality; Claude Haiku 5.5 is the fallback if the cost target is missed.
- The agent loop is written by hand with the Anthropic SDK (no agent frameworks).
- Automated tests must not call real paid APIs.

## 6. Success metrics
Measured on the evaluation set (~25 questions) in Stage 4.

| ID | Metric | Target |
|---|---|---|
| SM-01 | Answer correctness (LLM-as-judge) | ≥ 80% |
| SM-02 | Citation accuracy (cited source really supports the claim) | ≥ 90% |
| SM-03 | Correct refusal rate on unanswerable questions | ≥ 80% |
| SM-04 | Average cost per question | ≤ $0.05 |
| SM-05 | Response time | median ≤ 20 s, max ≤ 45 s |
| SM-06 | Agent steps per question | never more than 6 |

## 7. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Model invents facts or cites a source that does not support the claim | Medium | High | Citations may only point to sources returned by tools in that run; measure citation accuracy in eval. |
| Prompt injection: a web page or PDF contains text that tries to give the agent orders | Medium | High | Treat tool results as data only; system prompt rule; tools are read-only; calculator never runs code. |
| API costs grow from long loops or demo abuse | Medium | Medium | Step limit, per-IP rate limit, daily cost cap. |
| Poor retrieval (wrong chunks returned) leads to weak answers | Medium | Medium | Overlapping chunks, tune chunk size and top-k using the eval set. |
| Slow answers from several model and tool calls | Medium | Medium | Step limit, timeouts on each external call, track latency in eval. |
| Free-tier limits of search API or hosting are reached | Low | Medium | Provider behind an interface so it can be swapped; cache nothing sensitive. |
| Scanned PDFs return no text | Medium | Low | Detect empty pages and warn the user (OCR out of scope). |
