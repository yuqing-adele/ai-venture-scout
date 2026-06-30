"""验证确认点1的ID解析逻辑（纯逻辑测试，不调用任何API）"""
from workflow.graph import resolve_selected_ids

all_ids = [f"P{str(i).zfill(3)}" for i in range(1, 11)]  # P001..P010

# 1. 空输入 → 保留全部
assert resolve_selected_ids(all_ids, "") == all_ids
assert resolve_selected_ids(all_ids, None) == all_ids
print("PASS: 空输入保留全部")

# 2. 排除模式
result = resolve_selected_ids(all_ids, "排除 P002 P005")
assert result == ["P001", "P003", "P004", "P006", "P007", "P008", "P009", "P010"]
print(f"PASS: 排除模式正确，剩余{len(result)}个")

# 3. 保留模式（新功能，重点测试）
result = resolve_selected_ids(all_ids, "保留 P001 P003 P007")
assert result == ["P001", "P003", "P007"], f"实际结果: {result}"
print(f"PASS: 保留模式正确，剩余{len(result)}个 = {result}")

# 4. "只保留" 也要支持
result = resolve_selected_ids(all_ids, "只保留 P001 P002")
assert result == ["P001", "P002"]
print("PASS: 只保留 关键词正确")

# 5. 添加模式（暂不影响选择，全部保留）
result = resolve_selected_ids(all_ids, "添加 轻量化机械臂关节模块")
assert result == all_ids
print("PASS: 添加模式不影响现有选择")

# 6. 向后兼容：纯ID列表无动词，按排除理解
result = resolve_selected_ids(all_ids, "P002 P005")
assert result == ["P001", "P003", "P004", "P006", "P007", "P008", "P009", "P010"]
print("PASS: 向后兼容（无动词纯ID列表）按排除处理")

# 7. 保留模式但ID不存在于候选列表中，应该被忽略
result = resolve_selected_ids(all_ids, "保留 P001 P999")
assert result == ["P001"], f"实际结果: {result}"
print("PASS: 保留模式正确过滤掉不存在的ID")

print("\n=== 确认点1解析逻辑全部验证通过 ===")
