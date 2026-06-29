from __future__ import annotations
import logging
from datetime import datetime
from models.schemas import TechDirection, InvestmentAgentOutput
from agents.base import call_claude_structured
from agents._schemas import INVESTMENT_AGENT
from tools.tavily_tool import TavilyTool

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = "你是一名投资趋势分析师，追踪新兴科技领域的风险投资动向。所有文字使用中文。"


def run(direction: TechDirection) -> InvestmentAgentOutput:
    logger.info(f"Investment Agent 开始分析：{direction.name}")
    tavily = TavilyTool()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    results = []
    try:
        kw = " ".join(direction.search_keywords[:2])
        results += tavily.search_investment(f"{kw} startup funding raised million 2024 2025")
        results += tavily.search(f"{direction.name} 融资 投资 2024 2025", max_results=4)
    except Exception as e:
        logger.warning(f"Investment Agent 搜索失败: {e}")

    context = f"技术方向：{direction.name}\n今天日期：{today}\n\n"
    for r in results[:8]:
        context += f"- {r.get('title','')}\n  {r.get('url','')}\n  {r.get('content','')[:400]}\n\n"

    data = call_claude_structured(SYSTEM_PROMPT, context, INVESTMENT_AGENT)
    data.setdefault("notable_deals", [])
    data.setdefault("top_vc_investors", [])
    data.setdefault("citations", [])
    result = InvestmentAgentOutput(**data)
    logger.info(f"Investment Agent 完成：{direction.name}，热度={result.investment_heat}")
    return result
