"""
全量测试：逐个验证所有 Agent。
尽量复用缓存，减少 API 调用成本。
"""
from __future__ import annotations
import json
import logging
import sys
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")

from models.schemas import TechDirection, CandidateProduct, UserConstraints

# 复用同一个方向，缓存命中率高
DIRECTION = TechDirection(
    name="工业视觉检测",
    category="AI硬件",
    rationale="深圳制造业密集，工厂视觉检测需求大",
    search_keywords=["industrial vision inspection", "AI quality control", "工业视觉检测"],
)

PRODUCT = CandidateProduct(
    id="P001",
    name="工业PCB焊点AI视觉检测模块",
    one_line_description="基于边缘AI的PCB焊点缺陷实时检测设备，精度达99%+，替代人工抽检",
    tech_direction="工业视觉检测",
    target_customer="PCB制造厂、EMS代工厂质量工程师",
    core_value_proposition="将人工抽检率从5%提升到100%在线检测，误检率<0.1%",
    why_shenzhen_can_do="华强北元器件齐全、本地PCB厂密集可做客户、嵌入式工程师多",
)

USER_INPUT = "我想在深圳做 AI 创业，方向是具身智能和工业 AI，团队 5 人，预算 200 万"

CONSTRAINTS = UserConstraints(
    team_size_current=5,
    budget_amount=2000000,
    budget_currency="RMB",
    existing_product_summary="",
    tech_capabilities=["嵌入式开发", "计算机视觉"],
    raw_description=USER_INPUT,
)

passed = []
failed = []


def test(name: str, fn):
    try:
        result = fn()
        passed.append(name)
        print(f"  ✓ {name}")
        return result
    except Exception as e:
        failed.append((name, str(e)))
        print(f"  ✗ {name}: {e}")
        return None


print("\n=== 测试 Constraint Extractor ===")
import agents.constraint_extractor as ce
ce_result = test("Constraint Extractor", lambda: ce.run(USER_INPUT))
if ce_result:
    print(f"    团队{ce_result.team_size_current}人，预算{ce_result.budget_amount}{ce_result.budget_currency}")

print("\n=== 测试 Direction Planner ===")
import agents.direction_planner as dp
dp_result = test("Direction Planner", lambda: dp.run(USER_INPUT, CONSTRAINTS))

print("\n=== 测试 6 个研究 Agent（复用缓存）===")
import agents.technology_scout as ts
import agents.market_agent as ma
import agents.patent_agent as pa
import agents.investment_agent as ia
import agents.policy_agent as pola
import agents.competitor_agent as ca

tech_r = test("Technology Scout", lambda: ts.run(DIRECTION))
market_r = test("Market Agent", lambda: ma.run(DIRECTION))
patent_r = test("Patent Agent", lambda: pa.run(DIRECTION))
invest_r = test("Investment Agent", lambda: ia.run(DIRECTION))
policy_r = test("Policy Agent", lambda: pola.run(DIRECTION))
comp_r = test("Competitor Agent", lambda: ca.run(DIRECTION))

print("\n=== 测试 Product Generator ===")
import agents.product_generator as pg
pg_result = None
if all([tech_r, market_r, patent_r, invest_r, policy_r, comp_r]):
    pg_result = test("Product Generator", lambda: pg.run(
        user_input=USER_INPUT,
        constraints=CONSTRAINTS,
        tech=[tech_r],
        market=[market_r],
        patent=[patent_r],
        investment=[invest_r],
        policy=[policy_r],
        competitor=[comp_r],
    ))
    if pg_result:
        print(f"    生成了 {len(pg_result.candidates)} 个候选产品")

print("\n=== 测试 Deep Research（1个产品，5维度并行）===")
import agents.deep_research as dr
deep_r = test("Deep Research", lambda: dr.run(PRODUCT))

print("\n=== 测试 Evaluation Agent ===")
import agents.evaluation_agent as ea
eval_r = None
if deep_r:
    eval_r = test("Evaluation Agent", lambda: ea.run([deep_r], CONSTRAINTS))
    if eval_r:
        print(f"    评分完成，Top5: {eval_r.top5_ids}")

print("\n=== 测试 Report Agent ===")
import agents.report_agent as ra
from models.schemas import DirectionPlannerOutput
if eval_r and deep_r:
    directions_obj = DirectionPlannerOutput(
        directions=[DIRECTION],
        excluded_areas=[],
        research_focus="工业AI",
    )
    test("Report Agent", lambda: ra.run(
        user_input=USER_INPUT,
        constraints=CONSTRAINTS,
        directions=directions_obj,
        products=[deep_r],
        evaluation=eval_r,
        run_id="test001",
    ))

print("\n=== 测试 Workflow 图构建 ===")
from workflow.graph import build_graph
test("Workflow Graph Build", build_graph)

# 汇总
print(f"\n{'='*40}")
print(f"通过：{len(passed)}/{len(passed)+len(failed)}")
if failed:
    print("\n失败列表：")
    for name, err in failed:
        print(f"  ✗ {name}: {err}")
    sys.exit(1)
else:
    print("全部通过 ✓")
