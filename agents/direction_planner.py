from __future__ import annotations
import logging
from models.schemas import TechDirection, DirectionPlannerOutput
from agents.base import call_claude_structured
from agents._schemas import DIRECTION_PLANNER

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一名科技创业方向分析师，专注于识别中国深圳地区最有潜力的硬科技创业方向。

根据用户的创业背景，确定 5–8 个最值得深入研究的具体技术方向。

重点聚焦：AI、具身智能、机器人、AI硬件、工业视觉、边缘AI、脑机接口、低空经济等政策扶持方向。"""


def run(user_input: str) -> DirectionPlannerOutput:
    logger.info("Direction Planner 开始分析用户输入")
    data = call_claude_structured(
        SYSTEM_PROMPT,
        f"用户创业背景：\n{user_input}\n\n请确定 5–8 个最适合该用户的具体技术创业方向。",
        DIRECTION_PLANNER,
    )
    data.setdefault("excluded_areas", [])
    data.setdefault("research_focus", "")
    result = DirectionPlannerOutput(**data)
    logger.info(f"Direction Planner 完成，确定 {len(result.directions)} 个方向")
    return result
