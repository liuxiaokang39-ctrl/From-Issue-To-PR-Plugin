#!/usr/bin/env python3
"""PostToolUse hook：写入 docs/dev-docs 产物后，自动运行对应 Skill 的 evals 校验。

兼容 Claude Code 的 Write/Edit/MultiEdit（tool_input.file_path）与 Codex 的
apply_patch（tool_input.command 中的补丁信封）。校验结果以 additionalContext
回给模型；本 hook 不阻断工具调用。
project-doc-sync 的校验需要 rustdoc JSON 参数，无法在此自动推断，故不自动触发。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import _hooklib as lib

_MAX_REPORT_CHARS = 2000
_PATCH_FILE_PREFIXES = ("*** Add File: ", "*** Update File: ", "*** Delete File: ")
_PATCH_MOVE_PREFIX = "*** Move to: "


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


def _paths_from_event(event: dict) -> list[str]:
    """取出本次写入的目标文件：Claude 用 file_path，Codex 用补丁信封。"""
    tool_input = event.get("tool_input") or {}
    file_path = str(tool_input.get("file_path") or "")
    if file_path:
        return [file_path]

    patch = str(tool_input.get("command") or "")
    if not patch:
        return []

    paths: list[str] = []
    moved: dict[str, str] = {}
    current: str | None = None
    for raw in patch.splitlines():
        line = raw.strip()
        for prefix in _PATCH_FILE_PREFIXES:
            if line.startswith(prefix):
                current = line[len(prefix) :].strip()
                if current:
                    paths.append(current)
                break
        else:
            if line.startswith(_PATCH_MOVE_PREFIX) and current:
                target = line[len(_PATCH_MOVE_PREFIX) :].strip()
                if target:
                    moved[current] = target

    return [moved.get(path, path) for path in paths]


def _locate(file_path: str, project_dir: Path) -> tuple[Path, str, str] | None:
    """把写入路径落到某个开发序号目录，并判断应跑哪个 Skill 的校验。"""
    path = Path(file_path)
    if not path.is_absolute():
        path = project_dir / path

    located = lib.dev_index_from_path(str(path))
    if not located:
        return None

    index_dir, seq = located
    try:
        relative = path.resolve().relative_to(index_dir)
    except ValueError:
        return None

    skill = _skill_for(relative)
    if not skill:
        return None
    return index_dir, seq, skill


def _verify(index_dir: Path, seq: str, skill: str, project_dir: Path) -> str:
    """运行指定 Skill 的产物校验，返回给模型的反馈文本。"""
    script = lib.plugin_root() / "skills" / skill / "evals" / "verify_artifacts.py"
    if not script.is_file():
        return ""

    try:
        completed = subprocess.run(
            [sys.executable, str(script), str(index_dir)],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return f"[产物校验] {skill} 校验未能执行：{exc}"

    output = (completed.stdout + completed.stderr).strip()
    if len(output) > _MAX_REPORT_CHARS:
        output = output[:_MAX_REPORT_CHARS] + "\n…（输出过长已截断）"

    status = "通过" if completed.returncode == 0 else "未通过"
    return f"[产物校验] 开发序号 {seq} / {skill} —— {status}\n{output}"


def main() -> int:
    event = lib.read_event()
    project_dir = Path(event.get("cwd") or Path.cwd())
    reports: list[str] = []
    seen: set[tuple[str, str]] = set()

    for file_path in _paths_from_event(event):
        located = _locate(file_path, project_dir)
        if not located:
            continue

        index_dir, seq, skill = located
        key = (str(index_dir), skill)
        if key in seen:
            continue
        seen.add(key)

        report = _verify(index_dir, seq, skill, project_dir)
        if report:
            reports.append(report)

    if reports:
        lib.emit_context("PostToolUse", "\n\n".join(reports))
    return 0


if __name__ == "__main__":
    sys.exit(main())
