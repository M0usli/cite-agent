import json

import httpx2
import pytest

from app.providers.search import (
    FakeSearchProvider,
    SearchProviderError,
    TavilyProvider,
    WebResult,
)
from app.tools.registry import ToolRegistry
from app.tools.sources import SourceRegistry
from app.tools.web_search import MAX_SNIPPET_CHARS, WebSearch

RESULTS = [
    WebResult("Python 3.14 released", "https://python.org/news/3.14", "Python 3.14 is out."),
    WebResult("Python versions", "https://devguide.python.org/versions/", "Status of versions."),
]


def _registry(provider: FakeSearchProvider, sources: SourceRegistry | None = None) -> ToolRegistry:
    return ToolRegistry([WebSearch(provider, sources or SourceRegistry())])


def test_results_have_title_url_snippet_and_source_ids() -> None:
    """AC-11"""
    outcome = _registry(FakeSearchProvider(RESULTS)).execute(
        "web_search", {"query": "python latest version"}
    )

    assert outcome.is_error is False
    results = outcome.content["results"]
    assert [r["source_id"] for r in results] == ["W1", "W2"]
    for r in results:
        assert r["title"] and r["url"].startswith("https://") and r["snippet"]


def test_provider_failure_becomes_error_result() -> None:
    """AC-12"""
    provider = FakeSearchProvider(error=SearchProviderError("Web search timed out."))

    outcome = _registry(provider).execute("web_search", {"query": "anything"})

    assert outcome.is_error is True
    assert outcome.content == {"error": "Web search timed out."}


def test_same_url_keeps_same_source_id_across_searches() -> None:
    sources = SourceRegistry()
    registry = _registry(FakeSearchProvider(RESULTS), sources)

    registry.execute("web_search", {"query": "first"})
    second = registry.execute("web_search", {"query": "second"})

    assert [r["source_id"] for r in second.content["results"]] == ["W1", "W2"]
    assert len(sources.all()) == 2


def test_long_snippets_are_truncated() -> None:
    long = [WebResult("Long", "https://example.com", "x" * 2000)]

    outcome = _registry(FakeSearchProvider(long)).execute("web_search", {"query": "q"})

    assert len(outcome.content["results"][0]["snippet"]) == MAX_SNIPPET_CHARS


def test_max_results_is_limited_to_five() -> None:
    outcome = _registry(FakeSearchProvider(RESULTS)).execute(
        "web_search", {"query": "q", "max_results": 50}
    )

    assert outcome.is_error is True
    assert "max_results" in outcome.content["error"]


# --- TavilyProvider, with the HTTP layer mocked (no network) ---


def _tavily(handler) -> TavilyProvider:
    client = httpx2.Client(transport=httpx2.MockTransport(handler))
    return TavilyProvider("tvly-test-key", timeout=8, client=client)


def test_tavily_sends_key_and_parses_results() -> None:
    seen: dict = {}

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen["auth"] = request.headers["Authorization"]
        seen["body"] = json.loads(request.content)
        return httpx2.Response(
            200,
            json={
                "results": [
                    {"title": "Title A", "url": "https://a.com", "content": "Snippet A"},
                    {"title": "", "url": "https://b.com", "content": "Snippet B"},
                    {"title": "No URL", "content": "dropped"},
                ]
            },
        )

    results = _tavily(handler).search("cite agents", max_results=3)

    assert seen["auth"] == "Bearer tvly-test-key"
    assert seen["body"]["query"] == "cite agents"
    assert seen["body"]["max_results"] == 3
    assert results == [
        WebResult("Title A", "https://a.com", "Snippet A"),
        WebResult("https://b.com", "https://b.com", "Snippet B"),  # falls back to URL as title
    ]


@pytest.mark.parametrize(
    ("handler", "message"),
    [
        (lambda r: httpx2.Response(401, json={"detail": "bad key"}), "HTTP 401"),
        (lambda r: httpx2.Response(200, content=b"not json"), "unavailable"),
    ],
)
def test_tavily_errors_become_provider_errors(handler, message: str) -> None:
    with pytest.raises(SearchProviderError, match=message):
        _tavily(handler).search("q", 5)


def test_tavily_timeout_becomes_provider_error() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ReadTimeout("slow", request=request)

    with pytest.raises(SearchProviderError, match="timed out"):
        _tavily(handler).search("q", 5)


def test_tavily_without_key_fails_clearly() -> None:
    with pytest.raises(SearchProviderError, match="not configured"):
        TavilyProvider("", timeout=8).search("q", 5)
