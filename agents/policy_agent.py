from __future__ import annotations
import logging
from datetime import datetime
from models.schemas import TechDirection, PolicyAgentOutput
from agents.base import call_claude_structured
from agents._schemas import POLICY_AGENT
from tools.tavily_tool import TavilyTool

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一名政策研究员，分析中国国家和深圳地方政府对科技产业的扶持政策。

重点覆盖：
- 国家级（工信部、科技部、发改委）
- 广东省
- 深圳市
- 深圳各区（南山、福田、宝安、龙华、光明、坪山、龙岗）

每个级别最多列举 2–3 个最重要的政策。所有文字使用中文。

⚠️ 重要：citations 里的 url 字段必须是搜索结果中真实出现的链接，逐字复制，不能编造或猜测网址路径。
如果搜索结果里没有具体网址，该字段留空字符串，不要编造一个看起来像真的网址（如包含 XXXXXX 占位符的网址）。"""


def run(direction: TechDirection) -> PolicyAgentOutput:
    logger.info(f"Policy Agent 开始分析：{direction.name}")
    tavily = TavilyTool()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    results = []
    try:
        results += tavily.search_policies(f"{direction.name} 深圳 政策 补贴 扶持 2024 2025")
        results += tavily.search_policies(f"{direction.name} 工信部 科技部 产业政策 2024")
        results += tavily.search(f"深圳南山区 {direction.category} 创业补贴", max_results=4)
    except Exception as e:
        logger.warning(f"Policy Agent 搜索失败: {e}")

    context = f"技术方向：{direction.name}，类别：{direction.category}\n今天日期：{today}\n\n"
    for r in results[:10]:
        context += f"- {r.get('title','')}\n  {r.get('url','')}\n  {r.get('content','')[:400]}\n\n"

    data = call_claude_structured(SYSTEM_PROMPT, context, POLICY_AGENT, max_tokens=4096)
    data.setdefault("national_policies", [])
    data.setdefault("shenzhen_city_policies", [])
    data.setdefault("district_policies", [])
    data.setdefault("citations", [])

    for lst in ["national_policies", "shenzhen_city_policies", "district_policies"]:
        cleaned = []
        for item in data.get(lst, []):
            if isinstance(item, dict):
                item.setdefault("policy_name", "")
                item.setdefault("issuing_body", "")
                item.setdefault("level", "national")
                item.setdefault("key_support", "")
                item.setdefault("benefit_for_startup", "")
                cleaned.append(item)
        data[lst] = cleaned

    result = PolicyAgentOutput(**data)
    logger.info(f"Policy Agent 完成：{direction.name}，支持力度={result.policy_support_level}")
    return result
