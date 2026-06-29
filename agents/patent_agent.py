from __future__ import annotations
import logging
from datetime import datetime
from models.schemas import TechDirection, PatentAgentOutput
from agents.base import call_claude_structured
from agents._schemas import PATENT_AGENT
from tools.tavily_tool import TavilyTool

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = "你是一名专利分析师，评估技术方向的专利格局和知识产权风险。所有文字使用中文。"


def run(direction: TechDirection) -> PatentAgentOutput:
    logger.info(f"Patent Agent 开始分析：{direction.name}")
    tavily = TavilyTool()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    results = []
    try:
        kw = " ".join(direction.search_keywords[:2])
        results += tavily.search(f"{kw} patent holders landscape analysis", max_results=5)
        results += tavily.search(f"{direction.name} 专利 知识产权 中国", max_results=4)
    except Exception as e:
        logger.warning(f"Patent Agent 搜索失败: {e}")

    context = f"技术方向：{direction.name}\n今天日期：{today}\n\n"
    for r in results[:8]:
        context += f"- {r.get('title','')}\n  {r.get('url','')}\n  {r.get('content','')[:400]}\n\n"

    data = call_claude_structured(SYSTEM_PROMPT, context, PATENT_AGENT)
    data.setdefault("major_patent_holders", [])
    data.setdefault("chinese_patent_holders", [])
    data.setdefault("key_patent_areas", [])
    data.setdefault("citations", [])
    result = PatentAgentOutput(**data)
    logger.info(f"Patent Agent 完成：{direction.name}，风险={result.freedom_to_operate_risk}")
    return result
