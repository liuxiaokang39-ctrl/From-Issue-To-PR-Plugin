#!/usr/bin/env python3
"""校验 spec-manager 执行后是否在约定位置生成产物。

用法：
    python evals/verify_artifacts.py <项目根>             # 启动检查模式
    python evals/verify_artifacts.py <项目根> <开发序号>  # 开发信息分配模式

示例：
    python evals/verify_artifacts.py .
    python evals/verify_artifacts.py . 4

约定产物：
- docs/开发规范/Rust编码规范.md（存在且内容非空）；
- docs/开发规范/项目目录架构规范.md（存在且内容非空）；
- docs/开发规范/迁移信息/（目录存在）；
- 开发信息分配模式下额外校验：
  - docs/dev-docs/<开发序号>/ 及其下的 task-list/、test-process/、
    task-report/、test-report/ 四个子目录；
  - docs/dev-docs/<开发序号>/开发上下文.md，四项登记值齐全且非占位。

worktree 与分支不由本脚本校验，由 Agent 依据 `git worktree list` 与 `git branch` 复核。

退出码：全部通过为 0；有缺失或内容为空为 1；参数错误为 2。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_SPEC_DOCS = (
    Path("docs") / "开发规范" / "Rust编码规范.md",
    Path("docs") / "开发规范" / "项目目录架构规范.md",
)
_MIGRATION_DIR = Path("docs") / "开发规范" / "迁移信息"
_DEV_DOCS_DIR = Path("docs") / "dev-docs"
_CONTEXT_FILE = "开发上下文.md"
_SKELETON_DIRS = ("task-list", "test-process", "task-report", "test-report")
_CONTEXT_FIELDS = ("开发序号", "分支名", "worktree 路径", "开发目录")
_CONTEXT_RE = re.compile(r"^\s*[-*]\s*(开发序号|分支名|worktree 路径|开发目录)\s*[:：]\s*(.+?)\s*$")


def _is_non_empty(path: Path) -> bool:
    try:
        return bool(path.read_text(encoding="utf-8", errors="replace").strip())
    except OSError:
        return False


def _context_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return values
    for line in text.splitlines():
        match = _CONTEXT_RE.match(line)
        if match:
            values[match.group(1)] = match.group(2).strip()
    return values


def main(argv: list[str]) -> int:
    if len(argv) not in (2, 3):
        print("用法：python evals/verify_artifacts.py <项目根> [开发序号]", file=sys.stderr)
        return 2

    project_root = Path(argv[1])
    if not project_root.is_dir():
        print(f"项目根不存在：{project_root}", file=sys.stderr)
        return 2

    seq = argv[2].strip() if len(argv) == 3 else ""
    if len(argv) == 3 and not seq:
        print("开发序号不能为空", file=sys.stderr)
        return 2

    mode = "开发信息分配" if seq else "启动检查"
    print(f"[产物校验] spec-manager —— {project_root} / 模式 {mode} / 开发序号 {seq or '未分配'}")
    failures = 0

    for relative in _SPEC_DOCS:
        path = project_root / relative
        if not path.is_file():
            print(f"  ✗ 缺少规范文档：{relative}")
            failures += 1
        elif not _is_non_empty(path):
            print(f"  ✗ 规范文档内容为空：{relative}")
            failures += 1
        else:
            print(f"  ✓ 规范文档：{relative}")

    migration_dir = project_root / _MIGRATION_DIR
    if migration_dir.is_dir():
        print(f"  ✓ 迁移信息目录：{_MIGRATION_DIR}")
    else:
        print(f"  ✗ 缺少迁移信息目录：{_MIGRATION_DIR}")
        failures += 1

    if seq:
        index_dir = project_root / _DEV_DOCS_DIR / seq
        if not index_dir.is_dir():
            print(f"  ✗ 缺少开发序号目录：{_DEV_DOCS_DIR / seq}")
            failures += 1
        else:
            print(f"  ✓ 开发序号目录：{_DEV_DOCS_DIR / seq}")
            for name in _SKELETON_DIRS:
                if (index_dir / name).is_dir():
                    print(f"  ✓ 目录骨架：{(_DEV_DOCS_DIR / seq / name)}")
                else:
                    print(f"  ✗ 缺少目录骨架：{(_DEV_DOCS_DIR / seq / name)}")
                    failures += 1

            context_path = index_dir / _CONTEXT_FILE
            values = _context_values(context_path)
            if not context_path.is_file():
                print(f"  ✗ 缺少开发上下文登记文件：{(_DEV_DOCS_DIR / seq / _CONTEXT_FILE)}")
                failures += 1
            else:
                for field in _CONTEXT_FIELDS:
                    value = values.get(field, "")
                    if not value or value.startswith("<"):
                        print(f"  ✗ 登记文件缺少有效值：{field}")
                        failures += 1
                    else:
                        print(f"  ✓ 登记值：{field} = {value}")

    print()
    if failures:
        print(f"结果：失败（{failures} 项）")
        return 1
    print("结果：通过")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
