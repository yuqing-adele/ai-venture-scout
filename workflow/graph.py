from __future__ import annotations
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TypedDict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt

import agents.direction_planner as direction_planner
import agents.technology_scout as tech_scout
import agents.market_agent as market_agent
import agents.patent_agent as patent_agent
import agents.investment_agent as investment_agent
import agents.policy_agent as policy_agent
import agents.competitor_agent as competitor_agent
import agents.product_generator as product_generator
import agents.deep_research as deep_research
import agents.evaluation_agent as evaluation_agent
import agents.report_agent as report_agent

logger = logging.getLogger(__name__)


class GraphState(TypedDict, total=False):
    user_input: str
    run_id: str
    directions: list
    tech_research: list
    market_research: list
    patent_research: list
    investment_research: list
    policy_research: list
    competitor_research: list
    candidate_products: list
    selected_product_ids: list
    user_notes_checkpoint1: str
    product_details: dict
    evaluation_results: dict
    user_weight_override: dict
    user_notes_checkpoint2: str
    final_report_path: str
    final_report_markdown: str


# ── 节点函数 ──────────────────────────────────────────────────

def node_direction_planner(state: GraphState) -> GraphState:
    result = direction_planner.run(state["user_input"])
    return {"directions": [d.model_dump() for d in result.directions]}


def node_research(state: GraphState) -> GraphState:
    """6个研究 Agent 并行执行"""
    from models.schemas import TechDirection
    directions = [TechDirection(**d) for d in state["directions"]]

    tech_results, market_results, patent_results = [], [], []
    investment_results, policy_results, competitor_results = [], [], []

    def run_tech(d):    return tech_scout.run(d)
    def run_market(d):  return market_agent.run(d)
    def run_patent(d):  return patent_agent.run(d)
    def run_invest(d):  return investment_agent.run(d)
    def run_policy(d):  return policy_agent.run(d)
    def run_comp(d):    return competitor_agent.run(d)

    agent_fns = [run_tech, run_market, run_patent, run_invest, run_policy, run_comp]
    result_lists = [tech_results, market_results, patent_results,
                    investment_results, policy_results, competitor_results]

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = []
        for fn, results_list in zip(agent_fns, result_lists):
            for d in directions:
                futures.append((executor.submit(fn, d), results_list))

        for future, results_list in futures:
            try:
                results_list.append(future.result().model_dump())
            except Exception as e:
                logger.error(f"Research agent 失败: {e}")

    return {
        "tech_research": tech_results,
        "market_research": market_results,
        "patent_research": patent_results,
        "investment_research": investment_results,
        "policy_research": policy_results,
        "competitor_research": competitor_results,
    }


def node_product_generator(state: GraphState) -> GraphState:
    from models.schemas import (
        TechScoutOutput, MarketAgentOutput, PatentAgentOutput,
        InvestmentAgentOutput, PolicyAgentOutput, CompetitorAgentOutput,
        DirectionPlannerOutput, TechDirection,
    )
    result = product_generator.run(
        user_input=state["user_input"],
        tech=[TechScoutOutput(**d) for d in state.get("tech_research", [])],
        market=[MarketAgentOutput(**d) for d in state.get("market_research", [])],
        patent=[PatentAgentOutput(**d) for d in state.get("patent_research", [])],
        investment=[InvestmentAgentOutput(**d) for d in state.get("investment_research", [])],
        policy=[PolicyAgentOutput(**d) for d in state.get("policy_research", [])],
        competitor=[CompetitorAgentOutput(**d) for d in state.get("competitor_research", [])],
    )
    return {"candidate_products": [c.model_dump() for c in result.candidates]}


def node_checkpoint1(state: GraphState) -> GraphState:
    candidates = state.get("candidate_products", [])
    lines = ["\n发现以下候选产品方向：\n"]
    for c in candidates:
        lines.append(f"  {c['id']}  {c['name']}")
        lines.append(f"       {c['one_line_description']}")
    lines.append("\n操作说明：")
    lines.append("  - 直接回车 → 保留全部，继续深度研究")
    lines.append("  - 输入排除ID → 如：P005 P012 P018")
    lines.append("  - 输入添加 → 如：添加 轻量化机械臂关节模块")

    display = "\n".join(lines)
    user_response: str = interrupt(display)

    selected_ids = [c["id"] for c in candidates]
    if user_response and user_response.strip():
        resp = user_response.strip()
        if not resp.startswith("添加"):
            exclude = [x.strip() for x in resp.split() if x.strip().startswith("P")]
            selected_ids = [pid for pid in selected_ids if pid not in exclude]

    return {
        "selected_product_ids": selected_ids,
        "user_notes_checkpoint1": user_response or "",
    }


def node_deep_research(state: GraphState) -> GraphState:
    from models.schemas import CandidateProduct
    selected_ids = state.get("selected_product_ids", [])
    all_candidates = state.get("candidate_products", [])
    candidates = [
        CandidateProduct(**c) for c in all_candidates
        if c["id"] in selected_ids
    ]

    product_details: dict = {}

    def research_one(c):
        return c.id, deep_research.run(c)

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(research_one, c) for c in candidates]
        for future in as_completed(futures):
            try:
                pid, result = future.result()
                product_details[pid] = result.model_dump()
            except Exception as e:
                logger.error(f"Deep research 失败: {e}")

    return {"product_details": product_details}


def node_evaluation(state: GraphState) -> GraphState:
    from models.schemas import ProductFullResearch
    products = [ProductFullResearch(**v) for v in state.get("product_details", {}).values()]
    weight_override = state.get("user_weight_override")
    result = evaluation_agent.run(products, weight_override)
    return {"evaluation_results": result.model_dump()}


def node_checkpoint2(state: GraphState) -> GraphState:
    from models.schemas import EvaluationOutput
    eval_data = state.get("evaluation_results", {})
    if not eval_data:
        return {}

    ev = EvaluationOutput(**eval_data)
    lines = ["\n当前评分结果：\n"]
    lines.append(f"  {'排名':<4} {'产品名称':<30} {'总分':<6} {'市场':<5} {'深圳':<5} {'执行':<5} {'竞争':<5} {'时机'}")

    sorted_evals = sorted(ev.evaluations, key=lambda x: x.total_score, reverse=True)
    for i, e in enumerate(sorted_evals[:10], 1):
        scores = {s.dimension: s.score for s in e.dimension_scores}
        lines.append(
            f"  {i:<4} {e.product_name[:28]:<30} "
            f"{e.total_score:<6.0f} "
            f"{scores.get('市场机会',0):<5.0f} "
            f"{scores.get('深圳落地可行性',0):<5.0f} "
            f"{scores.get('小团队可执行性',0):<5.0f} "
            f"{scores.get('竞争格局',0):<5.0f} "
            f"{scores.get('时机',0):.0f}"
        )

    lines.append("\n操作说明：")
    lines.append("  - 直接回车 → 使用当前权重，生成报告")
    lines.append("  - 输入调整 → 如：市场35 深圳30 执行20 竞争10 时机5")

    display = "\n".join(lines)
    user_response: str = interrupt(display)

    weight_override = None
    if user_response and user_response.strip():
        # 尝试解析权重调整
        try:
            weight_override = _parse_weight_input(user_response)
        except Exception:
            pass

    return {
        "user_weight_override": weight_override,
        "user_notes_checkpoint2": user_response or "",
    }


def node_redo_evaluation(state: GraphState) -> GraphState:
    return node_evaluation(state)


def node_report(state: GraphState) -> GraphState:
    from models.schemas import ProductFullResearch, EvaluationOutput, DirectionPlannerOutput, TechDirection
    products = [ProductFullResearch(**v) for v in state.get("product_details", {}).values()]
    evaluation = EvaluationOutput(**state["evaluation_results"])
    directions_data = state.get("directions", [])
    directions_obj = DirectionPlannerOutput(
        directions=[TechDirection(**d) for d in directions_data],
        excluded_areas=[],
        research_focus="",
    )

    report_md, report_path = report_agent.run(
        user_input=state["user_input"],
        directions=directions_obj,
        products=products,
        evaluation=evaluation,
        run_id=state.get("run_id", "unknown"),
    )
    return {
        "final_report_markdown": report_md,
        "final_report_path": report_path,
    }


def _should_redo(state: GraphState) -> str:
    if state.get("user_weight_override"):
        return "redo_evaluation"
    return "report"


def _parse_weight_input(text: str) -> dict:
    import re
    mapping = {"市场": "市场机会", "深圳": "深圳落地可行性", "执行": "小团队可执行性",
               "竞争": "竞争格局", "时机": "时机"}
    result = {}
    for short, full in mapping.items():
        m = re.search(rf"{short}(\d+)", text)
        if m:
            result[full] = int(m.group(1))
    if result and sum(result.values()) != 100:
        raise ValueError("权重之和不等于100")
    return result


# ── 构建图 ────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(GraphState)

    g.add_node("direction_planner", node_direction_planner)
    g.add_node("research", node_research)
    g.add_node("product_generator", node_product_generator)
    g.add_node("checkpoint1", node_checkpoint1)
    g.add_node("deep_research", node_deep_research)
    g.add_node("evaluation", node_evaluation)
    g.add_node("checkpoint2", node_checkpoint2)
    g.add_node("redo_evaluation", node_redo_evaluation)
    g.add_node("report", node_report)

    g.add_edge(START, "direction_planner")
    g.add_edge("direction_planner", "research")
    g.add_edge("research", "product_generator")
    g.add_edge("product_generator", "checkpoint1")
    g.add_edge("checkpoint1", "deep_research")
    g.add_edge("deep_research", "evaluation")
    g.add_edge("evaluation", "checkpoint2")
    g.add_conditional_edges("checkpoint2", _should_redo, {
        "redo_evaluation": "redo_evaluation",
        "report": "report",
    })
    g.add_edge("redo_evaluation", "report")
    g.add_edge("report", END)

    checkpointer = MemorySaver()
    return g.compile(checkpointer=checkpointer)
