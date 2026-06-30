"""从已持久化的 SQLite 状态重新生成报告，不重跑研究/评分阶段（省钱）"""
from __future__ import annotations
import sys
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

from workflow.graph import build_graph
import agents.report_agent as report_agent
from models.schemas import ProductFullResearch, EvaluationOutput, DirectionPlannerOutput, TechDirection, UserConstraints

run_id = sys.argv[1] if len(sys.argv) > 1 else "guided01"

app = build_graph()
config = {"configurable": {"thread_id": run_id}}
state = app.get_state(config).values

if "user_constraints" not in state:
    print(f"错误：run_id={run_id} 的存档里没有 user_constraints（可能是旧版本跑的，结构升级前的存档），无法用新版report_agent重新生成")
    sys.exit(1)

products = [ProductFullResearch(**v) for v in state.get("product_details", {}).values()]
evaluation = EvaluationOutput(**state["evaluation_results"])
constraints = UserConstraints(**state["user_constraints"])
directions_data = state.get("directions", [])
directions_obj = DirectionPlannerOutput(
    directions=[TechDirection(**d) for d in directions_data],
    excluded_areas=[],
    research_focus="",
)

print(f"加载到 {len(products)} 个产品，评分包含 {len(evaluation.evaluations)} 条")

report_md, report_path = report_agent.run(
    user_input=state["user_input"],
    constraints=constraints,
    directions=directions_obj,
    products=products,
    evaluation=evaluation,
    run_id=run_id + "_v2",
)

print(f"\n✓ 新报告已保存：{report_path}")
