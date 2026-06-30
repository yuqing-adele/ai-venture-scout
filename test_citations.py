"""验证报告末尾引用文献功能（不调用 Claude API，纯逻辑测试）"""
from __future__ import annotations
from models.schemas import (
    ProductFullResearch, MarketDeepDive, TechDeepDive, CompetitionDeepDive,
    SupplyChainDeepDive, PolicyDeepDive, Citation,
)
from agents.report_agent import _collect_citations

# 构造两个产品，每个维度都有引用，且有重复 URL（测试去重）
def make_citation(claim, url, source="测试来源"):
    return Citation(claim=claim, source_name=source, url=url, publish_date="2026-01",
                     confidence="high", retrieval_date="2026-06-30")

product_a = ProductFullResearch(
    product_id="P001",
    product_name="测试产品A",
    market=MarketDeepDive(product_id="P001", citations=[
        make_citation("市场规模100亿", "https://example.com/market1"),
        make_citation("增长率20%", "https://example.com/market2"),
    ]),
    tech=TechDeepDive(product_id="P001", citations=[
        make_citation("技术成熟", "https://example.com/tech1"),
    ]),
    competition=CompetitionDeepDive(product_id="P001", citations=[]),
    supply_chain=SupplyChainDeepDive(product_id="P001", citations=[
        make_citation("元器件充足", "https://example.com/supply1"),
    ]),
    policy=PolicyDeepDive(product_id="P001", citations=[
        make_citation("政策支持", "https://example.com/policy1"),
    ]),
)

product_b = ProductFullResearch(
    product_id="P002",
    product_name="测试产品B",
    market=MarketDeepDive(product_id="P002", citations=[
        make_citation("市场规模100亿", "https://example.com/market1"),  # 重复URL，应该被去重
    ]),
    tech=TechDeepDive(product_id="P002", citations=[
        make_citation("新技术", "https://example.com/tech2"),
    ]),
    competition=CompetitionDeepDive(product_id="P002", citations=[]),
    supply_chain=SupplyChainDeepDive(product_id="P002", citations=[]),
    policy=PolicyDeepDive(product_id="P002", citations=[]),
)

citations = _collect_citations([product_a, product_b])

print(f"总引用数（去重后）: {len(citations)}")
print("\n详细列表：")
for i, c in enumerate(citations, 1):
    print(f"[{i}] {c['source_name']} — {c['claim']}")
    print(f"    {c['url']}")

# 验证逻辑
expected_unique_urls = {
    "https://example.com/market1", "https://example.com/market2",
    "https://example.com/tech1", "https://example.com/supply1",
    "https://example.com/policy1", "https://example.com/tech2",
}
actual_urls = {c["url"] for c in citations}

assert len(citations) == 6, f"应该是6条去重后的引用，实际是{len(citations)}"
assert actual_urls == expected_unique_urls, f"URL集合不匹配: {actual_urls}"
print(f"\n✓ 去重逻辑正确：6条唯一引用（市场规模100亿的重复URL被正确去重）")

# 测试空产品列表情况（应该返回空列表，不报错）
empty_result = _collect_citations([])
assert empty_result == []
print("✓ 空产品列表正确返回空引用列表")

print("\n=== 引用文献功能验证通过 ===")
