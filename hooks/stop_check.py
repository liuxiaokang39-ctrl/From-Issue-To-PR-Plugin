#!/usr/bin/env python3
"""Stop hook：阶段收尾时检查最近一个开发序号目录的产物是否齐全。

只做提醒，不阻断结束：缺产物时把清单回给模型，让其补齐后再收尾。
"""

from __future__ import annotations

import sys
from pathlib import Path

import _hooklib as lib

_CHECKS: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    ("阶段 1 需求确认", (lib.ISSUE_FILE_SUFFIX,), ()),
    ("阶段 2 开发文档", ("开发文档.md", "流程图.md"), ("migration-info",)),
    ("阶段 3 任务拆分", (), ("task-list",)),
    ("阶段 4 编码实现", (), ("task-report",)),
    ("阶段 5 测试流程与资源", (), ("test-process",)),
    ("阶段 6 执行测试", (), ("test-report",)),
    ("阶段 8 提交 PR", (lib.PR_FILE_SUFFIX,), ()),
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
    project_dir = Path(lib.read_event().get("cwd") or Path.cwd())
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

    if not missing:
        return 0

    lib.emit_context(
        "Stop",
        "【产物收尾提醒】开发序号 "
        f"{index_dir.name} 下仍有未落盘或缺失的产物：\n- "
        + "\n- ".join(missing)
        + "\n若本次只做部分阶段，可忽略与当前阶段无关的条目。",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
