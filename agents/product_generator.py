from __future__ import annotations
import logging
from models.schemas import (
    TechScoutOutput, MarketAgentOutput, PatentAgentOutput,
    InvestmentAgentOutput, PolicyAgentOutput, CompetitorAgentOutput,
    CandidateProduct, ProductGeneratorOutput,
)
from agents.base import call_claude_structured
from agents._schemas import PRODUCT_GENERATOR

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一名科技创业产品策划专家，为深圳硬件创业团队寻找最有价值的产品方向。

关键约束：
- 团队规模：3–8人
- 预算：300万以内能跑起来
- 地点：深圳，充分利用供应链优势
- 重点：AI、具身智能、机器人、AI硬件等政策扶持方向

产品名称要具体（不是"AI工业软件"，而是"PCB焊点AI视觉检测模块"这个级别）。
所有文字使用中文。"""


def run(
    user_input: str,
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

    context = f"用户背景：{user_input}\n\n研究数据：\n" + "\n".join(summaries)
    context += "\n\n请生成 20–30 个具体的创业产品方向，每个产品要足够具体可落地。"

    data = call_claude_structured(SYSTEM_PROMPT, context, PRODUCT_GENERATOR, max_tokens=4096)
    data.setdefault("candidates", [])
    for i, c in enumerate(data["candidates"]):
        c["id"] = f"P{str(i+1).zfill(3)}"
        c.setdefault("one_line_description", "")
        c.setdefault("tech_direction", "")
        c.setdefault("target_customer", "")
        c.setdefault("core_value_proposition", "")
        c.setdefault("why_shenzhen_can_do", "")

    result = ProductGeneratorOutput(**data)
    logger.info(f"Product Generator 完成，生成 {len(result.candidates)} 个候选产品")
    return result
