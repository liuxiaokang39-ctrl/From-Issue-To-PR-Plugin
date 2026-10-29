#!/usr/bin/env python3
"""Stop hook：阶段收尾时检查最近一个开发序号目录与项目级规范产物的齐全程度。

缺产物时返回一次继续执行的决定，把清单回给模型，让其补齐后再收尾；
`stop_hook_active` 为真时不再重复触发，避免无限循环。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import _hooklib as lib

_CHECKS: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    ("管理入口：开发上下文", ("dev-context.md",), ()),
    ("A 需求确认", (lib.ISSUE_FILE_SUFFIX,), ()),
    ("B/C 开发文档", ("-dev-doc.md", "-flowchart.md", "-interface-contract.md"), ("migration-info",)),
    ("D 任务拆分", (), ("task-list",)),
    ("E 编码实现", (), ("task-report",)),
    ("F 测试流程与资源", (), ("test-process",)),
    ("G 执行测试", (), ("test-report",)),
    ("N 提交 PR", (lib.PR_FILE_SUFFIX,), ()),
)

_PROJECT_CHECKS: tuple[tuple[str, tuple[Path, ...]], ...] = (
    (
        "管理入口：开发规范",
        (
            Path("docs") / "dev-standards" / "rust-coding-standards.md",
            Path("docs") / "dev-standards" / "project-architecture-standards.md",
        ),
    ),
)


def _latest_index_dir(project_dir: Path) -> Path | None:
    root = project_dir / lib.DEV_DOCS_REL
    if not root.is_dir():
        return None
    dirs = sorted((path for path in root.iterdir() if path.is_dir()), key=lambda p: p.name)
    return dirs[-1] if dirs else None


def _has_any(index_dir: Path, suffixes: tuple[str, ...]) -> bool:
    for path in index_dir.rglob("*"):
        if path.is_file() and any(path.name.endswith(suffix) for suffix in suffixes):
            return True
    return False


def main() -> int:
    event = lib.read_event()
    if event.get("stop_hook_active"):
        return 0

    project_dir = Path(event.get("cwd") or Path.cwd())
    index_dir = _latest_index_dir(project_dir)
    if index_dir is None:
        return 0

    missing: list[str] = []
    for stage, suffixes, dirs in _CHECKS:
        absent = [d for d in dirs if not (index_dir / d).is_dir()]
        if suffixes and not _has_any(index_dir, suffixes):
            absent.append("/".join(suffixes))
        if absent:
            missing.append(f"{stage}：缺少 {'、'.join(absent)}")

    for stage, files in _PROJECT_CHECKS:
        absent = [str(path) for path in files if not (project_dir / path).is_file()]
        if absent:
            missing.append(f"{stage}：缺少 {'、'.join(absent)}")

    if not missing:
        return 0

    reason = (
        "【产物收尾提醒】开发序号 "
        f"{index_dir.name} 下仍有未落盘或缺失的产物：\n- "
        + "\n- ".join(missing)
        + "\n请补齐后再收尾；若本次只做部分阶段，请向用户说明并忽略与当前阶段无关的条目。"
    )
    json.dump({"decision": "block", "reason": reason}, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
