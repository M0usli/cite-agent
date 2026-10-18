from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol

import httpx2

from app.config import get_settings


@dataclass(frozen=True)
class WebResult:
    title: str
    url: str
    snippet: str


class SearchProviderError(Exception):
    """The web search provider failed (timeout, bad key, outage...)."""


class SearchProvider(Protocol):
    """Web search backend. Swap providers by changing SEARCH_PROVIDER (NFR-11)."""

    def search(self, query: str, max_results: int) -> list[WebResult]: ...


class TavilyProvider:
    URL = "https://api.tavily.com/search"

    def __init__(self, api_key: str, timeout: float, client: httpx2.Client | None = None) -> None:
        self._api_key = api_key
        self._client = client or httpx2.Client(timeout=timeout)

    def search(self, query: str, max_results: int) -> list[WebResult]:
        if not self._api_key:
            raise SearchProviderError("Web search is not configured (TAVILY_API_KEY is empty).")
        try:
            response = self._client.post(
                self.URL,
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={"query": query, "max_results": max_results, "search_depth": "basic"},
            )
            response.raise_for_status()
            data = response.json()
        except httpx2.TimeoutException as exc:
            raise SearchProviderError("Web search timed out.") from exc
        except httpx2.HTTPStatusError as exc:
            raise SearchProviderError(
                f"Web search failed with HTTP {exc.response.status_code}."
            ) from exc
        except (httpx2.HTTPError, ValueError) as exc:
            raise SearchProviderError("Web search is unavailable right now.") from exc

        return [
            WebResult(title=r.get("title") or r["url"], url=r["url"], snippet=r.get("content", ""))
            for r in data.get("results", [])
            if r.get("url")
        ]


class FakeSearchProvider:
    """Canned results for tests and offline development. No network, no key."""

    def __init__(
        self, results: list[WebResult] | None = None, error: Exception | None = None
    ) -> None:
        self.results = results or []
        self.error = error
        self.queries: list[str] = []

    def search(self, query: str, max_results: int) -> list[WebResult]:
        self.queries.append(query)
        if self.error:
            raise self.error
        return self.results[:max_results]


@lru_cache
def get_search_provider() -> SearchProvider:
    settings = get_settings()
    if settings.search_provider == "fake":
        return FakeSearchProvider()
    return TavilyProvider(settings.tavily_api_key, timeout=settings.web_search_timeout_s)
