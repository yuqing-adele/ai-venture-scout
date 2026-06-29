#!/usr/bin/env python3
"""AI Venture Scout — 主入口"""
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
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)

console = Console()


def main():
    from workflow.graph import build_graph

    console.print(Panel.fit(
        "[bold cyan]AI Venture Scout[/bold cyan]\n"
        "深圳科技创业方向智能分析系统",
        border_style="cyan",
    ))

    user_input = console.input("\n[bold]请描述你的创业背景[/bold]（团队、预算、方向偏好）：\n> ")
    if not user_input.strip():
        console.print("[red]输入不能为空[/red]")
        return

    run_id = uuid.uuid4().hex[:8]
    config = {"configurable": {"thread_id": run_id}}

    app = build_graph()

    initial_state = {
        "user_input": user_input,
        "run_id": run_id,
    }

    console.print(f"\n[dim]Run ID: {run_id}[/dim]\n")

    # 运行直到完成或中断
    result = app.invoke(initial_state, config=config)

    while True:
        state = app.get_state(config)

        # 检查是否还有待执行的节点
        if not state.next:
            break

        # 检查中断
        interrupted = False
        for task in state.tasks:
            if task.interrupts:
                for intr in task.interrupts:
                    console.print(Panel(
                        str(intr.value),
                        title="[bold yellow]等待你的确认[/bold yellow]",
                        border_style="yellow",
                    ))
                    user_response = console.input("[bold]你的选择[/bold]（直接回车=确认）：\n> ")
                    result = app.invoke(Command(resume=user_response), config=config)
                    interrupted = True
                    break
            if interrupted:
                break

        if not interrupted:
            break

    # 显示最终报告
    final_state = app.get_state(config)
    report_md = final_state.values.get("final_report_markdown", "")
    report_path = final_state.values.get("final_report_path", "")

    if report_md:
        console.print("\n")
        console.print(Markdown(report_md))
        console.print(f"\n[green]✓ 报告已保存至：{report_path}[/green]")
    else:
        console.print("[red]报告生成失败，请检查日志[/red]")


if __name__ == "__main__":
    main()
