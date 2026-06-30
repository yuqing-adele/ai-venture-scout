from __future__ import annotations
import logging
from models.schemas import (
    TechScoutOutput, MarketAgentOutput, PatentAgentOutput,
    InvestmentAgentOutput, PolicyAgentOutput, CompetitorAgentOutput,
    CandidateProduct, ProductGeneratorOutput, UserConstraints,
)
from agents.base import call_claude_structured
from agents._schemas import PRODUCT_GENERATOR

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一名科技创业产品策划专家，为深圳硬件创业团队寻找最有价值的产品方向。

严格遵守用户消息中给出的团队规模、预算、已有产品/资源等具体约束条件，
不要套用任何固定假设——每个用户的情况不同，以用户实际描述为准。

通用原则：
- 地点：深圳，充分利用供应链优势
- 重点：AI、具身智能、机器人、AI硬件等政策扶持方向
- 产品名称要具体（不是"AI工业软件"，而是"PCB焊点AI视觉检测模块"这个级别）
- 即使用户已有产品基础，也必须生成具体的候选产品/扩展方向列表，不能返回空列表

所有文字使用中文。"""


def run(
    user_input: str,
    constraints: UserConstraints,
    tech: list[TechScoutOutput],
    market: list[MarketAgentOutput],
    patent: list[PatentAgentOutput],
    investment: list[InvestmentAgentOutput],
    policy: list[PolicyAgentOutput],
    competitor: list[CompetitorAgentOutput],
) -> ProductGeneratorOutput:
    logger.info("Product Generator 开始生成候选产品")

    summaries = []
    for t in tech:
        summaries.append(f"技术{t.direction_name}：TRL={t.trl_level}，趋势={t.paper_volume_trend}，突破：{'; '.join(t.key_breakthroughs[:2])}")
    for m in market:
        summaries.append(f"市场{m.direction_name}：{m.market_size_2024_usd_billion}B USD，CAGR={m.cagr_5year_percent}%，{m.market_maturity}")
    for p in patent:
        summaries.append(f"专利{p.direction_name}：密度={p.patent_density}，进入风险={p.freedom_to_operate_risk}")
    for inv in investment:
        summaries.append(f"投资{inv.direction_name}：热度={inv.investment_heat}，中国VC兴趣={inv.china_vc_interest}")
    for pol in policy:
        summaries.append(f"政策{pol.direction_name}：{pol.policy_support_level}，推荐区={pol.best_district}")
    for c in competitor:
        summaries.append(f"竞争{c.direction_name}：大厂威胁={c.big_tech_threat_level}，空白：{'; '.join(c.differentiation_gaps[:2])}")

    context = f"{constraints.format_for_prompt()}\n\n用户原始描述（补充语境）：{user_input}\n\n研究数据：\n" + "\n".join(summaries)
    context += "\n\n请生成 20–30 个具体的创业产品方向，每个产品要足够具体可落地，并且要在用户真实团队规模和预算范围内可执行。"

    data = call_claude_structured(
        SYSTEM_PROMPT, context, PRODUCT_GENERATOR,
        model="claude-sonnet-4-6", max_tokens=8192,
    )
    data.setdefault("candidates", [])

    if len(data["candidates"]) == 0:
        logger.warning("Product Generator 返回空列表，重试一次（精简字段长度避免截断）")
        data = call_claude_structured(
            SYSTEM_PROMPT,
            context + "\n\n⚠️ 必须生成至少 15 个具体候选产品，不能返回空列表。"
                       "每个字段控制在简短长度内（一句话），避免输出过长被截断。",
            PRODUCT_GENERATOR, model="claude-sonnet-4-6", max_tokens=8192,
        )
        data.setdefault("candidates", [])
        if len(data["candidates"]) == 0:
            raise ValueError("Product Generator 连续两次返回空候选列表，研究数据可能不足以支撑产品构想")

    valid_candidates = []
    for i, c in enumerate(data["candidates"]):
        if not isinstance(c, dict) or not c.get("name"):
            logger.warning(f"候选产品 #{i} 缺少 name 字段，丢弃这一条而不是让整批失败: {c}")
            continue
        c["id"] = f"P{str(len(valid_candidates)+1).zfill(3)}"
        c.setdefault("one_line_description", "")
        c.setdefault("tech_direction", "")
        c.setdefault("target_customer", "")
        c.setdefault("core_value_proposition", "")
        c.setdefault("why_shenzhen_can_do", "")
        valid_candidates.append(c)
    data["candidates"] = valid_candidates

    if len(valid_candidates) == 0:
        raise ValueError("所有候选产品都缺少必要字段（name），无法构建结果")

    result = ProductGeneratorOutput(**data)
    logger.info(f"Product Generator 完成，生成 {len(result.candidates)} 个候选产品")
    return result
