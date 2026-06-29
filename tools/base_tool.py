from __future__ import annotations
import json
import hashlib
import os
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent.parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)


class BaseTool:
    name: str = "base"
    default_ttl_hours: int = 24

    def _cache_key(self, query: str) -> str:
        raw = f"{self.name}|{query}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def _cache_path(self, key: str) -> Path:
        return CACHE_DIR / f"{key}.json"

    def _read_cache(self, query: str) -> dict | None:
        path = self._cache_path(self._cache_key(query))
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        expires_at = datetime.fromisoformat(data["expires_at"])
        if datetime.utcnow() > expires_at:
            path.unlink(missing_ok=True)
            return None
        return data["result"]

    def _write_cache(self, query: str, result: dict, ttl_hours: int | None = None) -> None:
        ttl = ttl_hours or self.default_ttl_hours
        key = self._cache_key(query)
        payload = {
            "key": key,
            "tool": self.name,
            "query": query,
            "result": result,
            "cached_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=ttl)).isoformat(),
        }
        self._cache_path(key).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
