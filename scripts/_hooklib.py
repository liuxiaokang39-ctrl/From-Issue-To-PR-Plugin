"""hooks 共用工具：读取事件 JSON、定位插件根与开发序号目录。

本文件不被 hooks.json 直接调用，仅供同目录下的 hook 脚本 import。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

DEV_DOCS_REL = Path("docs") / "dev-docs"
ISSUE_FILE_SUFFIX = "-issue.md"
PR_FILE_SUFFIX = "-PR.md"


def read_event() -> dict:
    """读取 stdin 上的 hook 事件 JSON；无内容或格式错误时返回空字典。"""
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        event = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return event if isinstance(event, dict) else {}


def plugin_root() -> Path:
    """插件根目录：优先取宿主注入的插件根变量，否则用本文件的上两级目录。"""
    for name in ("PLUGIN_ROOT", "CLAUDE_PLUGIN_ROOT"):
        env = os.environ.get(name)
        if env:
            return Path(env)
    return Path(__file__).resolve().parent.parent


def emit(hook_event_name: str, payload: dict) -> None:
    """输出 hookSpecificOutput 结构。"""
    body = {"hookSpecificOutput": {"hookEventName": hook_event_name}}
    body["hookSpecificOutput"].update(payload)
    json.dump(body, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


def emit_context(hook_event_name: str, text: str) -> None:
    emit(hook_event_name, {"additionalContext": text})


def dev_index_from_path(file_path: str) -> tuple[Path, str] | None:
    """从文件路径反推 (开发序号目录绝对路径, 开发序号)；不在 docs/dev-docs 下时返回 None。"""
    if not file_path:
        return None
    path = Path(file_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    path = path.resolve()
    parts = path.parts
    for index in range(len(parts) - 2):
        if parts[index] == "docs" and parts[index + 1] == "dev-docs":
            if index + 2 >= len(parts):
                return None
            seq = parts[index + 2]
            return (Path(*parts[: index + 3]), seq)
    return None
