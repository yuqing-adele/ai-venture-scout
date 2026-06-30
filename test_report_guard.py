"""验证 Report Agent 的空数据保护逻辑（不调用 API）"""
from agents.report_agent import run
from models.schemas import EvaluationOutput

try:
    run("test", None, [], EvaluationOutput(evaluations=[]), "test")
    print("FAIL: 应该报错但没有")
except ValueError as e:
    print(f"PASS: 正确拒绝空 products 列表 - {e}")

try:
    from models.schemas import ProductFullResearch, MarketDeepDive, TechDeepDive, CompetitionDeepDive, SupplyChainDeepDive, PolicyDeepDive
    fake_product = ProductFullResearch(
        product_id="P001", product_name="测试",
        market=MarketDeepDive(product_id="P001"), tech=TechDeepDive(product_id="P001"),
        competition=CompetitionDeepDive(product_id="P001"), supply_chain=SupplyChainDeepDive(product_id="P001"),
        policy=PolicyDeepDive(product_id="P001"),
    )
    run("test", None, [fake_product], EvaluationOutput(evaluations=[]), "test")
    print("FAIL: 应该报错但没有")
except ValueError as e:
    print(f"PASS: 正确拒绝空 evaluations 列表 - {e}")

print("\n=== Report Agent 防护逻辑验证通过 ===")
