"""快速测试 Technology Scout Agent"""
import json
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

from models.schemas import TechDirection
from agents.technology_scout import run

direction = TechDirection(
    name="工业视觉检测",
    category="AI硬件",
    rationale="深圳制造业密集，工厂视觉检测需求大",
    search_keywords=["industrial vision inspection", "AI quality control", "工业视觉检测"],
)

print("开始测试 Technology Scout...")
result = run(direction)

print("\n结果：")
print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
print(f"\nTRL 等级：{result.trl_level}")
print(f"论文趋势：{result.paper_volume_trend}")
print(f"GitHub 活跃度：{result.github_activity}")
print(f"引用来源数量：{len(result.citations)}")
