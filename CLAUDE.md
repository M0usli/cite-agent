# Project name: Cite
Tagline: "Cite: an agentic research assistant where every answer is backed by a source." Use the name Cite in the BRD, UI, README, and repo (repo name: cite-agent).

I want to build a portfolio project: an Agentic Research Assistant. It answers research questions by deciding for itself what to look up. It searches my uploaded documents, searches the web, does calculations, reads the results, decides whether it needs more information, and repeats until it can give a well-cited answer. This is "agentic RAG."

About me: 4th-year CS student. I've worked as a Business Analysis intern (Deloitte; BRDs, user stories, acceptance criteria, UAT) and I've built full-stack apps with Next.js + TypeScript, FastAPI, PostgreSQL, Docker, and GitHub Actions. I want this project to run like a real, lightweight software lifecycle: Requirements → Design → Development → QA → Deployment, so I can show both my BA and engineering skills. Keep each stage organized but SHORT; this is a portfolio project, not an enterprise program.

## How we'll work
- The project has two releases: v1.0 (basic) and v2.0 (advanced). Each release goes through the same 5 stages.
- Each stage ends with a GATE: stop, summarize what was produced, and wait for my approval before moving to the next stage. I'm playing the role of the business sponsor and reviewer.
- All project documents live in /docs as Markdown. Keep them concise: BRD ≤ 2 pages, use cases ≤ 1 page each, no filler.
- Use traceability IDs everywhere: business requirements (BR-01), use cases (UC-01), functional requirements (FR-01), non-functional requirements (NFR-01), acceptance criteria (AC-01), test cases (TC-01), defects (BUG-01). Every test must trace back to a requirement.
- Act as a mentor too: the first time an AI/agent concept appears (tool use/function calling, the agent loop, embeddings, vector search, context windows, prompt injection, LLM-as-judge), explain it briefly in plain language. I need to explain every part in interviews.
- Write the agent loop by hand using the Anthropic Python SDK's tool-use API, NOT a framework like LangChain, so I understand exactly how it works.
- This file is the project brief. Do not overwrite it. The public README.md is a separate file written at Stage 5.

## Tech stack
- Backend: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0 + Alembic.
- Database: PostgreSQL + pgvector (pgvector/pgvector Docker image).
- LLM: Anthropic Python SDK (Claude) with tool use. API key and model name come from env vars (.env gitignored; commit .env.example).
- Embeddings: local open-source model via sentence-transformers (e.g. BAAI/bge-small-en-v1.5), behind an interface so it can be swapped.
- Web search: a search API with a free tier (e.g. Tavily), behind an interface so the provider can be swapped. Key in env vars.
- Frontend: Next.js (App Router) + React + TypeScript (strict) + Tailwind.
- Dev environment: Docker Compose (frontend, backend, postgres); everything starts with `docker compose up`.
- Testing: pytest (mock the LLM and web search; no real API calls in automated tests), Vitest for a few frontend tests.
- CI: GitHub Actions running ruff, ESLint, tsc, and tests on every push.

=====================================================================
# RELEASE v1.0 — BASIC AGENT
=====================================================================
Scope: a working agent with 3 tools, a simple chat UI, and citations.
- Tools: (1) search_documents: vector search over my uploaded PDFs, returning chunks with document name and page number; (2) web_search: returns titles, URLs, and snippets; (3) calculator: SAFE arithmetic evaluation (never Python eval/exec on model output).
- Agent loop: send the question and tool definitions to Claude → if it requests tools, run them and return results → repeat until it gives a final answer. Enforce a max number of steps (e.g. 6) and handle tool errors gracefully.
- The final answer must cite sources: [doc name, p. X] for documents and [title](URL) for web results. If it can't find an answer, it says so.
- PDF upload: extract text page by page (PyMuPDF), chunk with overlap keeping page numbers, embed, store in pgvector.
- UI: upload PDFs, ask a question, see the answer with clickable citations, and a collapsible "Agent steps" panel listing each tool call and a short summary of its result.
- Out of scope for v1: streaming, conversation memory, planning, multiple collections, auth.

## Stage 1 — Requirements (BA)  → GATE
Produce:
- docs/BRD.md: problem statement, business objectives (BR-xx), stakeholders/users, in scope / out of scope, assumptions & constraints, success metrics, risks.
- docs/use-cases.md: 4–6 use cases (UC-xx), each with actor, preconditions, main flow, alternate/exception flows, postconditions. Include at least: ask a question answered from documents, ask one needing the web, ask one needing a calculation, ask one combining sources, and a question with no answer available.
- docs/requirements.md: functional (FR-xx) and non-functional (NFR-xx) requirements, each with acceptance criteria (AC-xx) in Given/When/Then format. NFRs should cover response time, max agent steps, cost per question, security (API keys, prompt injection from web content), and citation accuracy.
Stop and wait for my approval.

## Stage 2 — Design  → GATE
Produce docs/design.md (short):
- Architecture diagram (Mermaid): frontend, API, agent loop, tools, database, external APIs.
- Sequence diagram (Mermaid) of one question flowing through the agent loop with 2 tool calls.
- Data model, API endpoints, and tool definitions (names, input schemas, outputs).
- 3–5 key design decisions in "Decision / Alternatives / Why" format (e.g. hand-written loop vs framework, pgvector vs a separate vector DB).
Stop and wait for my approval.

## Stage 3 — Development  → GATE (after each increment)
Build in small increments, stopping after each one so I can run it and ask questions:
- Dev-1: Repo structure, Docker Compose, FastAPI + Next.js hello-world talking to each other, CI pipeline skeleton.
- Dev-2: PDF ingestion: upload, page-by-page extraction, chunking with page tracking, embeddings, pgvector storage, plus a debug endpoint to search chunks.
- Dev-3: The three tools as standalone, unit-tested Python modules.
- Dev-4: The agent loop with step limit, error handling, citations, and a log of every step saved to the database.
- Dev-5: Chat UI with citations and the Agent Steps panel.
Each increment: reference which FR-xx it implements in the commit message and in your summary.

## Stage 4 — QA  → GATE
Produce:
- docs/test-plan.md: scope, approach (unit, integration, end-to-end, agent evaluation), entry/exit criteria.
- A traceability matrix (in the test plan or docs/traceability.md): FR/AC → TC → status.
- Automated tests implementing the test cases (mocked LLM for deterministic tests).
- An agent evaluation set: eval/questions.csv with ~25 questions I'll help write (mix of doc-only, web-only, calculation, multi-source, and unanswerable), with expected sources and reference answers. A script (python -m app.eval) that reports: answer correctness (LLM-as-judge with a clear rubric), citation accuracy, correct-refusal rate, average steps, latency, and cost per question.
- docs/qa-report.md: results, defects found (BUG-xx with severity and status), and a go/no-go recommendation against the exit criteria.
Fix defects before the gate. Stop and wait for my approval.

## Stage 5 — Deployment  → GATE
- Deploy the app publicly (e.g. backend + Postgres on Render or Railway, frontend on Vercel). Add basic protections for a public demo: rate limiting and a daily cost cap, so strangers can't run up my API bill.
- docs/release-notes-v1.0.md: what's included, known limitations, how to use it.
- README.md (public-facing; separate from this CLAUDE.md): what it does, architecture diagram, how to run locally, live demo link, screenshots placeholders, and an eval Results table.
- Tag the release v1.0 in git.
Stop and wait for my approval before starting v2.0.

=====================================================================
# RELEASE v2.0 — ADVANCED AGENT
=====================================================================
Treat v2.0 as a CHANGE REQUEST on top of v1.0: write docs/change-request-v2.md (what's changing, why, impact on existing requirements, new BR/FR/NFR/UC IDs) instead of rewriting the BRD. Then run the same 5 stages, keeping documents as short addenda.

Scope for v2.0:
- Planning: for complex questions, the agent first writes a short research plan (sub-questions), then executes it. Show the plan in the UI.
- Parallel tool calls when sub-questions are independent.
- Self-verification: before answering, the agent checks that each claim is supported by a cited source and revises or flags unsupported claims.
- Streaming: stream the agent's progress live ("Searching documents for X…", "Reading 3 web results…") and the final answer token by token (Server-Sent Events).
- Conversation memory: follow-up questions use earlier context.
- New tools: fetch_url (read a full web page, with size limits and HTML cleaned to text) and one structured-data tool (e.g. query a CSV/Excel file I upload with SQL via DuckDB).
- Guardrails: step and token budgets per question, prompt-injection defenses for web content (treat fetched text as data, never instructions), and a visible "confidence / sources used" summary.
- Observability: a trace view per question showing each step, tokens used, latency, and cost.
- Evaluation: extend the eval set with multi-hop questions, and report v1 single-loop vs v2 planning+verification side by side (accuracy, citation accuracy, steps, latency, cost). This comparison is the headline result for my resume.

Stages for v2.0: Requirements (change request + new use cases + ACs) → Design (updated diagrams + decisions) → Development (increments: planning, verification, streaming, memory, new tools, guardrails, tracing) → QA (regression on v1 tests + new tests + comparison eval + QA report) → Deployment (release notes v2.0, README update, tag v2.0).

## Where we are
Start with v1.0 Stage 1. Before writing the documents, ask me up to 5 short questions you need answered as the "business sponsor" (e.g. who the target users are, which documents I'll use, budget limits). Then produce the Stage 1 documents.
When resuming in a new session, check /docs and the git log to see which stage and increment we're on, summarize it for me, and continue from there.
