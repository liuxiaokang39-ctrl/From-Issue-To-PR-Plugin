#!/usr/bin/env python3
"""校验 test-planner 执行后是否在约定位置生成三份测试流程文档。

用法：
    python evals/verify_artifacts.py <开发序号目录>

示例：
    python evals/verify_artifacts.py docs/dev-docs/001

开发序号目录即 docs/dev-docs/<开发序号>。约定产物为 `test-process/` 下的
`1-单元白盒测试流程.md`、`2-集成白盒测试流程.md`、`3-真实部署黑盒测试流程.md`，
须同时存在且内容非空。

退出码：全部通过为 0；有缺失或内容为空为 1；参数错误为 2。
"""

from __future__ import annotations

import sys
from pathlib import Path

_FILENAMES = (
    "1-单元白盒测试流程.md",
    "2-集成白盒测试流程.md",
    "3-真实部署黑盒测试流程.md",
)


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

    print(f"[产物校验] test-planner —— {root}")
    failures = 0

    process_dir = root / "test-process"
    if not process_dir.is_dir():
        print(f"  ✗ 缺少测试流程目录：{process_dir}")
        failures += 1

    for filename in _FILENAMES:
        path = process_dir / filename
        if not path.is_file():
            print(f"  ✗ 缺少测试流程文档：{path}")
            failures += 1
        elif not _is_non_empty(path):
            print(f"  ✗ 测试流程文档内容为空：{path}")
            failures += 1
        else:
            print(f"  ✓ 测试流程文档：{path}")

    print()
    if failures:
        print(f"结果：失败（{failures} 项）")
        return 1
    print("结果：通过")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
