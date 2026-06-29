from __future__ import annotations
import os
import time
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from tavily import TavilyClient
from .base_tool import BaseTool

logger = logging.getLogger(__name__)


class TavilyTool(BaseTool):
    name = "tavily"
    default_ttl_hours = 24

    def __init__(self):
        self._client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
        include_domains: list[str] | None = None,
        ttl_hours: int | None = None,
    ) -> list[dict]:
        cached = self._read_cache(query)
        if cached is not None:
            logger.debug(f"Cache hit: {query[:60]}")
            return cached

        time.sleep(1)  # rate limit: 1 req/sec

        kwargs: dict = {
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
        }
        if include_domains:
            kwargs["include_domains"] = include_domains

        response = self._client.search(**kwargs)
        results = response.get("results", [])

        self._write_cache(query, results, ttl_hours)
        logger.debug(f"Tavily fetched {len(results)} results for: {query[:60]}")
        return results

    def search_policies(self, query: str) -> list[dict]:
        domains = [
            "sz.gov.cn", "miit.gov.cn", "gd.gov.cn",
            "nanshanqu.gov.cn", "futianqu.gov.cn", "baoanqu.gov.cn",
            "longhuaqu.gov.cn", "guangmingqu.gov.cn", "longgangqu.gov.cn",
            "pingshangqu.gov.cn", "yantianqu.gov.cn", "luohuqu.gov.cn",
            "dpxq.gov.cn", "qianhai.gov.cn",
        ]
        return self.search(query, max_results=8, search_depth="advanced",
                           include_domains=domains, ttl_hours=72)

    def search_market(self, query: str) -> list[dict]:
        domains = [
            "mckinsey.com", "bcg.com", "grandviewresearch.com",
            "marketsandmarkets.com", "statista.com", "mordorintelligence.com",
        ]
        return self.search(query, max_results=6, search_depth="advanced",
                           include_domains=domains, ttl_hours=72)

    def search_investment(self, query: str) -> list[dict]:
        domains = [
            "crunchbase.com", "techcrunch.com", "36kr.com",
            "a16z.com", "sequoiacap.com", "pitchbook.com",
        ]
        return self.search(query, max_results=6, search_depth="basic",
                           include_domains=domains, ttl_hours=24)
