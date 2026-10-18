# Dev-3 — The three tools

**Implements:** FR-06 (`search_documents`), FR-07 (`web_search`), FR-08 (`calculator`), the tool side of FR-11 (errors become results, never crashes), NFR-06 (read-only tools, safe calculator), NFR-11 (search provider swappable by config, AC-37). Also adds source IDs for FR-12 (design D3).

Each tool is a standalone module with its own tests. The agent loop that calls them is Dev-4.

## What was built
| File | Purpose |
|---|---|
| `app/tools/base.py` | `Tool` protocol: `name`, `description`, `Input` (Pydantic model), `run()`. `ToolError` = expected failure with a safe message. |
| `app/tools/registry.py` | `ToolRegistry.definitions()` builds the Anthropic tool list (`name`, `description`, `input_schema` generated from the Pydantic model). `execute()` validates input, runs the tool, and turns **every** failure into `{"error": ...}` with `is_error=True`. Unexpected crashes are logged but their details are hidden from Claude. |
| `app/tools/sources.py` | `SourceRegistry`: one per run. Gives each result an ID (`D1, D2…` for chunks, `W1, W2…` for web). The same chunk or URL keeps the same ID. Dev-4 uses it to turn `[D2]` into `[smith2024.pdf, p. 4]`. |
| `app/tools/search_documents.py` | Wraps Dev-2's `search_chunks`. Input `query` (1–500 chars), `top_k` (1–10, default 5). Text capped at 1,200 chars. |
| `app/tools/web_search.py` + `app/providers/search.py` | `SearchProvider` interface with `TavilyProvider` (HTTP, Bearer key, 8 s timeout) and `FakeSearchProvider`. Chosen by `SEARCH_PROVIDER`. Snippets capped at 500 chars. Timeouts, HTTP errors, bad JSON and a missing key all become clear error messages. |
| `app/tools/calculator.py` | Parses with `ast` and walks the tree. Allows numbers, `+ - * / // % **`, unary ±, `pi`, `e`, and `sqrt round abs min max log`. Rejects everything else (names, attributes, strings, lambdas, bools, keyword args). Exponents are capped at 100 and results at about 10^300, so `9**9**9` is refused instantly. Floats are rounded to 10 significant digits (`0.1 + 0.2` → `0.3`). |

## Tests (87 total, all passing locally, in Docker, and in CI)
| Test file | Covers |
|---|---|
| `test_calculator.py` (35) | AC-13, AC-14 (code injection, `1/0`), 15 allowed expressions, 10 rejected ones, huge powers, math errors, `^` hint, length limit |
| `test_web_search.py` (10) | AC-11, AC-12, stable source IDs, snippet cap, max_results limit; Tavily request/response, 401, bad JSON, timeout, missing key (HTTP mocked) |
| `test_search_documents_tool.py` (4) | AC-09, AC-10, text cap, invalid `top_k` (real Postgres) |
| `test_registry.py` (7) | Anthropic tool format, unknown tool, missing input, crash caught with details hidden, AC-37 provider by config |

No test calls Tavily or Claude (NFR-09). `SEARCH_PROVIDER=fake` is forced in `tests/conftest.py`.

## Notes / decisions
- **Input validation happens before running.** Claude sometimes sends wrong arguments. The error message names the bad field (e.g. `top_k: Input should be less than or equal to 10`), so Claude can fix it on the next step.
- **AC-13 wording:** the calculator returns `21.4285714286` (10 significant digits), and rounding to 2 decimals gives 21.43. Rounding for display is left to the answer text, because forcing 2 decimals would destroy small numbers like 0.0012.
- **`httpx2`** is now a runtime dependency (Tavily client), not just a test dependency.
- **Live Tavily is not tested yet.** It needs your key. Add `TAVILY_API_KEY=tvly-…` to `.env` (free tier at tavily.com) before Dev-4, where the real agent uses it.
