"""
分段引导运行：每次只跑到下一个确认点就退出，状态持久化在 SQLite。
用法：
  python run_guided.py start <run_id> <input_file>   # 从文件读取 user_input（必须UTF-8），运行到第一个确认点
  python run_guided.py resume <run_id> "<回复>"        # 用持久化状态恢复，运行到下一个确认点或完成
  python run_guided.py status <run_id>                # 查看当前状态，不执行任何节点

注意：start 命令必须传文件路径，不要用 PowerShell 管道（Get-Content | python ...）传中文文本——
Windows PowerShell 管道会用错误的编码转换 Unicode 字符，导致中文内容损坏。
"""
from __future__ import annotations
import sys
import logging
from dotenv import load_dotenv
from langgraph.types import Command

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)


def get_app_and_config(run_id: str):
    from workflow.graph import build_graph
    app = build_graph()
    config = {"configurable": {"thread_id": run_id}}
    return app, config


def report_state(app, config):
    """打印当前状态：是否有待确认的中断，或是否已完成"""
    state = app.get_state(config)

    if not state.next:
        report_md = state.values.get("final_report_markdown", "")
        report_path = state.values.get("final_report_path", "")
        if report_md:
            print("===STATUS:DONE===")
            print(f"===REPORT_PATH:{report_path}===")
        else:
            print("===STATUS:ERROR===")
            print("流程已结束但没有生成报告，请检查日志")
        return

    for task in state.tasks:
        if task.interrupts:
            for intr in task.interrupts:
                print("===STATUS:WAITING===")
                print("===INTERRUPT_MESSAGE_START===")
                print(str(intr.value))
                print("===INTERRUPT_MESSAGE_END===")
                return

    print("===STATUS:RUNNING_NO_INTERRUPT===")


def cmd_start(run_id: str, input_file: str | None = None):
    if input_file:
        with open(input_file, "r", encoding="utf-8") as f:
            user_input = f.read()
    else:
        user_input = sys.stdin.read()
    if not user_input.strip():
        print("===STATUS:ERROR===")
        print("user_input 为空")
        sys.exit(1)

    app, config = get_app_and_config(run_id)
    try:
        app.invoke({"user_input": user_input, "run_id": run_id}, config=config)
    except Exception as e:
        logging.exception("启动失败")
        print("===STATUS:ERROR===")
        print(f"{type(e).__name__}: {e}")
        sys.exit(1)

    report_state(app, config)


def cmd_resume(run_id: str, resume_value: str):
    app, config = get_app_and_config(run_id)
    try:
        app.invoke(Command(resume=resume_value), config=config)
    except Exception as e:
        logging.exception("恢复执行失败")
        print("===STATUS:ERROR===")
        print(f"{type(e).__name__}: {e}")
        sys.exit(1)

    report_state(app, config)


def cmd_status(run_id: str):
    app, config = get_app_and_config(run_id)
    report_state(app, config)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python run_guided.py [start|resume|status] <run_id> [resume_value]")
        sys.exit(1)

    cmd, run_id = sys.argv[1], sys.argv[2]

    if cmd == "start":
        input_file = sys.argv[3] if len(sys.argv) > 3 else None
        cmd_start(run_id, input_file)
    elif cmd == "resume":
        resume_value = sys.argv[3] if len(sys.argv) > 3 else ""
        cmd_resume(run_id, resume_value)
    elif cmd == "status":
        cmd_status(run_id)
    else:
        print(f"未知命令: {cmd}")
        sys.exit(1)
