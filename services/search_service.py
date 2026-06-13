"""Tavily web search service."""

from __future__ import annotations

import logging
from typing import Any

import requests
from requests.exceptions import HTTPError, RequestException, Timeout

from services.config import TAVILY_API_KEY, SEARCH_RESULTS_COUNT, REQUEST_TIMEOUT_SECONDS
from utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)

CLAIM_TYPE_QUERY_TEMPLATES: dict[str, str] = {
    "Market Statistic":      'market size statistic "{claim}" latest data',
    "Financial Number":      'financial figure "{claim}" official report',
    "User Count":            'user count active users "{claim}" official',
    "Growth Rate":           'growth rate percentage "{claim}" verified',
    "Date":                  'event date timeline "{claim}" confirmed',
    "Technical Figure":      'technical specification "{claim}" verified',
    "Technical Specification": 'technical specification "{claim}" datasheet',
    "Revenue":               'company revenue earnings "{claim}" official filing',
    "Percentage":            'percentage statistic "{claim}" credible source',
    "Other":                 "Verify claim: {claim}",
}

_search_cache: dict[tuple, list[dict[str, Any]]] = {}


class SearchService:
    """Retrieve evidence snippets from Tavily Search API."""

    def __init__(self) -> None:
        if not TAVILY_API_KEY:
            raise ValueError(
                "TAVILY_API_KEY is not configured. "
                "Set it in .env (local) or Streamlit Cloud Secrets (production)."
            )
        self._key = TAVILY_API_KEY

    @staticmethod
    def build_query(claim: str, claim_type: str = "Other") -> str:
        template = CLAIM_TYPE_QUERY_TEMPLATES.get(claim_type, CLAIM_TYPE_QUERY_TEMPLATES["Other"])
        return template.format(claim=claim.strip())

    def search(
        self, query: str, max_results: int | None = None
    ) -> tuple[list[dict[str, Any]], str | None]:
        if max_results is None:
            max_results = SEARCH_RESULTS_COUNT
        cache_key = (self._key, query.strip()[:500], max_results)
        if cache_key in _search_cache:
            return [dict(r) for r in _search_cache[cache_key]], None
        results, error = self._do_search(self._key, query.strip()[:500], max_results)
        if not error:
            _search_cache[cache_key] = results
        return [dict(r) for r in results], error

    @staticmethod
    def _do_search(
        api_key: str, query: str, max_results: int
    ) -> tuple[list[dict[str, Any]], str | None]:
        if len(query) < 3:
            return [], "Search query is too short."

        payload = {
            "api_key": api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": max_results,
            "include_answer": True,
            "include_raw_content": False,
            "include_images": False,
        }

        def _perform() -> dict:
            response = requests.post(
                "https://api.tavily.com/search",
                json=payload,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            return response.json()

        try:
            data = retry_with_backoff(
                _perform,
                max_attempts=3,
                base_delay=1.0,
                retry_exceptions=(Timeout, HTTPError, RequestException),
            )
        except Timeout:
            return [], "Search request timed out."
        except HTTPError as exc:
            code = exc.response.status_code if exc.response is not None else "unknown"
            return [], f"Tavily search failed with status {code}."
        except RequestException as exc:
            return [], f"Tavily search error: {exc}"
        except ValueError:
            return [], "Tavily returned invalid JSON."

        results: list[dict[str, Any]] = []
        if answer := data.get("answer"):
            results.append({"title": "Tavily synthesized answer", "url": "", "content": str(answer), "score": 1.0})

        for item in data.get("results", [])[:max_results]:
            content = item.get("content") or item.get("snippet") or ""
            if not content:
                continue
            results.append({
                "title": item.get("title") or item.get("url") or "Untitled source",
                "url": item.get("url", ""),
                "content": content,
                "score": item.get("score", 0),
            })

        ranked = sorted(results, key=lambda r: r.get("score", 0), reverse=True)
        return ranked[: max_results + 1], None

    def search_claim(
        self, claim: str, claim_type: str = "Other"
    ) -> tuple[dict[str, Any], str | None]:
        query = self.build_query(claim, claim_type)
        results, error = self.search(query, SEARCH_RESULTS_COUNT)
        if error:
            return {"query": query, "sources": [], "evidence": ""}, error

        evidence_parts, sources = [], []
        for idx, result in enumerate(results, 1):
            title   = result.get("title", "Source")
            url     = result.get("url", "")
            content = str(result.get("content", "")).strip()
            if not content:
                continue
            evidence_parts.append(f"Source {idx}: {title}\nURL: {url or 'N/A'}\nSnippet: {content[:900]}")
            if url:
                sources.append({"title": title, "url": url})

        return {
            "query": query,
            "sources": sources[:SEARCH_RESULTS_COUNT],
            "evidence": "\n\n".join(evidence_parts),
        }, None
