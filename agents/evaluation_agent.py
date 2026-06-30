from __future__ import annotations
import logging
from models.schemas import ProductFullResearch, EvaluationOutput, ProductEvaluation, DimensionScore
from agents.base import call_claude_structured

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一名科技创业投资评估专家。

按以下标准对每个产品打分。"小团队可执行性"这一维度必须拿用户背景里的真实团队规模、真实预算、真实技术能力
跟每个产品自身需要的人力/预算/技术要求做直接对比，不能套用任何与用户实际情况无关的通用标准。

市场机会（30分）：市场规模>100B=15分/10-100B=10分/<10B=5分；增长>30%=10/15-30%=7/<15%=3；需求真实B2B=5/概念=2

深圳落地可行性（25分）：LCSC全买=10/大部分=6/少数=2；本地生态有=8/部分=4/无=1；认证无=7/CE+FCC=4/3C+行业=1

小团队可执行性（20分，对比用户真实资源，不是通用档位）：
  - 人力缺口（8分）：产品所需最小团队规模 vs 用户实际人数（含可招聘的人）
    完全够用=8分 / 缺口1-2人但可招到=5分 / 缺口很大需要大幅扩招或融资才能补齐=2分
  - 预算缺口（7分）：产品所需研发预算 vs 用户实际预算（注意单位换算，统一成同一币种再比较）
    预算内有明显余量=7分 / 接近或略超预算上限=4分 / 远超预算需要额外融资=1分
  - 技术能力匹配（5分）：产品所需技术 vs 用户现有技术栈和经验
    用户现有能力能直接做=5分 / 需要学习但用户表态愿意学且可行=3分 / 技术差距很大，团队当前能力做不到=1分

竞争格局（15分）：大厂无布局=8/边缘=4/核心=1；市场有空白=7/有缝隙=4/红海=1

时机（10分）：TRL 6-7=5/4-5=3/其他=1；政策strong=5/moderate=3/weak=1

dimension 字段必须严格使用这5个名称之一："市场机会"、"深圳落地可行性"、"小团队可执行性"、"竞争格局"、"时机"，不要用别的措辞或缩写。

每个产品的 rationale 里，"小团队可执行性"维度必须明确写出"用户有X人/产品需要Y人"、"用户预算Z万/产品需要W万"这种具体对比，不能只给分数不给对比依据。

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


def run(
    products: list[ProductFullResearch],
    user_input: str = "",
    weight_override: dict | None = None,
) -> EvaluationOutput:
    if not products:
        raise ValueError("没有产品数据可供评估，上游 Product Generator 或 Deep Research 可能失败")
    logger.info(f"Evaluation Agent 开始评估 {len(products)} 个产品")

    summaries = []
    for p in products:
        summaries.append(
            f"ID:{p.product_id} 名称:{p.product_name}\n"
            f"  市场:TAM={p.market.tam_usd_billion}B,SAM={p.market.sam_usd_billion}B,客户={','.join(p.market.key_customer_profiles[:2])}\n"
            f"  技术:研发{p.tech.development_timeline_months}月,该产品需要最少{p.tech.team_size_minimum}人,该产品需要预算{p.tech.initial_budget_usd} USD\n"
            f"  供应链:深圳生态={p.supply_chain.shenzhen_ecosystem_score}/10,BOM={p.supply_chain.bom_cost_estimate_usd},认证={','.join(p.supply_chain.certifications_needed)}\n"
            f"  竞争:壁垒={p.competition.entry_barrier},护城河={p.competition.moat_type}\n"
            f"  政策:推荐={p.policy.recommended_district},补贴={p.policy.estimated_subsidy_usd}\n"
        )

    context = ""
    if user_input:
        context += f"⚠️ 用户的真实团队规模、预算、技术能力（小团队可执行性维度必须对比这些真实数字）：\n{user_input}\n\n"
    context += f"请对以下 {len(products)} 个产品逐一评分：\n\n" + "\n".join(summaries)
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
