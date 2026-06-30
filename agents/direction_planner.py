from __future__ import annotations
import logging
from models.schemas import TechDirection, DirectionPlannerOutput, UserConstraints
from agents.base import call_claude_structured
from agents._schemas import DIRECTION_PLANNER

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一名科技创业方向分析师，专注于识别中国深圳地区最有潜力的硬科技创业方向。

根据用户的创业背景，确定 5–8 个最值得深入研究的具体技术方向。

重点聚焦：AI、具身智能、机器人、AI硬件、工业视觉、边缘AI、脑机接口、低空经济等政策扶持方向。

如果用户明确排除了某些方向，严格遵守，不要建议被排除的方向。
如果用户已有产品基础，优先考虑从现有产品延伸的方向，但也可以包含全新方向。"""


def run(user_input: str, constraints: UserConstraints) -> DirectionPlannerOutput:
    logger.info("Direction Planner 开始分析用户输入")
    context = (
        f"{constraints.format_for_prompt()}\n\n"
        f"用户原始描述（补充语境）：\n{user_input}\n\n"
        f"请确定 5–8 个最适合该用户的具体技术创业方向。"
    )
    data = call_claude_structured(SYSTEM_PROMPT, context, DIRECTION_PLANNER)
    data.setdefault("excluded_areas", [])
    data.setdefault("research_focus", "")
    data.setdefault("directions", [])

    valid_directions = []
    for i, d in enumerate(data["directions"]):
        if not isinstance(d, dict) or not d.get("name"):
            logger.warning(f"方向 #{i} 缺少 name 字段，丢弃这一条而不是让整批失败: {d}")
            continue
        d.setdefault("category", "")
        d.setdefault("rationale", "")
        d.setdefault("search_keywords", [])
        valid_directions.append(d)
    data["directions"] = valid_directions

    if len(valid_directions) == 0:
        raise ValueError("所有候选方向都缺少必要字段（name），无法构建结果")

    result = DirectionPlannerOutput(**data)
    logger.info(f"Direction Planner 完成，确定 {len(result.directions)} 个方向")
    return result
