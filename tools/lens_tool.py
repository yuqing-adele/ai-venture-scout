from __future__ import annotations
import os
import time
import logging
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .base_tool import BaseTool

logger = logging.getLogger(__name__)

LENS_BASE = "https://api.lens.org/patent/search"


class LensTool(BaseTool):
    """Lens.org 专利检索（免费 API，需要注册申请 Key）"""

    name = "lens"
    default_ttl_hours = 24 * 30  # 30天，专利数据变化极慢

    def __init__(self):
        self._api_key = os.environ.get("LENS_API_KEY", "").strip()

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TransportError, httpx.TimeoutException)),
        reraise=True,
    )
    def search_patents(self, keywords: list[str], max_results: int = 10) -> list[dict]:
        """
        按关键词搜索专利。
        返回统一格式：[{title, lens_id, url, applicants, jurisdiction, date_published}]
        如果未配置 Key 或请求失败，返回空列表（上层应有 Tavily 兜底）。
        """
        if not self.available:
            logger.debug("LENS_API_KEY 未配置，跳过 Lens.org 检索")
            return []

        query = " ".join(keywords[:3])
        cache_key = f"patents:{query}:{max_results}"
        cached = self._read_cache(cache_key)
        if cached is not None:
            logger.debug(f"Lens 缓存命中: {query[:60]}")
            return cached

        time.sleep(0.3)  # 限速保护，避免触发免费额度限流

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "query": {
                "query_string": {
                    "query": query,
                    "fields": ["title", "abstract"],
                }
            },
            "size": min(max_results, 20),
            "sort": [{"date_published": "desc"}],
            "include": [
                "lens_id", "biblio.invention_title", "date_published",
                "biblio.parties.applicants", "jurisdiction",
            ],
        }

        try:
            resp = httpx.post(LENS_BASE, headers=headers, json=body, timeout=20)
        except (httpx.TransportError, httpx.TimeoutException):
            raise
        except Exception as e:
            logger.warning(f"Lens.org 请求异常: {e}")
            return []

        if resp.status_code == 401:
            logger.error("Lens.org API Key 无效或未授权（401），请检查 LENS_API_KEY")
            return []
        if resp.status_code == 429:
            logger.warning("Lens.org 触发限流（429），跳过本次查询")
            return []
        if resp.status_code != 200:
            logger.warning(f"Lens.org 返回异常状态码 {resp.status_code}: {resp.text[:200]}")
            return []

        try:
            raw = resp.json()
        except Exception as e:
            logger.warning(f"Lens.org 响应解析失败: {e}")
            return []

        results = []
        for item in raw.get("data", []):
            lens_id = item.get("lens_id", "")
            biblio = item.get("biblio", {}) or {}
            title_info = biblio.get("invention_title", [])
            title = ""
            if isinstance(title_info, list) and title_info:
                title = title_info[0].get("text", "") if isinstance(title_info[0], dict) else str(title_info[0])
            elif isinstance(title_info, str):
                title = title_info

            applicants = []
            parties = biblio.get("parties", {}) or {}
            for app in parties.get("applicants", []) or []:
                name = app.get("extracted_name", {}).get("value", "") if isinstance(app, dict) else ""
                if name:
                    applicants.append(name)

            results.append({
                "title": title,
                "lens_id": lens_id,
                "url": f"https://www.lens.org/lens/patent/{lens_id}" if lens_id else "",
                "applicants": applicants,
                "jurisdiction": item.get("jurisdiction", ""),
                "date_published": item.get("date_published", ""),
            })

        self._write_cache(cache_key, results)
        logger.info(f"Lens.org 检索到 {len(results)} 条专利结果: {query[:60]}")
        return results
