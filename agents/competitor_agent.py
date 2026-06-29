from __future__ import annotations
import logging
from datetime import datetime
from models.schemas import TechDirection, CompetitorAgentOutput
from agents.base import call_claude_structured
from agents._schemas import COMPETITOR_AGENT
from tools.tavily_tool import TavilyTool

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = "你是一名竞争情报分析师，识别科技创业领域的竞争格局。所有文字使用中文。"


def run(direction: TechDirection) -> CompetitorAgentOutput:
    logger.info(f"Competitor Agent 开始分析：{direction.name}")
    tavily = TavilyTool()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    results = []
    try:
        kw = " ".join(direction.search_keywords[:2])
        results += tavily.search(f"{kw} companies startups competitors market 2024", max_results=6)
        results += tavily.search(f"{direction.name} 竞争格局 主要厂商 2024", max_results=4)
    except Exception as e:
        logger.warning(f"Competitor Agent 搜索失败: {e}")

    context = f"技术方向：{direction.name}\n今天日期：{today}\n\n"
    for r in results[:8]:
        context += f"- {r.get('title','')}\n  {r.get('url','')}\n  {r.get('content','')[:400]}\n\n"

    data = call_claude_structured(SYSTEM_PROMPT, context, COMPETITOR_AGENT, max_tokens=3000)
    data.setdefault("big_tech_players", [])
    data.setdefault("startup_competitors", [])
    data.setdefault("chinese_competitors", [])
    data.setdefault("differentiation_gaps", [])
    data.setdefault("citations", [])
    result = CompetitorAgentOutput(**data)
    logger.info(f"Competitor Agent 完成：{direction.name}，大厂威胁={result.big_tech_threat_level}")
    return result
