"""
将 Markdown 报告导出为格式精美的 HTML。
中文 PDF 最可靠的方式：浏览器打开 → Ctrl+P → 另存为 PDF
"""
from __future__ import annotations
import sys
import glob
import subprocess
from pathlib import Path

try:
    import markdown
except ImportError:
    print("请先运行: pip install markdown")
    sys.exit(1)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  @page {{ margin: 2cm; }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans SC", "Source Han Sans CN",
                 "Hiragino Sans GB", Arial, sans-serif;
    font-size: 13px;
    line-height: 1.75;
    color: #1a1a2e;
    max-width: 900px;
    margin: 0 auto;
    padding: 40px 50px;
    background: white;
  }}
  h1 {{
    font-size: 26px;
    color: #1a1a2e;
    border-bottom: 3px solid #2563eb;
    padding-bottom: 10px;
    margin-top: 0;
  }}
  h2 {{
    font-size: 18px;
    color: #1e40af;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 5px;
    margin-top: 32px;
  }}
  h3 {{
    font-size: 15px;
    color: #1d4ed8;
    margin-top: 24px;
  }}
  h4 {{ font-size: 13px; color: #374151; font-weight: 600; }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 14px 0;
    font-size: 12px;
  }}
  th {{
    background: #2563eb;
    color: white;
    padding: 9px 12px;
    text-align: left;
    font-weight: 600;
  }}
  td {{
    padding: 8px 12px;
    border-bottom: 1px solid #e5e7eb;
    vertical-align: top;
  }}
  tr:nth-child(even) td {{ background: #f8fafc; }}
  blockquote {{
    border-left: 4px solid #2563eb;
    margin: 12px 0;
    padding: 8px 16px;
    background: #eff6ff;
    border-radius: 0 6px 6px 0;
    color: #1e40af;
    font-style: italic;
  }}
  code {{
    background: #f1f5f9;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 11px;
    color: #dc2626;
  }}
  pre {{
    background: #f1f5f9;
    padding: 14px;
    border-radius: 6px;
    overflow-x: auto;
    font-size: 11px;
    line-height: 1.5;
  }}
  pre code {{ background: none; color: #374151; padding: 0; }}
  hr {{
    border: none;
    border-top: 1px solid #e5e7eb;
    margin: 24px 0;
  }}
  a {{ color: #2563eb; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  ul, ol {{ padding-left: 24px; }}
  li {{ margin: 4px 0; }}
  strong {{ color: #1e3a5f; }}
  .print-hint {{
    background: #fef3c7;
    border: 1px solid #f59e0b;
    border-radius: 6px;
    padding: 12px 16px;
    margin-bottom: 24px;
    font-size: 12px;
    color: #92400e;
  }}
  @media print {{
    .print-hint {{ display: none; }}
    body {{ padding: 0; max-width: 100%; }}
    h2 {{ page-break-before: auto; }}
    h3 {{ page-break-after: avoid; }}
    table {{ page-break-inside: avoid; }}
  }}
</style>
</head>
<body>
<div class="print-hint">
  📄 <strong>导出 PDF：</strong>按 <kbd>Ctrl+P</kbd>（Mac: Cmd+P）→ 目标打印机选「另存为 PDF」→ 点「保存」
</div>
{body}
</body>
</html>"""


def convert(md_path: str | None = None) -> str:
    if md_path is None:
        reports = sorted(glob.glob("reports/report_*.md"), key=lambda f: Path(f).stat().st_mtime)
        if not reports:
            print("未找到报告文件（reports/report_*.md）")
            sys.exit(1)
        md_path = reports[-1]

    md_path = Path(md_path)
    print(f"转换：{md_path}")

    md_text = md_path.read_text(encoding="utf-8")
    html_body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "nl2br", "toc"],
    )

    title = md_path.stem.replace("_", " ").title()
    full_html = HTML_TEMPLATE.format(title=title, body=html_body)

    html_path = md_path.with_suffix(".html")
    html_path.write_text(full_html, encoding="utf-8")
    print(f"✓ HTML 已生成：{html_path}")
    print()
    print("  打开方式：在文件管理器双击 .html 文件，或用 Chrome/Edge 打开")
    print("  导出 PDF：Ctrl+P → 目标打印机选「另存为 PDF」→ 保存")

    # 自动在浏览器打开
    try:
        import os
        os.startfile(str(html_path))
        print("  （已自动在浏览器中打开）")
    except Exception:
        pass

    return str(html_path)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    convert(path)
