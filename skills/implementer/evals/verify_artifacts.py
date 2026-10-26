#!/usr/bin/env python3
"""校验 implementer 执行后是否在约定位置生成任务报告。

用法：
    python evals/verify_artifacts.py <开发序号目录>

示例：
    python evals/verify_artifacts.py docs/dev-docs/001

开发序号目录即 docs/dev-docs/<开发序号>。约定产物为
`task-report/<编号>-<任务标题>.md`，须与 `task-list/` 下的每个任务文件一一对应，
且内容非空。

退出码：全部通过为 0；有缺失或内容为空为 1；参数错误为 2。
"""

from __future__ import annotations

import sys
from pathlib import Path

_ORDER_NAME = "执行顺序.md"


def _is_non_empty(path: Path) -> bool:
    try:
        return bool(path.read_text(encoding="utf-8", errors="replace").strip())
    except OSError:
        return False


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("用法：python evals/verify_artifacts.py <开发序号目录>", file=sys.stderr)
        return 2

    root = Path(argv[1])
    if not root.is_dir():
        print(f"开发序号目录不存在：{root}", file=sys.stderr)
        return 2

    print(f"[产物校验] implementer —— {root}")
    failures = 0

    task_dir = root / "task-list"
    if not task_dir.is_dir():
        print(f"  ✗ 缺少任务目录，无法确定应产出的任务报告：{task_dir}")
        failures += 1
        task_files: list[Path] = []
    else:
        task_files = sorted(
            path
            for path in task_dir.iterdir()
            if path.is_file() and path.suffix == ".md" and path.name != _ORDER_NAME
        )
        if not task_files:
            print(f"  ✗ 任务目录下没有任务文件：{task_dir}")
            failures += 1

    report_dir = root / "task-report"
    if not report_dir.is_dir():
        print(f"  ✗ 缺少任务报告目录：{report_dir}")
        failures += 1

    for task_file in task_files:
        report = report_dir / task_file.name
        if not report.is_file():
            print(f"  ✗ 缺少任务报告：{report}")
            failures += 1
        elif not _is_non_empty(report):
            print(f"  ✗ 任务报告内容为空：{report}")
            failures += 1
        else:
            print(f"  ✓ 任务报告：{report}")

    print()
    if failures:
        print(f"结果：失败（{failures} 项）")
        return 1
    print("结果：通过")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
