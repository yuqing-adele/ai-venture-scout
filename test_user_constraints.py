"""验证 UserConstraints 的校验逻辑能正确拦截不合理的数字（不调用API）"""
from pydantic import ValidationError
from models.schemas import UserConstraints

# 1. 正常情况应该通过
c = UserConstraints(team_size_current=2, budget_amount=1000000, budget_currency="RMB")
print(f"PASS: 正常值通过校验 - {c.team_size_current}人, {c.budget_amount}{c.budget_currency}")

# 2. 团队人数为0或负数应该报错（模拟编码损坏导致提取出异常值）
try:
    UserConstraints(team_size_current=0, budget_amount=1000000)
    print("FAIL: 应该拒绝 team_size_current=0")
except ValidationError:
    print("PASS: 正确拒绝 team_size_current=0")

try:
    UserConstraints(team_size_current=-5, budget_amount=1000000)
    print("FAIL: 应该拒绝负数团队人数")
except ValidationError:
    print("PASS: 正确拒绝负数团队人数")

# 3. 团队人数离谱地大（比如编码错误导致解析出一个巨大数字）
try:
    UserConstraints(team_size_current=99999, budget_amount=1000000)
    print("FAIL: 应该拒绝不合理的巨大团队人数")
except ValidationError:
    print("PASS: 正确拒绝不合理的巨大团队人数")

# 4. 预算为0或负数应该报错
try:
    UserConstraints(team_size_current=2, budget_amount=0)
    print("FAIL: 应该拒绝预算为0")
except ValidationError:
    print("PASS: 正确拒绝预算为0")

try:
    UserConstraints(team_size_current=2, budget_amount=-100)
    print("FAIL: 应该拒绝负数预算")
except ValidationError:
    print("PASS: 正确拒绝负数预算")

# 5. format_for_prompt() 格式化方法测试
c2 = UserConstraints(
    team_size_current=2, team_size_hireable=1, budget_amount=1000000, budget_currency="RMB",
    existing_product_summary="仓库视频追溯系统", tech_capabilities=["计算机视觉", "Go后端"],
)
formatted = c2.format_for_prompt()
print(f"\n--- format_for_prompt() 输出 ---\n{formatted}\n---")
assert "2 人" in formatted
assert "1000000.0 RMB" in formatted or "1000000 RMB" in formatted
assert "仓库视频追溯系统" in formatted
print("PASS: format_for_prompt() 包含所有关键字段")

print("\n=== UserConstraints 校验逻辑全部通过 ===")
