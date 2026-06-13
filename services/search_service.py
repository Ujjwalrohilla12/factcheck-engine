"""Tavily web search service."""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any

import requests

from utils.constants import ERROR_API_KEY, REQUEST_TIMEOUT_SECONDS, SEARCH_RESULTS_COUNT

logger = logging.getLogger(__name__)


class SearchService:
    """Retrieve evidence snippets from Tavily Search API."""

    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError(ERROR_API_KEY)
        self.base_url = "https://api.tavily.com/search"

    def search(self, query: str, max_results: int = SEARCH_RESULTS_COUNT) -> tuple[list[dict[str, Any]], str | None]:
        """Search Tavily and return normalized results."""
        return self._cached_search(self.api_key, query.strip()[:500], max_results)

    @staticmethod
    @lru_cache(maxsize=256)
    def _cached_search(api_key: str, query: str, max_results: int) -> tuple[list[dict[str, Any]], str | None]:
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

        try:
            response = requests.post(
                "https://api.tavily.com/search",
                json=payload,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()
        except requests.Timeout:
            return [], "Search request timed out."
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "unknown"
            return [], f"Tavily search failed with status {status}."
        except requests.RequestException as exc:
            return [], f"Tavily search error: {exc}"
        except ValueError:
            return [], "Tavily returned invalid JSON."

        results = []
        answer = data.get("answer")
        if answer:
            results.append({
                "title": "Tavily synthesized answer",
                "url": "",
                "content": str(answer),
                "score": 1.0,
            })

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

        return results[: max_results + 1], None

    def search_claim(self, claim: str) -> tuple[dict[str, Any], str | None]:
        """Search the requested verification query and format evidence."""
        query = f"Verify claim: {claim}"
        results, error = self.search(query, SEARCH_RESULTS_COUNT)
        if error:
            return {"query": query, "sources": [], "evidence": ""}, error

        evidence_parts = []
        sources = []
        for index, result in enumerate(results, start=1):
            title = result.get("title", "Source")
            url = result.get("url", "")
            content = str(result.get("content", "")).strip()
            if not content:
                continue
            evidence_parts.append(
                f"Source {index}: {title}\nURL: {url or 'N/A'}\nSnippet: {content[:900]}"
            )
            if url:
                sources.append({"title": title, "url": url})

        return {
            "query": query,
            "sources": sources[:SEARCH_RESULTS_COUNT],
            "evidence": "\n\n".join(evidence_parts),
        }, None
