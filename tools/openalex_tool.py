from __future__ import annotations
import os
import time
import logging
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from .base_tool import BaseTool

logger = logging.getLogger(__name__)

OPENALEX_BASE = "https://api.openalex.org"
EMAIL = os.environ.get("CONTACT_EMAIL", "researcher@example.com")


class OpenAlexTool(BaseTool):
    name = "openalex"
    default_ttl_hours = 168  # 7 days

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=8), reraise=True)
    def search_papers(self, keywords: list[str], max_results: int = 10) -> list[dict]:
        query = " OR ".join(keywords[:3])
        cache_key = f"papers:{query}"
        cached = self._read_cache(cache_key)
        if cached is not None:
            return cached

        time.sleep(0.4)
        params = {
            "search": query,
            "per-page": max_results,
            "sort": "cited_by_count:desc",
            "mailto": EMAIL,
        }
        resp = httpx.get(f"{OPENALEX_BASE}/works", params=params, timeout=15)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        self._write_cache(cache_key, results)
        return results

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=8), reraise=True)
    def get_yearly_trend(self, keywords: list[str], years: int = 5) -> list[dict]:
        query = " OR ".join(keywords[:3])
        cache_key = f"trend:{query}:{years}"
        cached = self._read_cache(cache_key)
        if cached is not None:
            return cached

        time.sleep(0.4)
        from datetime import datetime
        current_year = datetime.now().year
        start_year = current_year - years
        params = {
            "search": query,
            "filter": f"publication_year:{start_year}-{current_year}",
            "group-by": "publication_year",
            "mailto": EMAIL,
        }
        resp = httpx.get(f"{OPENALEX_BASE}/works", params=params, timeout=15)
        resp.raise_for_status()
        results = resp.json().get("group_by", [])
        self._write_cache(cache_key, results)
        return results
