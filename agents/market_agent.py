from __future__ import annotations
import logging
from datetime import datetime
from models.schemas import TechDirection, MarketAgentOutput
from agents.base import call_claude_structured
from agents._schemas import MARKET_AGENT
from tools.tavily_tool import TavilyTool

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = "你是一名市场分析师，专注于新兴科技市场的规模和增长趋势研究。根据提供的搜索数据输出市场分析，所有文字使用中文，数字有引用来源。"


def run(direction: TechDirection) -> MarketAgentOutput:
    logger.info(f"Market Agent 开始分析：{direction.name}")
    tavily = TavilyTool()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    results = []
    try:
        results += tavily.search_market(f"{direction.name} market size revenue 2024 2025 billion")
        results += tavily.search(f"{direction.name} 市场规模 增长 中国 2024 2025", max_results=4)
    except Exception as e:
        logger.warning(f"Market Agent 搜索失败: {e}")

    context = f"技术方向：{direction.name}\n今天日期：{today}\n\n"
    for r in results[:8]:
        context += f"- {r.get('title','')}\n  {r.get('url','')}\n  {r.get('content','')[:400]}\n\n"

    data = call_claude_structured(SYSTEM_PROMPT, context, MARKET_AGENT)
    data.setdefault("growth_drivers", [])
    data.setdefault("target_segments", [])
    data.setdefault("citations", [])
    result = MarketAgentOutput(**data)
    logger.info(f"Market Agent 完成：{direction.name}，规模={result.market_size_2024_usd_billion}B")
    return result
