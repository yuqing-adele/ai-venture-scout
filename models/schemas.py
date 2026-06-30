from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field, field_validator


# ── 基础引用模型 ──────────────────────────────────────────────

class Citation(BaseModel):
    claim: str = ""
    source_name: str = ""
    url: str = ""
    publish_date: str = ""
    confidence: str = "medium"
    retrieval_date: str = ""


# ── User Constraints（结构化用户约束，所有下游Agent的事实来源）───

class UserConstraints(BaseModel):
    team_size_current: int          # 当前团队人数
    team_size_hireable: int = 0     # 还可以招聘的人数（如果用户提到）
    budget_amount: float            # 预算数值
    budget_currency: str = "RMB"    # 预算货币单位
    timeline_months: int = 12       # 期望多久内要有付费客户/见效
    location: str = "深圳"
    existing_product_summary: str = ""    # 已有产品摘要（如果有）
    existing_customer_summary: str = ""   # 已有客户资源摘要（如果有）
    tech_capabilities: list[str] = []     # 团队已具备的技术能力
    tech_gaps: list[str] = []             # 团队明确缺乏的能力
    excluded_directions: list[str] = []   # 明确排除的方向
    raw_description: str = ""             # 原始完整描述，供需要更多细节/语境的Agent参考

    @field_validator("team_size_current", mode="after")
    @classmethod
    def validate_team_size(cls, v):
        if v <= 0 or v > 1000:
            raise ValueError(
                f"提取出的团队人数不合理（{v}），原始输入可能损坏、编码错误，或提取失败，不应继续往下跑"
            )
        return v

    @field_validator("budget_amount", mode="after")
    @classmethod
    def validate_budget(cls, v):
        if v <= 0:
            raise ValueError(
                f"提取出的预算金额不合理（{v}），原始输入可能损坏、编码错误，或提取失败，不应继续往下跑"
            )
        return v

    def format_for_prompt(self) -> str:
        """统一的结构化事实展示格式，所有需要对比用户真实资源的Agent都用这个，
        确保每个Agent看到的是同一份明确数字，而不是各自去裸文本里找。"""
        lines = [
            "【用户真实约束（结构化事实，必须以这里的数字为准，不能用其他来源的数字替代）】",
            f"  当前团队人数：{self.team_size_current} 人",
        ]
        if self.team_size_hireable:
            lines.append(f"  还可以招聘：{self.team_size_hireable} 人")
        lines.append(f"  预算：{self.budget_amount} {self.budget_currency}")
        lines.append(f"  期望见效时间：{self.timeline_months} 个月内")
        lines.append(f"  地点：{self.location}")
        if self.existing_product_summary:
            lines.append(f"  已有产品：{self.existing_product_summary}")
        if self.existing_customer_summary:
            lines.append(f"  已有客户资源：{self.existing_customer_summary}")
        if self.tech_capabilities:
            lines.append(f"  已具备技术能力：{', '.join(self.tech_capabilities)}")
        if self.tech_gaps:
            lines.append(f"  明确缺乏的能力：{', '.join(self.tech_gaps)}")
        if self.excluded_directions:
            lines.append(f"  明确排除的方向：{', '.join(self.excluded_directions)}")
        return "\n".join(lines)


# ── Direction Planner ─────────────────────────────────────────

class TechDirection(BaseModel):
    name: str
    category: str
    rationale: str
    search_keywords: list[str]


class DirectionPlannerOutput(BaseModel):
    directions: list[TechDirection]
    excluded_areas: list[str] = []
    research_focus: str = ""


# ── Technology Scout ──────────────────────────────────────────

class PaperTrend(BaseModel):
    title: str = ""
    year: int = 0
    citation_count: int = 0
    key_finding: str = ""
    source: Citation = Field(default_factory=Citation)

    @field_validator("citation_count", "year", mode="before")
    @classmethod
    def coerce_none_to_zero(cls, v):
        return 0 if v is None else v


class TechScoutOutput(BaseModel):
    direction_name: str
    trl_level: int = 5
    trl_rationale: str = ""
    paper_volume_trend: str = "stable"
    key_papers: list[PaperTrend] = []
    github_activity: str = "moderate"
    key_breakthroughs: list[str] = []
    citations: list[Citation] = []


# ── Market Agent ──────────────────────────────────────────────

class MarketAgentOutput(BaseModel):
    direction_name: str
    market_size_2024_usd_billion: float = 0.0
    cagr_5year_percent: float = 0.0
    growth_drivers: list[str] = []
    target_segments: list[str] = []
    geographic_focus: str = "Global"
    market_maturity: str = "growing"
    china_market_share_percent: float | None = None
    citations: list[Citation] = []


# ── Patent Agent ──────────────────────────────────────────────

class PatentAgentOutput(BaseModel):
    direction_name: str
    patent_density: str = "medium"
    major_patent_holders: list[str] = []
    chinese_patent_holders: list[str] = []
    key_patent_areas: list[str] = []
    freedom_to_operate_risk: str = "medium"
    risk_rationale: str = ""
    citations: list[Citation] = []


# ── Investment Agent ──────────────────────────────────────────

class FundingEvent(BaseModel):
    company: str = ""
    amount_usd_million: float = 0.0
    round: str = "unknown"
    date: str = ""
    investors: list[str] = []
    source: Citation | None = None


class InvestmentAgentOutput(BaseModel):
    direction_name: str
    investment_heat: str = "warm"
    total_funding_2023_2025_usd_million: float = 0.0
    notable_deals: list[FundingEvent] = []
    top_vc_investors: list[str] = []
    china_vc_interest: str = "medium"
    investment_stage_focus: str = "早期"
    citations: list[Citation] = []


# ── Policy Agent ─────────────────────────────────────────────

class PolicyItem(BaseModel):
    policy_name: str = ""
    issuing_body: str = ""
    level: str = "national"
    district: str | None = None
    key_support: str = ""
    benefit_for_startup: str = ""
    source: Citation = Field(default_factory=Citation)


class PolicyAgentOutput(BaseModel):
    direction_name: str
    policy_support_level: str = "moderate"
    national_policies: list[PolicyItem] = []
    shenzhen_city_policies: list[PolicyItem] = []
    district_policies: list[PolicyItem] = []
    best_district: str = "南山区"
    total_subsidy_estimate: str = ""
    citations: list[Citation] = []


# ── Competitor Agent ──────────────────────────────────────────

class Competitor(BaseModel):
    name: str = ""
    country: str = "未知"
    funding_total_usd_million: float | None = None
    stage: str = "startup"
    key_product: str = ""
    source: Citation | None = None

    @field_validator("funding_total_usd_million", mode="before")
    @classmethod
    def coerce_unknown_to_none(cls, v):
        if isinstance(v, str):
            return None
        return v


class CompetitorAgentOutput(BaseModel):
    direction_name: str
    big_tech_players: list[str] = []
    big_tech_threat_level: str = "medium"
    startup_competitors: list[Competitor] = []
    chinese_competitors: list[Competitor] = []
    market_concentration: str = "fragmented"
    differentiation_gaps: list[str] = []
    citations: list[Citation] = []


# ── Product Generator ─────────────────────────────────────────

class CandidateProduct(BaseModel):
    id: str
    name: str
    one_line_description: str = ""
    tech_direction: str = ""
    target_customer: str = ""
    core_value_proposition: str = ""
    why_shenzhen_can_do: str = ""


class ProductGeneratorOutput(BaseModel):
    candidates: list[CandidateProduct]
    generation_rationale: str = ""


# ── Deep Research：5个维度 ─────────────────────────────────────

class MarketDeepDive(BaseModel):
    product_id: str
    tam_usd_billion: float = 0.0
    sam_usd_billion: float = 0.0
    som_year1_usd_million: float = 0.0
    key_customer_profiles: list[str] = []
    sales_channel: str = ""
    selling_price_range: str = ""
    citations: list[Citation] = []


class TechDeepDive(BaseModel):
    product_id: str
    core_technologies: list[str] = []
    development_timeline_months: int = 0
    team_size_minimum: int = 0
    initial_budget_usd: str = ""
    key_technical_risks: list[str] = []
    mvp_scope: str = ""
    citations: list[Citation] = []


class CompetitionDeepDive(BaseModel):
    product_id: str
    direct_competitors: list[str] = []
    competitive_advantage: str = ""
    moat_type: str = "技术"
    entry_barrier: str = "medium"
    citations: list[Citation] = []


class ComponentAvailability(BaseModel):
    component_name: str = ""
    available_on_lcsc: bool = True
    lcsc_price_usd: float | None = None
    lead_time_weeks: int | None = None
    moq: int | None = None
    alternative_sources: list[str] = []


class SupplyChainDeepDive(BaseModel):
    product_id: str
    key_components: list[ComponentAvailability] = []
    bom_cost_estimate_usd: str = ""
    local_manufacturer_available: bool = True
    certifications_needed: list[str] = []
    certification_time_months: int = 0
    certification_cost_usd: str = ""
    shenzhen_ecosystem_score: int = 5
    citations: list[Citation] = []


class PolicyDeepDive(BaseModel):
    product_id: str
    best_applicable_policies: list[str] = []
    recommended_district: str = "南山区"
    estimated_subsidy_usd: str = ""
    policy_stability: str = "stable"
    citations: list[Citation] = []


class ProductFullResearch(BaseModel):
    product_id: str
    product_name: str
    market: MarketDeepDive
    tech: TechDeepDive
    competition: CompetitionDeepDive
    supply_chain: SupplyChainDeepDive
    policy: PolicyDeepDive


# ── Evaluation Agent ──────────────────────────────────────────

class DimensionScore(BaseModel):
    dimension: str
    score: float = 0.0
    max_score: float = 0.0
    rationale: str = ""


class ProductEvaluation(BaseModel):
    product_id: str
    product_name: str
    total_score: float = 0.0
    dimension_scores: list[DimensionScore] = []
    top_strengths: list[str] = []
    top_risks: list[str] = []
    tier: str = "honorable_mention"


class EvaluationOutput(BaseModel):
    evaluations: list[ProductEvaluation]
    top5_ids: list[str] = []
    honorable_mention_ids: list[str] = []
    weight_used: dict[str, float] = Field(default_factory=lambda: {
        "市场机会": 30, "深圳落地可行性": 25, "小团队可执行性": 20,
        "竞争格局": 15, "时机": 10,
    })

    @field_validator("weight_used", mode="before")
    @classmethod
    def clean_weights(cls, v):
        import re
        if isinstance(v, dict):
            return {
                k: float(re.sub(r"[^\d.]", "", str(val)) or "0")
                if isinstance(val, str) else float(val)
                for k, val in v.items()
            }
        return v


# ── Global State ──────────────────────────────────────────────

class ResearchState(BaseModel):
    user_input: str = ""
    run_id: str = ""
    directions: list[TechDirection] = []
    research_focus: str = ""
    tech_research: list[TechScoutOutput] = []
    market_research: list[MarketAgentOutput] = []
    patent_research: list[PatentAgentOutput] = []
    investment_research: list[InvestmentAgentOutput] = []
    policy_research: list[PolicyAgentOutput] = []
    competitor_research: list[CompetitorAgentOutput] = []
    candidate_products: list[CandidateProduct] = []
    selected_product_ids: list[str] = []
    user_notes_checkpoint1: str = ""
    product_details: dict[str, Any] = {}
    evaluation_results: EvaluationOutput | None = None
    user_weight_override: dict[str, float] | None = None
    user_notes_checkpoint2: str = ""
    final_report_path: str = ""
    final_report_markdown: str = ""
