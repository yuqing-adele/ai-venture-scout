from __future__ import annotations
import logging
from models.schemas import UserConstraints
from agents.base import call_claude_structured
from agents._schemas import USER_CONSTRAINTS

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一个信息提取专家，从用户的创业背景描述中提取结构化的关键事实。

严格规则：
- 只提取用户明确提到的事实，绝对不要推测、不要编造、不要用"典型创业团队"的假设值填充
- 如果用户没有明确提到某个字段，数值字段用 0，文本字段用空字符串，列表字段用空数组
- team_size_current 必须是用户明确说的当前团队人数，不是任何产品/项目所需的人数
- ⚠️ budget_amount 必须展开成完整数字，不能保留"万"这种中文简写单位：
  例如用户写"100万"或"100万元"，budget_amount 必须是 1000000（一百万整数），不能写成 100
  例如用户写"50万美元"，budget_amount 必须是 500000，budget_currency 写 "USD"
  例如用户写"5000元"，budget_amount 就是 5000，不要乘任何倍数
- budget_currency 标注清楚是 RMB 还是 USD，根据用户原文的"元/人民币/RMB"或"美元/USD/dollar"判断
- 如果输入文本看起来是乱码、不连贯、或包含大量问号等无法识别的字符，
  仍然如实提取你能识别的部分，不要为了凑出"合理"的数字而编造

所有文字使用中文（除非用户原文是英文）。"""


def run(user_input: str) -> UserConstraints:
    logger.info("Constraint Extractor 开始提取用户约束")

    data = call_claude_structured(
        SYSTEM_PROMPT,
        f"用户创业背景描述：\n{user_input}",
        USER_CONSTRAINTS,
        max_tokens=1500,
    )
    data["raw_description"] = user_input
    data.setdefault("tech_capabilities", [])
    data.setdefault("tech_gaps", [])
    data.setdefault("excluded_directions", [])
    data.setdefault("budget_currency", "RMB")
    data.setdefault("location", "深圳")
    data.setdefault("timeline_months", 12)
    data.setdefault("team_size_hireable", 0)

    result = UserConstraints(**data)  # Pydantic validator 在这里会拦截不合理的数字
    logger.info(
        f"Constraint Extractor 完成：团队{result.team_size_current}人，"
        f"预算{result.budget_amount}{result.budget_currency}"
    )
    return result
