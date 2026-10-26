#!/usr/bin/env python3
"""PostToolUse hook：写入 docs/dev-docs 产物后，自动运行对应 Skill 的 evals 校验。

校验结果以 additionalContext 回给模型；本 hook 不阻断工具调用。
project-doc-sync 的校验需要 rustdoc JSON 参数，无法在此自动推断，故不自动触发。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import _hooklib as lib

_MAX_REPORT_CHARS = 2000


def _skill_for(relative: Path) -> str | None:
    """按产物相对开发序号目录的路径判断负责该产物的 Skill。"""
    name = relative.name
    parts = relative.parts

    if name.endswith(lib.ISSUE_FILE_SUFFIX):
        return "issue-writer"
    if name.endswith(lib.PR_FILE_SUFFIX):
        return "pr-creator"
    if "task-list" in parts:
        return "task-planner"
    if "task-report" in parts:
        return "implementer"
    if "test-process" in parts:
        return "test-planner"
    if "test-report" in parts:
        return "test-runner"
    if "migration-info" in parts:
        return "dev-doc-writer"
    if name.endswith(("开发文档.md", "流程图.md", "公有接口契约.md")):
        return "dev-doc-writer"
    return None


def main() -> int:
    event = lib.read_event()
    tool_input = event.get("tool_input") or {}
    file_path = str(tool_input.get("file_path") or "")
    located = lib.dev_index_from_path(file_path)
    if not located:
        return 0

    index_dir, seq = located
    relative = Path(file_path).resolve().relative_to(index_dir)
    skill = _skill_for(relative)
    if not skill:
        return 0

    script = lib.plugin_root() / "skills" / skill / "evals" / "verify_artifacts.py"
    if not script.is_file():
        return 0

    project_dir = Path(event.get("cwd") or Path.cwd())
    try:
        completed = subprocess.run(
            [sys.executable, str(script), str(index_dir)],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        lib.emit_context("PostToolUse", f"[产物校验] {skill} 校验未能执行：{exc}")
        return 0

    output = (completed.stdout + completed.stderr).strip()
    if len(output) > _MAX_REPORT_CHARS:
        output = output[:_MAX_REPORT_CHARS] + "\n…（输出过长已截断）"

    status = "通过" if completed.returncode == 0 else "未通过"
    lib.emit_context(
        "PostToolUse",
        f"[产物校验] 开发序号 {seq} / {skill} —— {status}\n{output}",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
