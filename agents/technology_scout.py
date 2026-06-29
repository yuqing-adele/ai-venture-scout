from __future__ import annotations
import logging
from datetime import datetime
from anthropic import Anthropic
from models.schemas import TechDirection, TechScoutOutput
from agents.base import call_claude_structured
from agents._schemas import TECH_SCOUT
from tools.tavily_tool import TavilyTool
from tools.openalex_tool import OpenAlexTool

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一名技术情报分析师，专注于评估新兴科技方向的技术成熟度和研究趋势。

NASA TRL 技术成熟度等级：
TRL 1–3：基础研究，实验室概念
TRL 4–5：技术验证，原型存在
TRL 6–7：系统验证，接近商业化
TRL 8–9：商业部署，市场已有产品

所有文字使用中文，数字有引用来源。"""


def run(direction: TechDirection) -> TechScoutOutput:
    logger.info(f"Technology Scout 开始分析：{direction.name}")
    tavily = TavilyTool()
    openalex = OpenAlexTool()
    today = datetime.utcnow().strftime("%Y-%m-%d")

    search_results, papers, trend = [], [], []
    try:
        search_results = tavily.search(
            f"{direction.name} technology breakthrough 2024 2025", max_results=6, search_depth="advanced"
        )
    except Exception as e:
        logger.warning(f"Tavily 搜索失败: {e}")
    try:
        papers = openalex.search_papers(direction.search_keywords, max_results=8)
        trend = openalex.get_yearly_trend(direction.search_keywords, years=5)
    except Exception as e:
        logger.warning(f"OpenAlex 失败: {e}")
    try:
        search_results += tavily.search(f"{direction.name} open source github stars 2024", max_results=4)
    except Exception:
        pass

    context = f"技术方向：{direction.name}，类别：{direction.category}\n今天日期：{today}\n\n"
    if papers:
        context += "学术论文（OpenAlex）：\n"
        for p in papers[:5]:
            context += f"- {p.get('title','')} ({p.get('publication_year','')}) 引用:{p.get('cited_by_count',0)} DOI:{p.get('doi','')}\n"
    if trend:
        context += "\n近5年论文数量趋势：\n"
        for t in trend:
            context += f"- {t.get('key','')}: {t.get('count',0)} 篇\n"
    if search_results:
        context += "\n网络搜索结果：\n"
        for r in search_results[:8]:
            context += f"- {r.get('title','')}\n  {r.get('url','')}\n  {r.get('content','')[:300]}\n\n"

    data = call_claude_structured(SYSTEM_PROMPT, context, TECH_SCOUT, max_tokens=4096)
    data.setdefault("key_papers", [])
    data.setdefault("key_breakthroughs", [])
    data.setdefault("citations", [])
    data.setdefault("trl_level", 5)
    data.setdefault("paper_volume_trend", "stable")
    data.setdefault("github_activity", "moderate")

    result = TechScoutOutput(**data)
    logger.info(f"Technology Scout 完成：{direction.name}，TRL={result.trl_level}")
    return result
