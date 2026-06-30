"""验证 Lens.org 专利检索工具（如果未配置 Key 或无权限，应优雅降级返回空列表）"""
from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv()

from tools.lens_tool import LensTool

key = os.environ.get("LENS_API_KEY", "").strip()
print(f"LENS_API_KEY 是否已配置: {'是' if key else '否'}")

tool = LensTool()
print(f"available 属性: {tool.available}")

results = tool.search_patents(["industrial vision inspection", "defect detection"], max_results=5)
print(f"返回结果数量: {len(results)}")

for r in results:
    print(f"  - {r['title'][:60]}")
    print(f"    申请人: {r['applicants']} | {r['jurisdiction']} | {r['date_published']}")
    print(f"    {r['url']}")

if not key:
    assert results == [], "未配置 Key 时应返回空列表"
    print("\n✓ 未配置 Key 时正确降级返回空列表（不报错，不阻断流程）")
elif len(results) == 0:
    print("\n⚠️ Key 已配置但返回 0 结果——可能账号没有 Patent API 权限，"
          "需要登录 lens.org 检查 Patent Search API 是否已开通")
else:
    print(f"\n✓ Lens.org 集成正常工作，检索到 {len(results)} 条真实专利数据")
