from __future__ import annotations
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from models.schemas import (
    CandidateProduct, ProductFullResearch,
    MarketDeepDive, TechDeepDive, CompetitionDeepDive,
    SupplyChainDeepDive, PolicyDeepDive,
)
from agents.base import call_claude_structured
from agents._schemas import MARKET_DEEP, TECH_DEEP, COMPETITION_DEEP, SUPPLY_CHAIN_DEEP, POLICY_DEEP
from tools.tavily_tool import TavilyTool

logger = logging.getLogger(__name__)


def _ctx(task: str, product: CandidateProduct, results: list, today: str) -> str:
    c = (f"任务：{task}\n产品：{product.name}\n描述：{product.one_line_description}\n"
         f"目标客户：{product.target_customer}\n今天：{today}\n\n")
    for r in results[:6]:
        c += f"- {r.get('title','')}\n  {r.get('url','')}\n  {r.get('content','')[:350]}\n\n"
    return c


def _market(product: CandidateProduct, tavily: TavilyTool, today: str) -> MarketDeepDive:
    results = []
    try:
        results = tavily.search(f"{product.name} market size TAM SAM customers revenue 2024", max_results=5)
    except Exception as e:
        logger.warning(f"市场搜索失败: {e}")
    data = call_claude_structured(
        "你是市场分析师。分析产品市场深度，所有文字使用中文。",
        _ctx("市场深度分析", product, results, today), MARKET_DEEP, max_tokens=2048,
    )
    data["product_id"] = product.id
    data.setdefault("key_customer_profiles", [])
    data.setdefault("citations", [])
    return MarketDeepDive(**data)


def _tech(product: CandidateProduct, tavily: TavilyTool, today: str) -> TechDeepDive:
    results = []
    try:
        results = tavily.search(f"{product.name} technology development timeline team cost MVP", max_results=5)
    except Exception as e:
        logger.warning(f"技术搜索失败: {e}")
    data = call_claude_structured(
        "你是技术评估专家。分析产品技术可行性，所有文字使用中文。",
        _ctx("技术可行性分析", product, results, today), TECH_DEEP, max_tokens=2048,
    )
    data["product_id"] = product.id
    data.setdefault("core_technologies", [])
    data.setdefault("key_technical_risks", [])
    data.setdefault("citations", [])
    return TechDeepDive(**data)


def _competition(product: CandidateProduct, tavily: TavilyTool, today: str) -> CompetitionDeepDive:
    results = []
    try:
        results = tavily.search(f"{product.name} competitors alternatives comparison 2024", max_results=5)
    except Exception as e:
        logger.warning(f"竞争搜索失败: {e}")
    data = call_claude_structured(
        "你是竞争分析师。分析产品竞争格局，所有文字使用中文。",
        _ctx("竞争深度分析", product, results, today), COMPETITION_DEEP, max_tokens=1500,
    )
    data["product_id"] = product.id
    data.setdefault("direct_competitors", [])
    data.setdefault("citations", [])
    return CompetitionDeepDive(**data)


def _supply_chain(product: CandidateProduct, tavily: TavilyTool, today: str) -> SupplyChainDeepDive:
    results = []
    try:
        results = tavily.search(f"{product.name} components BOM cost LCSC Shenzhen supply chain certification", max_results=5)
        results += tavily.search(f"{product.name} 元器件 深圳 供应链 认证 CE FCC 3C", max_results=3)
    except Exception as e:
        logger.warning(f"供应链搜索失败: {e}")
    data = call_claude_structured(
        "你是深圳供应链专家。分析产品供应链可行性，所有文字使用中文。",
        _ctx("深圳供应链分析", product, results, today), SUPPLY_CHAIN_DEEP, max_tokens=2500,
    )
    data["product_id"] = product.id
    data.setdefault("key_components", [])
    data.setdefault("certifications_needed", [])
    data.setdefault("citations", [])
    return SupplyChainDeepDive(**data)


def _policy(product: CandidateProduct, tavily: TavilyTool, today: str) -> PolicyDeepDive:
    results = []
    try:
        results = tavily.search_policies(f"{product.tech_direction} 深圳 创业补贴 政策 {product.name}")
    except Exception as e:
        logger.warning(f"政策搜索失败: {e}")
    data = call_claude_structured(
        "你是政策研究员。分析产品适用的政策支持，所有文字使用中文。",
        _ctx("政策匹配分析", product, results, today), POLICY_DEEP, max_tokens=1500,
    )
    data["product_id"] = product.id
    data.setdefault("best_applicable_policies", [])
    data.setdefault("citations", [])
    return PolicyDeepDive(**data)


def run(product: CandidateProduct) -> ProductFullResearch:
    logger.info(f"Deep Research 开始：{product.name}")
    tavily = TavilyTool()
    today = datetime.utcnow().strftime("%Y-%m-%d")

    defaults = {
        "market": MarketDeepDive(product_id=product.id),
        "tech": TechDeepDive(product_id=product.id),
        "competition": CompetitionDeepDive(product_id=product.id),
        "supply_chain": SupplyChainDeepDive(product_id=product.id),
        "policy": PolicyDeepDive(product_id=product.id),
    }
    tasks = {
        "market": lambda: _market(product, tavily, today),
        "tech": lambda: _tech(product, tavily, today),
        "competition": lambda: _competition(product, tavily, today),
        "supply_chain": lambda: _supply_chain(product, tavily, today),
        "policy": lambda: _policy(product, tavily, today),
    }
    results = dict(defaults)
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fn): name for name, fn in tasks.items()}
        for future in as_completed(futures):
            name = futures[future]
            try:
                results[name] = future.result()
            except Exception as e:
                logger.error(f"Deep Research [{name}] 失败，使用默认值：{e}")

    return ProductFullResearch(
        product_id=product.id, product_name=product.name,
        market=results["market"], tech=results["tech"],
        competition=results["competition"], supply_chain=results["supply_chain"],
        policy=results["policy"],
    )
