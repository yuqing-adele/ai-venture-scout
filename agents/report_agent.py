from __future__ import annotations
import logging
from datetime import datetime
from pathlib import Path
from models.schemas import (
    ProductFullResearch, EvaluationOutput, ProductEvaluation,
    DirectionPlannerOutput,
)
from agents.base import get_client

logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


def run(
    user_input: str,
    directions: DirectionPlannerOutput,
    products: list[ProductFullResearch],
    evaluation: EvaluationOutput,
    run_id: str,
) -> tuple[str, str]:
    """返回 (report_markdown, report_path)"""
    logger.info("Report Agent 开始生成报告")

    if not products:
        raise ValueError("没有产品研究数据，无法生成报告（拒绝在无数据情况下生成内容，防止幻觉）")
    if not evaluation.evaluations:
        raise ValueError("没有评分数据，无法生成报告（拒绝在无数据情况下生成内容，防止幻觉）")

    # 按评分排序
    eval_map = {e.product_id: e for e in evaluation.evaluations}
    product_map = {p.product_id: p for p in products}

    top5 = [eval_map[pid] for pid in evaluation.top5_ids if pid in eval_map]
    honorable = [eval_map[pid] for pid in evaluation.honorable_mention_ids if pid in eval_map]

    # 构建报告上下文
    top5_details = []
    for ev in top5:
        p = product_map.get(ev.product_id)
        if p:
            top5_details.append(_format_product_detail(ev, p))

    honorable_details = []
    for ev in honorable:
        p = product_map.get(ev.product_id)
        if p:
            honorable_details.append(_format_honorable(ev, p))

    context = f"""你是一名科技创业分析报告撰写专家。请根据以下研究数据，生成一份完整的中文创业机会分析报告。

用户背景：
{user_input}

研究聚焦方向：
{chr(10).join([f"- {d.name}（{d.category}）" for d in directions.directions])}

Top 5 产品详细数据：
{''.join(top5_details)}

候选产品数据（荣誉提名）：
{''.join(honorable_details)}

评分权重：{evaluation.weight_used}

今天日期：{datetime.utcnow().strftime('%Y-%m-%d')}

---

请生成一份完整的 Markdown 格式报告，包含以下结构：

# AI Venture Scout 创业机会分析报告

## 执行摘要（3–5句话）

## 研究范围

## Top 5 创业机会（每个产品详细分析）

### 1. [产品名称] — [分数]/100

**一句话定义**

**为什么值得做**

**市场分析**
- 市场规模、增长率、目标客户

**深圳落地可行性**
- 元器件、认证、本地生态

**小团队可执行性**
- 研发周期、人员、预算、MVP范围

**竞争格局**
- 竞争者、壁垒、差异化切入点

**政策支持**
- 适用政策、推荐注册区、补贴估算

**主要优势**

**主要风险**

**推荐理由**（结合用户具体背景）

（重复5次）

## 候选产品附录（荣誉提名）

（每个产品：名称、分数、一句话描述、最大优势、未进前五的原因）

## 最终推荐

**第一推荐**：[产品名] — [理由]
**第二推荐**：[产品名] — [理由]
**第三推荐**：[产品名] — [理由]

**下一步行动建议**

---

报告中所有数据结论务必准确反映研究数据，不要编造数字。"""

    client = get_client()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        messages=[{"role": "user", "content": context}],
    )

    report_md = response.content[0].text
    report_path = REPORTS_DIR / f"report_{run_id}.md"
    report_path.write_text(report_md, encoding="utf-8")

    # 附上所有引用来源
    all_citations = _collect_citations(products)
    if all_citations:
        report_md += "\n\n---\n\n## 参考文献\n\n"
        for i, c in enumerate(all_citations, 1):
            report_md += f"[{i}] **{c.get('source_name', '未知来源')}** — {c.get('claim', '')}\n"
            if c.get('url'):
                report_md += f"    🔗 {c.get('url')}\n"
            if c.get('publish_date'):
                report_md += f"    📅 {c.get('publish_date')} | 置信度：{c.get('confidence', 'medium')}\n"
            report_md += "\n"

    report_path.write_text(report_md, encoding="utf-8")
    logger.info(f"报告已保存：{report_path}")
    return report_md, str(report_path)


def _collect_citations(products: list) -> list[dict]:
    """从所有产品研究中收集所有引用来源，去重"""
    seen_urls = set()
    all_citations = []
    for p in products:
        for dim in [p.market, p.tech, p.competition, p.supply_chain, p.policy]:
            for c in dim.citations:
                url = c.url or c.claim
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_citations.append(c.model_dump())
    return all_citations


def _format_product_detail(ev: ProductEvaluation, p: ProductFullResearch) -> str:
    scores = {s.dimension: s.score for s in ev.dimension_scores}
    return f"""
产品：{ev.product_name} (ID: {ev.product_id})
总分：{ev.total_score}/100
维度分：市场={scores.get('市场机会',0)}/30，深圳={scores.get('深圳落地可行性',0)}/25，
       执行={scores.get('小团队可执行性',0)}/20，竞争={scores.get('竞争格局',0)}/15，时机={scores.get('时机',0)}/10
优势：{', '.join(ev.top_strengths)}
风险：{', '.join(ev.top_risks)}
市场：TAM={p.market.tam_usd_billion}B USD，SAM={p.market.sam_usd_billion}B，年收入目标第一年={p.market.som_year1_usd_million}M
      客户={', '.join(p.market.key_customer_profiles[:3])}，价格区间={p.market.selling_price_range}
技术：研发{p.tech.development_timeline_months}个月，{p.tech.team_size_minimum}人，预算{p.tech.initial_budget_usd} USD
      MVP={p.tech.mvp_scope}
供应链：BOM={p.supply_chain.bom_cost_estimate_usd} USD，深圳生态={p.supply_chain.shenzhen_ecosystem_score}/10
        认证={', '.join(p.supply_chain.certifications_needed)}，认证周期={p.supply_chain.certification_time_months}个月
政策：推荐注册={p.policy.recommended_district}，补贴估算={p.policy.estimated_subsidy_usd}
竞争：壁垒={p.competition.entry_barrier}，护城河类型={p.competition.moat_type}
"""


def _format_honorable(ev: ProductEvaluation, p: ProductFullResearch) -> str:
    return (
        f"\n产品：{ev.product_name} | 总分：{ev.total_score}/100 | "
        f"优势：{ev.top_strengths[0] if ev.top_strengths else ''} | "
        f"未进前五原因：{ev.top_risks[0] if ev.top_risks else ''}\n"
    )
