#!/usr/bin/env python3
"""SessionStart hook：向会话注入本插件的工作流定位信息。"""

from __future__ import annotations

import sys
from pathlib import Path

import _hooklib as lib

_STAGES = (
    "issue-writer（需求确认）→ dev-doc-writer（开发文档）→ task-planner（任务拆分）"
    "→ implementer（编码实现）→ test-planner（测试流程与资源）→ test-runner（执行测试）"
    "→ project-doc-sync（项目文档同步）→ pr-creator（提交 PR）"
)


def _recent_indexes(project_dir: Path, limit: int = 3) -> list[str]:
    root = project_dir / lib.DEV_DOCS_REL
    if not root.is_dir():
        return []
    dirs = sorted((path for path in root.iterdir() if path.is_dir()), key=lambda p: p.name)
    return [path.name for path in dirs[-limit:]]


def main() -> int:
    project_dir = Path.cwd()
    lines = [
        "【from-issue-to-pr 插件】当前工作流共 8 个阶段：",
        _STAGES,
        "产物统一落在 docs/dev-docs/<开发序号>/，项目文档按既有位置就地更新。",
        "单阶段调用对应 Skill（如 issue-writer）；Claude Code 可用 /from-issue-to-pr:issue 等命令，Codex 用 $issue-writer 等技能名。",
        "全流程按上述顺序串联；Claude Code 可用 /from-issue-to-pr:workflow 一次推进。",
    ]
    recent = _recent_indexes(project_dir)
    if recent:
        lines.append(f"已有开发序号目录：{', '.join(recent)}（沿用同一序号继续推进）。")
    lib.emit_context("SessionStart", "\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
