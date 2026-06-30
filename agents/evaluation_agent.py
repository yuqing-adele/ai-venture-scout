from __future__ import annotations
import logging
from models.schemas import ProductFullResearch, EvaluationOutput, ProductEvaluation, DimensionScore
from agents.base import call_claude_structured

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一名科技创业投资评估专家。

按以下标准对每个产品打分：

市场机会（30分）：市场规模>100B=15分/10-100B=10分/<10B=5分；增长>30%=10/15-30%=7/<15%=3；需求真实B2B=5/概念=2
深圳落地可行性（25分）：LCSC全买=10/大部分=6/少数=2；本地生态有=8/部分=4/无=1；认证无=7/CE+FCC=4/3C+行业=1
小团队可执行性（20分）：MVP<6月=8/6-12月=5/>12月=2；预算<50万=7/50-200万=4/>200万=1；技术匹配完全=5/需招聘=3/差距大=1
竞争格局（15分）：大厂无布局=8/边缘=4/核心=1；市场有空白=7/有缝隙=4/红海=1
时机（10分）：TRL 6-7=5/4-5=3/其他=1；政策strong=5/moderate=3/weak=1

所有文字使用中文。"""

EVAL_SCHEMA = {
    "type": "object",
    "properties": {
        "evaluations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string"},
                    "product_name": {"type": "string"},
                    "total_score": {"type": "number"},
                    "dimension_scores": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "dimension": {"type": "string"},
                                "score": {"type": "number"},
                                "max_score": {"type": "number"},
                                "rationale": {"type": "string"},
                            },
                            "required": ["dimension", "score", "max_score"],
                        },
                    },
                    "top_strengths": {"type": "array", "items": {"type": "string"}},
                    "top_risks": {"type": "array", "items": {"type": "string"}},
                    "tier": {"type": "string"},
                },
                "required": ["product_id", "product_name", "total_score"],
            },
        },
        "top5_ids": {"type": "array", "items": {"type": "string"}},
        "honorable_mention_ids": {"type": "array", "items": {"type": "string"}},
        "weight_used": {"type": "object"},
    },
    "required": ["evaluations", "top5_ids"],
}


def run(products: list[ProductFullResearch], weight_override: dict | None = None) -> EvaluationOutput:
    if not products:
        raise ValueError("没有产品数据可供评估，上游 Product Generator 或 Deep Research 可能失败")
    logger.info(f"Evaluation Agent 开始评估 {len(products)} 个产品")

    summaries = []
    for p in products:
        summaries.append(
            f"ID:{p.product_id} 名称:{p.product_name}\n"
            f"  市场:TAM={p.market.tam_usd_billion}B,SAM={p.market.sam_usd_billion}B,客户={','.join(p.market.key_customer_profiles[:2])}\n"
            f"  技术:研发{p.tech.development_timeline_months}月,{p.tech.team_size_minimum}人,预算{p.tech.initial_budget_usd}\n"
            f"  供应链:深圳生态={p.supply_chain.shenzhen_ecosystem_score}/10,BOM={p.supply_chain.bom_cost_estimate_usd},认证={','.join(p.supply_chain.certifications_needed)}\n"
            f"  竞争:壁垒={p.competition.entry_barrier},护城河={p.competition.moat_type}\n"
            f"  政策:推荐={p.policy.recommended_district},补贴={p.policy.estimated_subsidy_usd}\n"
        )

    context = f"请对以下 {len(products)} 个产品逐一评分：\n\n" + "\n".join(summaries)
    if weight_override:
        context += f"\n\n⚠️ 用户调整权重：{weight_override}"

    data = call_claude_structured(
        SYSTEM_PROMPT, context, EVAL_SCHEMA,
        model="claude-sonnet-4-6", max_tokens=6000,
    )
    data.setdefault("evaluations", [])
    data.setdefault("top5_ids", [])
    data.setdefault("honorable_mention_ids", [])
    data.setdefault("weight_used", {"市场机会": 30, "深圳落地可行性": 25, "小团队可执行性": 20, "竞争格局": 15, "时机": 10})

    result = EvaluationOutput(**data)
    logger.info(f"Evaluation Agent 完成，Top5: {result.top5_ids}")
    return result
