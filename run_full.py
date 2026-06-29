"""
完整分析运行脚本（自动接受确认点，适合第一次测试）
"""
from __future__ import annotations
import logging
import sys
import uuid
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from langgraph.types import Command

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)

console = Console()

USER_INPUT = """
我想在深圳做 AI 创业。
团队：5人，技术背景涵盖嵌入式开发、计算机视觉、算法。
预算：200万人民币以内跑起来第一版。
方向偏好：AI、具身智能、工业 AI、机器人、AI 硬件。
不想做：纯软件 SaaS、消费品、医疗器械。
目标市场：优先国内 B2B，出口欧美是加分项。
希望充分利用深圳供应链优势。
"""


def main():
    from workflow.graph import build_graph

    console.print(Panel.fit(
        "[bold cyan]AI Venture Scout[/bold cyan] — 完整分析运行中",
        border_style="cyan",
    ))
    console.print(f"\n[bold]用户背景：[/bold]{USER_INPUT.strip()}\n")

    run_id = uuid.uuid4().hex[:8]
    config = {"configurable": {"thread_id": run_id}}
    app = build_graph()

    console.print("[dim]阶段 1/5：分析创业方向...[/dim]")
    result = app.invoke({"user_input": USER_INPUT, "run_id": run_id}, config=config)

    checkpoint_count = 0
    while True:
        state = app.get_state(config)
        if not state.next:
            break

        interrupted = False
        for task in state.tasks:
            if task.interrupts:
                checkpoint_count += 1
                for intr in task.interrupts:
                    msg = str(intr.value)

                    if checkpoint_count == 1:
                        console.print(Panel(
                            msg,
                            title="[bold yellow]确认点 1：候选产品列表[/bold yellow]",
                            border_style="yellow",
                        ))
                        console.print("[dim]自动接受全部候选产品，继续深度研究...[/dim]\n")
                        result = app.invoke(Command(resume=""), config=config)
                    else:
                        console.print(Panel(
                            msg,
                            title="[bold yellow]确认点 2：评分结果[/bold yellow]",
                            border_style="yellow",
                        ))
                        console.print("[dim]使用默认权重，生成最终报告...[/dim]\n")
                        result = app.invoke(Command(resume=""), config=config)

                    interrupted = True
                    break
            if interrupted:
                break

        if not interrupted:
            break

    final_state = app.get_state(config)
    report_md = final_state.values.get("final_report_markdown", "")
    report_path = final_state.values.get("final_report_path", "")

    if report_md:
        console.print("\n" + "=" * 60)
        console.print(Markdown(report_md))
        console.print(f"\n[bold green]✓ 报告已保存：{report_path}[/bold green]")
    else:
        console.print("[red]报告生成失败，请检查日志[/red]")


if __name__ == "__main__":
    main()
